"""
Cloud-OpsBench field verification -- can it serve as a third stake corpus?

DAY-1 CHECK, run before committing to a 3.8 GB download, exactly as was done
for RCAEval and RCA100.

The stake model needs three components:

    rho = rho_infra  +  lambda_exp * r_fail  +  lambda_slo * burn
          replicas       failed requests        error-budget burn rate

Cloud-OpsBench exposes a FIXED ten-tool interface -- GetResources,
DescribeResource, GetAlerts, GetErrorLogs, GetServiceDependencies,
CheckNodeServiceStatus, CheckServiceConnectivity, GetAppYAML,
GetClusterConfiguration, ListCodeFiles -- and no metrics tool. Verified across
admission, performance, infrastructure and scheduling cases: `latency`,
`throughput`, `qps` and `duration_seconds` appear zero times.

So r_fail and burn are unavailable. This script measures what IS available --
replica counts and dependency fan-out -- and answers the question that
actually matters:

    Does the near-constant infrastructure term, which floored the composite on
    both previous corpora, also appear here?

If replicas vary widely, the floor is a property of RCAEval and RCA100 rather
than of benchmarks generally, and the paper's generalisation needs narrowing.
If they do not, this is a third independent confirmation.

    python cloudops_probe.py --sample 40
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import pathlib
import re

import numpy as np
import requests

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "cloudops"
BASE = "https://huggingface.co/datasets/LLM4Ops/Cloud-OpsBench/resolve/main"
H = {"User-Agent": "research-field-verification/1.0"}

# A pod line in `kubectl get pods` output: NAME READY STATUS RESTARTS AGE
# READY is "n/m" -- m is the desired count, n the ready count.
READY = re.compile(r"\b(\d+)/(\d+)\b")


def load_index() -> list[dict]:
    p = DATA / "index.jsonl"
    if not p.exists():
        raise SystemExit(f"missing {p}. Fetch index.jsonl first.")
    return [json.loads(l) for l in p.open(encoding="utf-8") if l.strip()]


def fetch_case(case: dict) -> dict | None:
    local = DATA / "cases" / case["case_key"].replace("/", "_") / "tool_cache.json"
    if local.exists():
        blob = local.read_text(encoding="utf-8")
    else:
        try:
            r = requests.get(f"{BASE}/{case['tool_cache_path']}",
                             timeout=(20, 180), headers=H)
        except Exception:                                      # noqa: BLE001
            return None
        if r.status_code != 200:
            return None
        blob = r.text
        local.parent.mkdir(parents=True, exist_ok=True)
        local.write_text(blob, encoding="utf-8")

    d = json.loads(blob)

    # --- replica counts, from the plain `get pods` listing -----------------
    ready_pairs: list[tuple[int, int]] = []
    deps = 0
    for k, v in d.items():
        if not isinstance(k, str):
            continue
        text = v if isinstance(v, str) else json.dumps(v)
        if k.startswith("GetResources:") and '"resource_type":"pods"' in k \
                and '"name":""' in k and "output_wide" not in k \
                and "show_labels" not in k:
            ready_pairs += [(int(a), int(b)) for a, b in READY.findall(text)]
        if k.startswith("GetServiceDependencies"):
            deps = max(deps, len(re.findall(r'"[a-z][a-z0-9-]{2,}"', text)))

    if not ready_pairs:
        return None
    desired = sum(b for _, b in ready_pairs)
    ready = sum(a for a, _ in ready_pairs)
    return {"case": case["case_key"], "system": case["system"],
            "category": case["category"], "root_cause": case["root_cause"],
            "difficulty": case.get("difficulty", "?"),
            "pods": len(ready_pairs), "desired": desired, "ready": ready,
            "unready": desired - ready, "deps": deps}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=40)
    ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()

    idx = load_index()
    # stratify: equal share from every system/category present
    by_cat: dict[str, list] = {}
    for c in idx:
        by_cat.setdefault(f"{c['system']}/{c['category']}", []).append(c)
    per = max(1, a.sample // len(by_cat))
    picks = [c for v in by_cat.values() for c in v[:per]]
    print(f"index: {len(idx)} cases, {len(by_cat)} system/category groups")
    print(f"sampling {len(picks)} ({per} per group)\n")

    rows = []
    with cf.ThreadPoolExecutor(a.workers) as ex:
        for i, r in enumerate(ex.map(fetch_case, picks), 1):
            if r:
                rows.append(r)
            if i % 10 == 0:
                print(f"  {i}/{len(picks)}", flush=True)

    if not rows:
        raise SystemExit("no cases parsed -- check the tool-cache format")

    desired = np.array([r["desired"] for r in rows], dtype=float)
    unready = np.array([r["unready"] for r in rows], dtype=float)
    deps = np.array([r["deps"] for r in rows], dtype=float)

    print(f"\nparsed {len(rows)} cases\n")
    print("=" * 66)
    print("DOES THE INFRASTRUCTURE TERM VARY HERE?")
    print("=" * 66)

    def line(name, v):
        lo, hi = v.min(), v.max()
        spread = hi / max(lo, 1e-9)
        cv = v.std() / v.mean() if v.mean() else float("nan")
        print(f"  {name:<22}{lo:7.0f} - {hi:<7.0f} spread {spread:6.2f}x   CV {cv:5.2f}")

    line("desired replicas", desired)
    line("UNREADY replicas", unready)
    line("dependency fan-out", deps)

    print()
    print("  reference, same quantity on the other two corpora:")
    print("    RCAEval  rho_infra spread  5.57x")
    print("    RCA100   rho_infra spread  1.07x   <- the floor")
    print()
    spread = desired.max() / max(desired.min(), 1e-9)
    if spread > 3:
        print("  VERDICT: desired replicas DO vary here. The infrastructure floor")
        print("  is not universal across benchmarks, and the paper's")
        print("  generalisation must be narrowed to fixed-size chaos corpora.")
    else:
        print("  VERDICT: desired replicas are near-constant here too -- a third")
        print("  independent confirmation of the floor.")
    print()
    print("  NOTE: r_fail and burn cannot be computed on this corpus at all.")
    print("  There is no metrics tool in the ten-tool interface, so no request")
    print("  rate, latency or error rate exists to measure. Cloud-OpsBench")
    print("  cannot serve as a third STAKE corpus; it is, however, the right")
    print("  corpus for the AGENT study (golden trajectories, 57 fault types).")

    out = DATA / "probe_results.json"
    out.write_text(json.dumps(rows, indent=1), encoding="utf-8")
    print(f"\n  rows -> {out}")


if __name__ == "__main__":
    main()
