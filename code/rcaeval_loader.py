"""
RCAEval loader -- telemetry to stake, against the REAL schema.

SCHEMA FACTS verified against the data on 2026-09-21. All three systems differ;
a loader written to one silently misreads the others.

    system            rows  cols  throughput col   latency cols      error cols
    Online Boutique   4201    49  <svc>_load       <svc>_latency     3 of 12
    Sock Shop          721    59  <svc>_workload   <svc>_latency-50  5 of 15
                                                   <svc>_latency-90
    Train Ticket       961   220  <svc>_workload   <svc>_latency-50  5 of 64
                                                   <svc>_latency-90

Sample interval is 1 s in all three.

THREE SUBSTITUTIONS FORCED BY THE DATA. Each must appear in Section 5.2 of the
paper; a silent substitution is a construct-validity failure.

  1. NO REPLICA COUNTS anywhere in the corpus. The OpenCost replica-seconds
     formula cannot be applied directly. We proxy infrastructure cost from CPU
     and memory consumption priced at published per-core and per-GB rates,
     which is the same quantity OpenCost bills for, one level down.

  2. ERROR COLUMNS ARE SPARSE -- 3/12, 5/15 and 5/64 services respectively.
     Per-service error ratio is unavailable, so the availability component of
     the SLO is computed only where error columns exist, and the latency
     objective carries the rest. Latency IS available per service, which is
     what makes this workable.

  3. NO TRACES IN RE1 (0%, verified). Blast radius uses the published static
     topology. See topology.py.
"""

from __future__ import annotations

import pathlib
import re

import numpy as np
import pandas as pd

from stakes import StakeParams
from topology import blast_radius, SUPPORTED

DATA = pathlib.Path(__file__).resolve().parent.parent / "data"

# Column grammar is DETECTED PER FILE, not keyed on system.
#
# BUG FOUND 2026-09-21, after first results were reported. The schema varies by
# FAULT TYPE within a single system, not merely between systems:
#
#   re1ob_adservice_cpu_1    4201 rows  _load     _latency
#   re1ob_adservice_delay_1   721 rows  _workload _latency-50 / _latency-90
#   re1ob_adservice_disk_1    721 rows  _workload _latency-50 / _latency-90
#   re1ob_adservice_loss_1    721 rows  _workload _latency-50 / _latency-90
#   re1ob_adservice_mem_1    4201 rows  _load     _latency
#
# A system-keyed lookup returned no throughput columns for ob delay/disk/loss,
# so req_rate was 0, the error ratio was 0, and burn was 0 on every one of
# those cases -- which is precisely the "median burn is zero on half the cases"
# artefact seen in the first run. It was a parsing failure, not a property of
# the data.
#
# Preference order within each family: richer signal first.
THROUGHPUT_SUFFIXES = ("_workload", "_load")
LATENCY_SUFFIXES = ("_latency-90", "_latency-50", "_latency")


def detect_schema(cols: list[str]) -> dict:
    """Pick the throughput and latency families actually present in THIS file."""
    thr = next((s for s in THROUGHPUT_SUFFIXES
                if any(c.endswith(s) for c in cols)), None)
    lat = next((s for s in LATENCY_SUFFIXES
                if any(c.endswith(s) for c in cols)), None)
    if thr is None:
        raise ValueError(f"no throughput column family found in {len(cols)} cols")
    return {"throughput": thr, "latency": lat}

# Published on-demand rates. Swept in Section 5.5; these are anchors.
USD_PER_CORE_SECOND = 0.0000094    # ~0.034 USD/core-hr
USD_PER_GB_SECOND = 0.0000013      # ~0.0045 USD/GB-hr


def _services(cols: list[str], suffix: str) -> dict[str, str]:
    """Map service name -> column, for columns ending in `suffix`."""
    return {c[: -len(suffix)]: c for c in cols if c.endswith(suffix)}


