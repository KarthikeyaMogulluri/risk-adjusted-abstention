"""
Deterministic telemetry summarisation for the agent study.

The agent cannot be handed 4,200 x 49 raw samples per case. This compresses a
case into a compact, faithful anomaly report: for every service, the shift
between the pre-injection and post-injection windows on each signal, ranked by
magnitude.

DETERMINISTIC ON PURPOSE. No model is involved in this step, so the context an
agent sees is reproducible from the data alone, and any variance in the study
comes from the agent rather than from its input. It also means summaries are
cached once and reused across models, repetitions and pricing experiments.

    python summarise.py --corpus rcaeval --limit 3     # inspect
    python summarise.py --build                        # cache all 352
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re

import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
CACHE = ROOT / "data" / "summaries"
SIGNALS = ("cpu", "mem", "latency", "workload", "error")


def _pct(now: float, before: float) -> float:
    if before == 0:
        return float("inf") if now > 0 else 0.0
    return (now - before) / abs(before) * 100.0


# ---------------------------------------------------------------- RCAEval ---
def summarise_rcaeval(case: str) -> dict:
    from rcaeval_loader import detect_schema
    d = ROOT / "data" / "cases" / case
    m = pd.read_parquet(d / "metrics.parquet")
    inject = int((d / "inject_time.txt").read_text().strip())
    cols = [c for c in m.columns if c != "time"]
    g = detect_schema(cols)

    pre, post = m[m.time < inject], m[m.time >= inject]
    if len(pre) < 2 or len(post) < 2:
        raise ValueError(f"{case}: window too short")

    fam = {"cpu": "_cpu", "mem": "_mem",
           "latency": g["latency"], "workload": g["throughput"],
           "error": "_error"}

    svc: dict[str, dict] = {}
    for sig, suf in fam.items():
        if not suf:
            continue
        for c in cols:
            if not c.endswith(suf):
                continue
            name = c[: -len(suf)]
            a, b = float(pre[c].mean()), float(post[c].mean())
            if not (np.isfinite(a) and np.isfinite(b)):
                continue
            svc.setdefault(name, {})[sig] = (a, b, _pct(b, a))

    rows = []
    for name, sigs in svc.items():
        score = max((abs(v[2]) if np.isfinite(v[2]) else 1e9)
                    for v in sigs.values())
        rows.append((score, name, sigs))
    rows.sort(reverse=True, key=lambda r: r[0])

    return {"case": case, "n_services": len(svc),
            "window_s": int((post.time.max() - inject)),
            "services": [{"service": n,
                          "signals": {k: {"before": round(v[0], 4),
                                          "after": round(v[1], 4),
                                          "pct_change": (None if not np.isfinite(v[2])
                                                         else round(v[2], 1))}
                                      for k, v in s.items()}}
                         for _, n, s in rows]}


# ----------------------------------------------------------------- RCA100 ---
# signal family -> the RCA100 metric names that populate it.
#
# NODE METRICS ADDED 2026-09-23. Without them, 17 of 103 cases (16.5%) had a
# node-level root cause (e.g. cn-hongkong.10.0.1.69) that never appeared in the
# summary at all, capping achievable accuracy at 83.5% for a reason unrelated
# to the agent's reasoning. Measured, not assumed -- see the entity-kind census
# in the project notes.
M_MAP = {
    "cpu":      ["cpu", "node_cpu_usage_rate", "deployment_cpu_usage_total"],
    "mem":      ["mem", "node_memory_usage_rate", "deployment_memory_usage_total"],
    "disk":     ["node_disk_usage_rate"],
    "latency":  ["latency", "avg_request_latency_seconds"],
    "workload": ["request_count", "workload", "node_pod_running_count"],
    "error":    ["error_count", "error_rate"],
    "ready":    ["node_ready_status", "deployment_availability_rate"],
}


def summarise_rca100(task: str) -> dict:
    d = ROOT / "data" / "rca100" / "cases" / task
    m = pd.read_parquet(d / "metrics.parquet")
    t = json.loads((d / "task.json").read_text(encoding="utf-8"))
    w = t["alert_window"]
    start = pd.Timestamp(w["start"]).value // 1000
    end = pd.Timestamp(w["end"]).value // 1000

    pre, post = m[m.time < start], m[(m.time >= start) & (m.time <= end)]
    if post.empty:
        raise ValueError(f"{task}: empty alert window")
    if pre.empty:                       # no pre-window: use first 20%
        cut = m.time.quantile(0.2)
        pre, post = m[m.time < cut], m[m.time >= cut]

    svc: dict[str, dict] = {}
    for sig, metrics in M_MAP.items():
        sel_pre = pre[pre.metric.isin(metrics)]
        sel_post = post[post.metric.isin(metrics)]
        a = sel_pre.groupby("entity_name")["value"].mean()
        b = sel_post.groupby("entity_name")["value"].mean()
        for name in set(a.index) | set(b.index):
            x, y = float(a.get(name, 0.0)), float(b.get(name, 0.0))
            if not (np.isfinite(x) and np.isfinite(y)):
                continue
            svc.setdefault(name, {})[sig] = (x, y, _pct(y, x))

    rows = []
    for name, sigs in svc.items():
        score = max((abs(v[2]) if np.isfinite(v[2]) else 1e9)
                    for v in sigs.values())
        rows.append((score, name, sigs))
    rows.sort(reverse=True, key=lambda r: r[0])

    return {"case": task, "n_services": len(svc),
            "window_s": int((end - start) / 1e6),
            "alert": t.get("alert_title", "")[:160],
            "services": [{"service": n,
                          "signals": {k: {"before": round(v[0], 4),
                                          "after": round(v[1], 4),
                                          "pct_change": (None if not np.isfinite(v[2])
                                                         else round(v[2], 1))}
                                      for k, v in s.items()}}
                         for _, n, s in rows]}


# ------------------------------------------------------------------ render --
def render(summary: dict, top: int = 20) -> str:
    """Compact text the agent actually sees. Deterministic."""
    L = [f"Incident {summary['case']} | {summary['n_services']} services "
         f"| fault window {summary['window_s']}s"]
    if summary.get("alert"):
        L.append(f"Entry alert: {summary['alert']}")
    L.append("")
    L.append("Per-service shift, pre-fault mean -> in-fault mean "
             "(ranked by largest change):")
    for s in summary["services"][:top]:
        bits = []
        for sig, v in s["signals"].items():
            pc = v["pct_change"]
            tag = "new" if pc is None else f"{pc:+.0f}%"
            bits.append(f"{sig} {v['before']:.3g}->{v['after']:.3g} ({tag})")
        L.append(f"  {s['service']:<32} " + ", ".join(bits))
    if len(summary["services"]) > top:
        L.append(f"  ... {len(summary['services']) - top} further services "
                 f"with smaller changes")
    return "\n".join(L)


def build_all(verbose: bool = True) -> dict:
    CACHE.mkdir(parents=True, exist_ok=True)
    import rcaeval_loader, rca100_loader
    out = {"rcaeval": [], "rca100": []}

    idx = pd.read_parquet(ROOT / "data" / "cases.parquet")
    idx = idx[(idx.suite == "RE1") & (idx.system.isin(("ob", "ss")))]
    for c in idx["case"]:
        if not (ROOT / "data" / "cases" / c / "metrics.parquet").exists():
            continue
        try:
            out["rcaeval"].append(summarise_rcaeval(c))
        except Exception as e:                            # noqa: BLE001
            if verbose:
                print(f"  skip {c}: {type(e).__name__}")

    tasks = [t.strip() for t in
             (ROOT / "data" / "rca100" / "manifest.txt").read_text().split()
             if t.strip()]
    for t in tasks:
        if not (ROOT / "data" / "rca100" / "cases" / t /
                "metrics.parquet").exists():
            continue
        try:
            out["rca100"].append(summarise_rca100(t))
        except Exception as e:                            # noqa: BLE001
            if verbose:
                print(f"  skip {t}: {type(e).__name__}")

    for k, v in out.items():
        (CACHE / f"{k}.json").write_text(json.dumps(v), encoding="utf-8")
        if verbose:
            print(f"  cached {len(v)} {k} summaries -> {CACHE/f'{k}.json'}")
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", choices=["rcaeval", "rca100"])
    ap.add_argument("--limit", type=int, default=2)
    ap.add_argument("--build", action="store_true")
    a = ap.parse_args()

    if a.build:
        build_all()
        return

    if a.corpus == "rca100":
        tasks = [t.strip() for t in
                 (ROOT / "data" / "rca100" / "manifest.txt").read_text().split()
                 if t.strip()]
        for t in tasks[: a.limit]:
            print(render(summarise_rca100(t)))
            print("\n" + "=" * 70 + "\n")
    else:
        idx = pd.read_parquet(ROOT / "data" / "cases.parquet")
        idx = idx[(idx.suite == "RE1") & (idx.system == "ob")]
        for c in idx["case"][: a.limit]:
            print(render(summarise_rcaeval(c)))
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
