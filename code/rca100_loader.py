"""
RCA100 loader -- the second, independent population.

RCA100 is long-format (one row per entity/metric/timestamp), where RCAEval is
wide (one column per service/metric). Nothing is shared between the two
loaders except the stake equations they both feed, which is the point: if the
RCAEval result were an artefact of its wide-format parsing, it would not
survive here.

WHAT THIS DATASET FIXES. All three substitutions RCAEval forced are
unnecessary here, so each becomes testable rather than merely declared:

  RCAEval substitution              RCA100 replacement
  --------------------------------  -----------------------------------------
  1  no replica counts ->           deployment_ready_replicas is measured, so
     CPU+memory proxy               the OpenCost replica-seconds formula runs
                                    as specified
  2  errors on 3-5 services ->      error_count / error_rate are per-entity
     latency violations carry it    across the whole estate
  3  no traces -> static published  topology.json ships ~277 entities and ~353
     call graph                     edges per case, measured in-window

SCHEMA (verified 2026-09-21 against cases/t001):
  metrics.parquet  time(int64 us), domain, entity_set, entity_id, entity_name,
                   metric, value, metric_set_id, service           92k rows
  task.json        alert_window {start,end} ISO8601, alert_entity, task_id
  topology.json    entities[], edges[{src, src_type, dst, dst_type, relation}]
  answer_key/tNNN.gt.json  root_cause_entities[], root_cause_types[]
"""

from __future__ import annotations

import json
import pathlib

import numpy as np
import pandas as pd

from stakes import StakeParams

DATA = pathlib.Path(__file__).resolve().parent.parent / "data" / "rca100"

# Published on-demand rate, same anchor as the RCAEval loader so the two
# populations are priced identically.
USD_PER_POD_SECOND = 0.192 / 16.0 / 3600.0

M_REPLICAS = "deployment_ready_replicas"
M_REQUESTS = "request_count"
M_ERRORS = "error_count"
M_SLOW = "slow_count"
M_LATENCY = "latency"
M_AVAIL = "deployment_availability_rate"


def _sum_metric(df: pd.DataFrame, name: str) -> float:
    """Mean over time of the estate-wide total for one metric."""
    d = df[df["metric"] == name]
    if d.empty:
        return 0.0
    per_t = d.groupby("time")["value"].sum()
    return float(per_t.mean()) if len(per_t) else 0.0


def blast_radius(topo: dict, root_names: list[str]) -> int:
    """Entities transitively reachable from the root-cause entities.

    Uses the measured in-window graph. Matching is by entity name and by the
    `service` prop, since ground truth names services ("payment") while the
    graph carries typed entities ("payment" deployment, pod, operation...).
    """
    ents = topo.get("entities", [])
    edges = topo.get("edges", [])
    by_id = {e["id"]: e for e in ents}

    roots = {e["id"] for e in ents
             if e.get("name") in root_names
             or (e.get("props") or {}).get("service") in root_names}
    if not roots:
        return 0

    adj: dict[str, list[str]] = {}
    for e in edges:
        adj.setdefault(e["src"], []).append(e["dst"])

    seen, stack = set(), list(roots)
    while stack:
        n = stack.pop()
        for m in adj.get(n, []):
            if m not in seen:
                seen.add(m)
                stack.append(m)
    seen -= roots
    # count distinct services reached, not raw entities, so the number is
    # commensurable with RCAEval's service-level blast radius
    svcs = {(by_id.get(i, {}).get("props") or {}).get("service")
            or by_id.get(i, {}).get("name") for i in seen}
    svcs.discard(None)
    return len(svcs)


