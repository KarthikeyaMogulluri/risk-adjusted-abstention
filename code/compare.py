"""
Cross-dataset comparison -- the test the paper actually needs.

One dataset is an artefact; two is a finding. RCAEval and RCA100 share nothing
but the stake equations: different systems, different collection method,
different file format (wide vs long), different loader, and RCA100 needs none
of the three substitutions RCAEval forced.

If the RCAEval refutation were an artefact of those substitutions or of the
wide-format parsing, it would not reproduce here.

    python compare.py
"""

from __future__ import annotations

import numpy as np

from stakes import StakeParams
from policy import CostParams, tau_act, straddles_boundary
from evaluate import all_baselines, simulate_confidence
from rebalance import calibrate
import rcaeval_loader
import rca100_loader

P = CostParams()
SP = StakeParams()


def load_both():
    _, _, _, a = rcaeval_loader.build_dataset("RE1", ("ob", "ss"), verbose=False)
    _, _, _, b = rca100_loader.build_dataset(verbose=False)
    return {"RCAEval RE1": a, "RCA100": b}


def compose(df, lam_exp, lam_slo, boost=1.0):
    return (df["rho_infra"].to_numpy()
            + lam_exp * df["r_fail"].to_numpy()
            + lam_slo * boost * df["burn"].to_numpy())


def analyse(df, lam_exp, lam_slo, boost=1.0):
    rho = compose(df, lam_exp, lam_slo, boost)
    D = SP.kappa * df["blast"].to_numpy() * float(np.mean(rho))
    T_e = df["T_faulty"].to_numpy()
    rng = np.random.default_rng(0)
    q, Y = simulate_confidence(len(rho), rng, 0.62, 0.08)
    res = all_baselines(q, Y, rho, D, T_e, P)
    ta = tau_act(rho, D, P)
    s = straddles_boundary(D, P)
    return {
        "n": len(rho),
        "decades": float(np.log10(rho.max() / max(rho.min(), 1e-12))),
        "iqr": float(np.subtract(*np.percentile(ta, [75, 25]))),
        "rises": s["frac_threshold_rises_with_stake"],
        "hind": res["fixed_hindsight"],
        "ours": res["derived"],
        "delta": (res["derived"] - res["fixed_hindsight"]) / res["fixed_hindsight"] * 100,
        "viol": res["_diagnostics"]["ordering_violation_fraction"],
    }


def main() -> None:
    data = load_both()

    print("=" * 74)
    print("1.  STRUCTURAL COMPARISON")
    print("=" * 74)
    print(f"{'':<30}{'RCAEval RE1':>20}{'RCA100':>20}")
    a, b = data["RCAEval RE1"], data["RCA100"]
    rows = [
        ("cases", f"{len(a)}", f"{len(b)}"),
        ("format", "wide", "long"),
        ("replica counts", "absent (proxied)", "measured"),
        ("error signal", "3-5 svcs + latency", "per-entity"),
        ("call graph", "static published", "measured in-window"),
        ("burn == 0", f"{(a.burn==0).mean():.1%}", f"{(b.burn==0).mean():.1%}"),
        ("blast radius range", f"{a.blast.min():.0f}-{a.blast.max():.0f}",
         f"{b.blast.min():.0f}-{b.blast.max():.0f}"),
        ("infra spread (max/min)", f"{a.rho_infra.max()/max(a.rho_infra.min(),1e-12):.1f}x",
         f"{b.rho_infra.max()/max(b.rho_infra.min(),1e-12):.2f}x"),
    ]
    for k, v1, v2 in rows:
        print(f"{k:<30}{v1:>20}{v2:>20}")

    print()
    print("=" * 74)
    print("2.  BALANCED COMPOSITION -- the pre-registered gate on each")
    print("=" * 74)
    print(f"{'':<16}{'n':>6}{'decades':>9}{'tauIQR':>9}{'rises':>8}"
          f"{'hind':>9}{'ours':>9}{'delta':>9}{'verdict':>10}")
    print("-" * 74)
    bal = {}
    for name, df in data.items():
        le, ls, _ = calibrate(df)
        r = analyse(df, le, ls)
        bal[name] = (le, ls, r)
        verdict = "REFUTED" if (r["rises"] in (0.0, 1.0) or r["iqr"] < 0.10) else "pass"
        print(f"{name:<16}{r['n']:>6}{r['decades']:>9.2f}{r['iqr']:>9.3f}"
              f"{r['rises']:>8.0%}{r['hind']:>9.4f}{r['ours']:>9.4f}"
              f"{r['delta']:>+9.1f}%{verdict:>10}")

    print()
    print("=" * 74)
    print("3.  BURN-DOMINANCE SWEEP -- does the win-window reproduce?")
    print("=" * 74)
    print(f"{'boost':>8}", end="")
    for name in data:
        print(f"{name:>26}", end="")
    print()
    print(f"{'':>8}", end="")
    for _ in data:
        print(f"{'tauIQR':>9}{'delta':>9}{'':>8}", end="")
    print()
    print("-" * 74)
    for boost in [1, 3, 10, 30, 100, 300, 1000, 10000]:
        print(f"{boost:>8}", end="")
        for name, df in data.items():
            le, ls, _ = bal[name]
            r = analyse(df, le, ls, boost)
            mark = "  win" if r["delta"] < 0 else "     "
            print(f"{r['iqr']:>9.3f}{r['delta']:>+9.1f}%{mark:>8}", end="")
        print()

    print()
    print("=" * 74)
    print("4.  ORDERING VIOLATION (tau_assist > tau_act)")
    print("=" * 74)
    for name, (le, ls, r) in bal.items():
        print(f"  {name:<16} {r['viol']:.1%}")
    print("  synthetic baseline   35-39%")


if __name__ == "__main__":
    main()