def load_case(case_dir: pathlib.Path, system: str, sp: StakeParams) -> dict:
    """Compute the stake terms for one incident.

    Returns raw components; composition into rho happens in build_dataset so
    the exchange rates can be swept without re-reading 375 parquet files.
    """
    m = pd.read_parquet(case_dir / "metrics.parquet")
    inject = int((case_dir / "inject_time.txt").read_text().strip())

    cols = [c for c in m.columns if c != "time"]
    g = detect_schema(cols)

    faulty = m[m["time"] >= inject]
    if len(faulty) < 2:
        raise ValueError(f"{case_dir.name}: fewer than 2 faulty samples")
    dt = float(np.median(np.diff(m["time"].to_numpy()))) or 1.0
    T_faulty = float(len(faulty) * dt)

    # --- 1. infrastructure rate, proxied from CPU + memory (substitution 1) --
    cpu = _services(cols, "_cpu")
    mem = _services(cols, "_mem")
    cpu_tot = float(faulty[list(cpu.values())].mean().sum()) if cpu else 0.0
    mem_tot = float(faulty[list(mem.values())].mean().sum()) if mem else 0.0
    # memory columns are bytes in this corpus; convert to GB
    rho_infra = cpu_tot * USD_PER_CORE_SECOND + (mem_tot / 1e9) * USD_PER_GB_SECOND

    # --- 2. throughput and latency-objective violations ---------------------
    thr = _services(cols, g["throughput"])
    lat = _services(cols, g["latency"]) if g["latency"] else {}

    req_rate = float(faulty[list(thr.values())].mean().sum()) if thr else 0.0
    if req_rate <= 0:
        # Must never happen after the per-file schema fix. If it does, the
        # grammar has changed again -- fail loudly rather than emit burn = 0.
        raise ValueError(
            f"{case_dir.name}: zero throughput from {len(thr)} columns "
            f"via '{g['throughput']}' -- schema grammar may have changed"
        )

    # Latency units differ across the corpus (s vs ms). Normalise by detecting
    # scale: values below 10 are seconds.
    viol_rate = 0.0
    for svc, lcol in lat.items():
        tcol = thr.get(svc)
        if tcol is None:
            continue
        l = faulty[lcol].to_numpy(dtype=float)
        if np.nanmedian(l[np.isfinite(l)] if np.isfinite(l).any() else [0]) < 10:
            l = l * 1000.0                          # seconds -> ms
        bad = np.nan_to_num(l) > sp.slo_latency_ms
        viol_rate += float(np.nanmean(np.nan_to_num(faulty[tcol].to_numpy()) * bad))

    # --- 3. availability, where error columns exist (substitution 2) --------
    err = _services(cols, "_error")
    err_rate = float(faulty[list(err.values())].mean().sum()) if err else 0.0

    failed = err_rate + viol_rate
    ratio = failed / req_rate if req_rate > 0 else 0.0
    burn = ratio / (1.0 - sp.slo_availability)

    return {
        "rho_infra": rho_infra,
        "r_fail": failed,
        "burn": burn,
        "req_rate": req_rate,
        "T_faulty": T_faulty,
        "n_services_err": len(err),
        "n_services_lat": len(lat),
    }


def build_dataset(suite: str = "RE1", systems: tuple = SUPPORTED,
                  sp: StakeParams | None = None, verbose: bool = True):
    """Load a suite and return (rho, D, T_e, detail DataFrame)."""
    sp = sp or StakeParams()
    idx = pd.read_parquet(DATA / "cases.parquet")
    idx = idx[(idx.suite == suite) & (idx.system.isin(systems))]

    rows, skipped = [], []
    for _, c in idx.iterrows():
        d = DATA / "cases" / c["case"]
        if not (d / "metrics.parquet").exists():
            skipped.append((c["case"], "not downloaded"))
            continue
        try:
            r = load_case(d, c["system"], sp)
        except Exception as e:                       # noqa: BLE001
            skipped.append((c["case"], f"{type(e).__name__}: {e}"))
            continue
        r.update(case=c["case"], system=c["system"],
                 root_cause=c["root_cause_service"], fault=c["fault"])
        try:
            r["blast"] = blast_radius(c["system"], c["root_cause_service"])
            r["blast_known"] = True
        except Exception:                            # noqa: BLE001
            r["blast"], r["blast_known"] = 0, False
        rows.append(r)

    df = pd.DataFrame(rows)
    if df.empty:
        raise RuntimeError(f"no cases loaded. skipped={skipped[:5]}")

    unknown = (~df["blast_known"]).sum()
    if unknown and verbose:
        print(f"  WARNING: {unknown} cases have a root cause absent from the "
              f"declared topology -- blast radius defaulted to 0.")
        print("   ", sorted(df.loc[~df.blast_known, 'root_cause'].unique())[:8])

    rho = (df["rho_infra"].to_numpy()
           + sp.lambda_exp * df["r_fail"].to_numpy()
           + sp.lambda_slo * df["burn"].to_numpy())
    D = sp.kappa * df["blast"].to_numpy() * float(np.mean(rho))
    T_e = df["T_faulty"].to_numpy()

    if verbose:
        print(f"  loaded {len(df)} cases from {suite} {list(systems)}"
              f"  (skipped {len(skipped)})")
        if skipped:
            print(f"    first skips: {skipped[:3]}")
    return rho, D, T_e, df


if __name__ == "__main__":
    import sys
    systems = tuple(sys.argv[1:]) or SUPPORTED
    print(f"Loading RE1 for systems {systems} ...")
    rho, D, T_e, df = build_dataset("RE1", systems)
    print()
    print(df.groupby("system")[["rho_infra", "r_fail", "burn", "blast",
                                "T_faulty"]].describe().T.to_string())
    print()
    print(f"rho    : [{rho.min():.4e}, {rho.max():.4e}]  "
          f"spread {np.log10(rho.max()/max(rho.min(),1e-12)):.2f} decades")
    print(f"D      : [{D.min():.4e}, {D.max():.4e}]")
    print(f"T_e    : [{T_e.min():.0f}, {T_e.max():.0f}] s")