def load_case(task: str, sp: StakeParams) -> dict:
    d = DATA / "cases" / task
    m = pd.read_parquet(d / "metrics.parquet")
    t = json.loads((d / "task.json").read_text(encoding="utf-8"))

    w = t["alert_window"]
    start = pd.Timestamp(w["start"]).value // 1000      # ns -> us
    end = pd.Timestamp(w["end"]).value // 1000
    win = m[(m["time"] >= start) & (m["time"] <= end)]
    if win.empty:                                        # fall back to all
        win = m
    T_e = max((end - start) / 1e6, 1.0)                  # seconds

    # --- rho_infra: REAL replica-seconds, no proxy ---------------------------
    replicas = _sum_metric(win, M_REPLICAS)
    rho_infra = replicas * USD_PER_POD_SECOND

    # --- failure signal: measured per entity ---------------------------------
    req = _sum_metric(win, M_REQUESTS)
    errs = _sum_metric(win, M_ERRORS)
    slow = _sum_metric(win, M_SLOW)

    # latency-objective violations, for parity with the RCAEval definition
    lat = win[win["metric"] == M_LATENCY]
    viol = 0.0
    if not lat.empty and req > 0:
        v = lat["value"].to_numpy(dtype=float)
        v = v * 1000.0 if np.nanmedian(v) < 10 else v     # s -> ms if needed
        viol = float(np.nanmean(v > sp.slo_latency_ms)) * req

    failed = errs + max(slow, viol)
    ratio = failed / req if req > 0 else 0.0
    burn = ratio / (1.0 - sp.slo_availability)

    gt_path = DATA / "answer_key" / f"{task}.gt.json"
    roots: list[str] = []
    if gt_path.exists():
        roots = json.loads(gt_path.read_text(encoding="utf-8")).get(
            "root_cause_entities", []) or []

    topo_path = d / "topology.json"
    blast = 0
    if topo_path.exists() and roots:
        blast = blast_radius(
            json.loads(topo_path.read_text(encoding="utf-8")), roots)

    return {"task": task, "rho_infra": rho_infra, "r_fail": failed,
            "burn": burn, "req_rate": req, "replicas": replicas,
            "T_faulty": T_e, "blast": blast,
            "root_cause": ",".join(roots), "n_rows": len(win)}


def build_dataset(sp: StakeParams | None = None, verbose: bool = True):
    sp = sp or StakeParams()
    tasks = [t.strip() for t in
             (DATA / "manifest.txt").read_text().split() if t.strip()]
    rows, skipped = [], []
    for t in tasks:
        if not (DATA / "cases" / t / "metrics.parquet").exists():
            skipped.append((t, "not downloaded"))
            continue
        try:
            rows.append(load_case(t, sp))
        except Exception as e:                            # noqa: BLE001
            skipped.append((t, f"{type(e).__name__}: {e}"))

    df = pd.DataFrame(rows)
    if df.empty:
        raise RuntimeError(f"no RCA100 cases loaded; skipped={skipped[:3]}")

    rho = (df["rho_infra"].to_numpy()
           + sp.lambda_exp * df["r_fail"].to_numpy()
           + sp.lambda_slo * df["burn"].to_numpy())
    D = sp.kappa * df["blast"].to_numpy() * float(np.mean(rho))
    T_e = df["T_faulty"].to_numpy()

    if verbose:
        print(f"  RCA100: {len(df)} cases loaded, {len(skipped)} skipped")
        if skipped:
            print(f"    first skips: {skipped[:3]}")
    return rho, D, T_e, df


if __name__ == "__main__":
    rho, D, T_e, df = build_dataset()
    print()
    print(df[["rho_infra", "r_fail", "burn", "replicas", "blast",
              "T_faulty"]].describe().T.to_string())
    print()
    print(f"blast radius   : {df.blast.min()}-{df.blast.max()} "
          f"(median {df.blast.median():.0f})")
    print(f"replicas       : {df.replicas.min():.0f}-{df.replicas.max():.0f}")
    print(f"burn == 0      : {(df.burn == 0).mean():.1%}")
    print(f"rho spread     : "
          f"{np.log10(rho.max()/max(rho.min(),1e-12)):.2f} decades")
