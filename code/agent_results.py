"""
Bridge: real agent output -> the verified evaluation pipeline.

Reads the JSONL written by agent.py, substitutes the real (q, Y) for the
simulated pair, and re-runs exactly the analysis verify_paper.py already
checks. Nothing downstream is modified, so any change in the conclusions is
attributable to the confidence signal and not to the harness.

Reports, in this order:
  1. accuracy against the TRIVIAL rank-1 baseline -- an agent that cannot beat
     "pick the largest anomaly" has not earned its place in the paper
  2. measured ECE, replacing the simulated 0.070 / 0.097
  3. the full baseline table and the RQ1 gate on real confidence

    python agent_results.py --corpus rca100
"""

from __future__ import annotations

import argparse
import json
import pathlib

import numpy as np

from stakes import StakeParams
from policy import CostParams, tau_act, straddles_boundary
from evaluate import (all_baselines, expected_calibration_error, regret,
                      ACT, ESCALATE)
from rebalance import calibrate, compose

ROOT = pathlib.Path(__file__).resolve().parent.parent
RUNS = ROOT / "data" / "agent_runs"
P, SP = CostParams(), StakeParams()


def load_run(corpus: str, pattern: str = "*") -> dict:
    files = sorted(RUNS.glob(f"{corpus}_{pattern}.jsonl"))
    if not files:
        raise SystemExit(f"no runs found in {RUNS} for {corpus}. "
                         f"Run: python agent.py --corpus {corpus}")
    recs = {}
    for f in files:
        for line in f.open(encoding="utf-8"):
            if not line.strip():
                continue
            r = json.loads(line)
            recs.setdefault(r["case"], []).append(r)
    print(f"  {len(recs)} cases from {len(files)} run file(s)")
    return recs


def build_stakes(corpus: str):
    if corpus == "rcaeval":
        import rcaeval_loader
        _, _, _, df = rcaeval_loader.build_dataset("RE1", ("ob", "ss"),
                                                   verbose=False)
        key = "case"
    else:
        import rca100_loader
        _, _, _, df = rca100_loader.build_dataset(verbose=False)
        key = "task"
    le, ls, _ = calibrate(df)
    rho = compose(df, le, ls, (1 / 3, 1 / 3, 1 / 3))
    D = SP.kappa * df["blast"].to_numpy() * float(np.mean(rho))
    return dict(zip(df[key], zip(rho, D, df["T_faulty"].to_numpy())))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", choices=["rcaeval", "rca100"], default="rca100")
    a = ap.parse_args()

    recs = load_run(a.corpus)
    stakes = build_stakes(a.corpus)

    cases, q, Y, Yr = [], [], [], []
    for c, rs in recs.items():
        if c not in stakes:
            continue
        cases.append(c)
        q.append(float(np.mean([r["q"] for r in rs])))
        Y.append(int(round(np.mean([r["Y"] for r in rs]))))
        Yr.append(int(rs[0].get("Y_rank1", 0)))
    q, Y, Yr = np.asarray(q), np.asarray(Y), np.asarray(Yr)
    rho = np.array([stakes[c][0] for c in cases])
    D = np.array([stakes[c][1] for c in cases])
    T_e = np.array([stakes[c][2] for c in cases])
    n = len(cases)

    print()
    print("=" * 70)
    print("1.  DID THE AGENT BEAT THE TRIVIAL BASELINE?")
    print("=" * 70)
    print(f"  cases                    {n}")
    print(f"  agent accuracy           {Y.mean():.1%}")
    print(f"  rank-1 baseline          {Yr.mean():.1%}")
    d = Y.mean() - Yr.mean()
    print(f"  difference               {d:+.1%}")
    if d <= 0:
        print("  -> the agent does NOT beat picking the largest anomaly.")
        print("     Report this. It bounds what any confidence signal built")
        print("     on it can be worth.")

    print()
    print("=" * 70)
    print("2.  CALIBRATION  (replaces the simulated value)")
    print("=" * 70)
    ece = expected_calibration_error(q, Y)
    print(f"  measured ECE             {ece:.4f}")
    print(f"  simulated ECE in paper   {0.070 if a.corpus=='rcaeval' else 0.097:.4f}")
    print(f"  mean stated confidence   {q.mean():.3f}")
    print(f"  actual accuracy          {Y.mean():.3f}")
    print(f"  overconfidence           {q.mean()-Y.mean():+.3f}")
    print(f"  distinct q values        {len(np.unique(q))}")
    if len(np.unique(q)) < 5:
        print("  -> confidence is nearly constant; a threshold on it cannot")
        print("     discriminate, whatever the stake model says.")

    print()
    print("=" * 70)
    print("3.  BASELINES ON REAL CONFIDENCE")
    print("=" * 70)
    res = all_baselines(q, Y, rho, D, T_e, P)
    print(f"  always act               {regret(np.full(n,ACT),Y,rho,D,T_e,P):.4f}")
    print(f"  always escalate          {regret(np.full(n,ESCALATE),Y,rho,D,T_e,P):.4f}")
    print(f"  hindsight-tuned          {res['fixed_hindsight']:.4f}  "
          f"(tau*={res['_hindsight_tau']:.3f})")
    print(f"  derived (ours)           {res['derived']:.4f}")
    delta = (res["derived"] - res["fixed_hindsight"]) / res["fixed_hindsight"] * 100
    print(f"  delta vs tuned           {delta:+.1f}%")
    print(f"  coverage                 {res['_coverage']:.3f}")
    print(f"  ordering violated        "
          f"{res['_diagnostics']['ordering_violation_fraction']:.1%}")

    print()
    print("=" * 70)
    print("4.  RQ1 GATE ON REAL CONFIDENCE")
    print("=" * 70)
    t = tau_act(rho, D, P)
    s = straddles_boundary(D, P)
    print(f"  stake spread (decades)   "
          f"{np.log10(rho.max()/max(rho.min(),1e-12)):.2f}")
    print(f"  tau_act IQR              "
          f"{np.subtract(*np.percentile(t,[75,25])):.3f}")
    print(f"  rises with stake         "
          f"{s['frac_threshold_rises_with_stake']:.0%}")
    print()
    print("  The stake side is unchanged by definition -- only q and Y are new.")
    print("  If the verdict moves, it moved because of the confidence signal.")


if __name__ == "__main__":
    main()
