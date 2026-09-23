"""
End-to-end verification: recompute every number the paper claims and compare.

Run before submission. Any MISMATCH is a number in the paper that the code no
longer produces -- either the code drifted or the paper was never updated.

    python verify_paper.py
"""

from __future__ import annotations

import numpy as np
from scipy.optimize import brentq

from stakes import StakeParams
from policy import (CostParams, tau_act, tau_assist, straddles_boundary,
                    ACT, ESCALATE, derived_policy)
from evaluate import (all_baselines, simulate_confidence, regret,
                      tune_fixed_threshold, expected_calibration_error)
from rebalance import calibrate, compose, simplex
import rcaeval_loader
import rca100_loader

P, SP = CostParams(), StakeParams()
PASS, FAIL = [], []


def chk(label, claimed, actual, tol=0.02, pct=False):
    """tol is relative unless the claim is 0, then absolute."""
    if isinstance(claimed, str) or isinstance(actual, str):
        good = str(claimed) == str(actual)
    elif claimed == 0:
        good = abs(actual) < 1e-9
    else:
        good = abs(actual - claimed) / abs(claimed) <= tol
    tag = "ok  " if good else "MISMATCH"
    fmt = (lambda v: f"{v:.4g}") if not isinstance(claimed, str) else str
    line = f"  [{tag}] {label:<46} paper={fmt(claimed):>10}  code={fmt(actual):>10}"
    (PASS if good else FAIL).append(line)
    print(line)


def build(name):
    if name == "rcaeval":
        _, _, _, df = rcaeval_loader.build_dataset("RE1", ("ob", "ss"),
                                                   verbose=False)
    else:
        _, _, _, df = rca100_loader.build_dataset(verbose=False)
    le, ls, _ = calibrate(df)
    return df, le, ls


def analyse(df, le, ls, boost=1.0):
    rho = (df["rho_infra"].to_numpy() + le * df["r_fail"].to_numpy()
           + ls * boost * df["burn"].to_numpy())
    D = SP.kappa * df["blast"].to_numpy() * float(np.mean(rho))
    T_e = df["T_faulty"].to_numpy()
    rng = np.random.default_rng(0)
    q, Y = simulate_confidence(len(rho), rng, 0.62, 0.08)
    return rho, D, T_e, q, Y


def main() -> None:
    print("=" * 84)
    print("1.  PROPOSITIONS  (re-verified numerically)")
    print("=" * 84)
    rng = np.random.default_rng(0)
    r = 10.0 ** rng.uniform(-6, 1, 20000)
    d = 10.0 ** rng.uniform(-3, 5, 20000)
    ta, ts = tau_act(r, d, P), tau_assist(r, P)
    chk("Prop 1: tau_act in [0,1]", "yes",
        "yes" if np.all((ta >= 0) & (ta <= 1)) else "no")
    chk("Prop 1: tau_assist in [0,1]", "yes",
        "yes" if np.all((ts >= 0) & (ts <= 1)) else "no")
    h = r * 1e-6
    num = (tau_act(r + h, d, P) - tau_act(r - h, d, P)) / (2 * h)
    from policy import dtau_dstake_sign
    ana = dtau_dstake_sign(d, P)
    live = np.abs(num) > 1e-14
    chk("Prop 2: analytic sign == finite difference", "yes",
        "yes" if (np.sign(num[live]) == ana[live]).all() else "no")

    data = {n: build(n) for n in ("rcaeval", "rca100")}

    print()
    print("=" * 84)
    print("2.  CORPUS DESCRIPTIVES")
    print("=" * 84)
    claims = {
        "rcaeval": dict(n=249, zero_burn=0.365, blast_lo=0, blast_hi=9,
                        infra_spread=5.6),
        "rca100": dict(n=103, zero_burn=0.010, blast_lo=0, blast_hi=68,
                       infra_spread=1.07),
    }
    for name, (df, le, ls) in data.items():
        c = claims[name]
        print(f" {name}:")
        chk("cases", c["n"], len(df))
        chk("zero-burn fraction", c["zero_burn"], float((df.burn == 0).mean()),
            tol=0.05)
        chk("blast radius max", c["blast_hi"], int(df.blast.max()))
        chk("infra spread (max/min)", c["infra_spread"],
            float(df.rho_infra.max() / max(df.rho_infra.min(), 1e-12)), tol=0.05)

    print()
    print("=" * 84)
    print("3.  RQ1 GATE  (balanced composition)")
    print("=" * 84)
    rq1 = {"rcaeval": dict(dec=1.51, iqr=0.056, rises=1.0),
           "rca100": dict(dec=0.56, iqr=0.016, rises=1.0)}
    for name, (df, le, ls) in data.items():
        rho, D, T_e, q, Y = analyse(df, le, ls)
        c = rq1[name]
        print(f" {name}:")
        chk("stake spread (decades)", c["dec"],
            float(np.log10(rho.max() / max(rho.min(), 1e-12))), tol=0.05)
        t = tau_act(rho, D, P)
        chk("tau_act IQR", c["iqr"],
            float(np.subtract(*np.percentile(t, [75, 25]))), tol=0.08)
        chk("fraction rising with stake", c["rises"],
            straddles_boundary(D, P)["frac_threshold_rises_with_stake"])

    print()
    print("=" * 84)
    print("4.  HEADLINE TABLE")
    print("=" * 84)
    head = {
        "rcaeval": dict(act=0.0727, esc=1.5350, f80=0.8474, hind=0.0727,
                        der=0.1015, ece=0.070, tau=0.000),
        "rca100": dict(act=0.0250, esc=1.7077, f80=0.7871, hind=0.0172,
                       der=0.0250, ece=0.097, tau=0.333),
    }
    deltas = {}
    for name, (df, le, ls) in data.items():
        rho, D, T_e, q, Y = analyse(df, le, ls)
        n = len(rho)
        c = head[name]
        print(f" {name}:")
        chk("always act regret", c["act"],
            regret(np.full(n, ACT), Y, rho, D, T_e, P), tol=0.03)
        chk("always escalate regret", c["esc"],
            regret(np.full(n, ESCALATE), Y, rho, D, T_e, P), tol=0.03)
        res = all_baselines(q, Y, rho, D, T_e, P)
        chk("hindsight-tuned regret", c["hind"], res["fixed_hindsight"], tol=0.03)
        chk("derived regret", c["der"], res["derived"], tol=0.03)
        chk("tuned tau*", c["tau"], res["_hindsight_tau"], tol=0.05)
        chk("ECE of q", c["ece"], expected_calibration_error(q, Y), tol=0.10)
        d = (res["derived"] - res["fixed_hindsight"]) / res["fixed_hindsight"] * 100
        deltas[name] = d
        chk("delta vs tuned (%)",
            39.6 if name == "rcaeval" else 45.0, d, tol=0.05)
        chk("ordering violated fraction", 1.0,
            res["_diagnostics"]["ordering_violation_fraction"])

    print()
    print("=" * 84)
    print("5.  SIMPLEX SWEEP  (paper: loses 12/12, +5.9% to +41.2%)")
    print("=" * 84)
    df, le, ls = data["rcaeval"]
    ds = []
    for w in simplex(4):
        rho = compose(df, le, ls, w)
        D = SP.kappa * df["blast"].to_numpy() * float(np.mean(rho))
        rng2 = np.random.default_rng(0)
        q, Y = simulate_confidence(len(rho), rng2, 0.62, 0.08)
        res = all_baselines(q, Y, rho, D, df["T_faulty"].to_numpy(), P)
        ds.append((res["derived"] - res["fixed_hindsight"])
                  / res["fixed_hindsight"] * 100)
    ds = np.array(ds)
    chk("weightings tested", 12, len(ds))
    chk("number where derived loses", 12, int((ds > 0).sum()))
    chk("min delta (%)", 5.9, float(ds.min()), tol=0.05)
    chk("max delta (%)", 41.2, float(ds.max()), tol=0.05)

    print()
    print("=" * 84)
    print("6.  rho*  (paper: 0.031 USD/s = $111/hr; shortfall 34x / 80x)")
    print("=" * 84)

    def crossover(D_):
        f = lambda lr: (tau_assist(np.array([10 ** lr]), P)[0]
                        - tau_act(np.array([10 ** lr]), np.array([D_]), P)[0])
        try:
            return 10 ** brentq(f, -8, 8)
        except Exception:
            return np.nan

    chk("rho* at D=0 (USD/s)", 0.031, crossover(0.0), tol=0.05)
    chk("rho* per hour (USD)", 111.3, crossover(0.0) * 3600, tol=0.05)
    short = {"rcaeval": 34, "rca100": 80}
    hourly = {"rcaeval": 3.24, "rca100": 1.38}
    for name, (df, le, ls) in data.items():
        rho, D, *_ = analyse(df, le, ls)
        med = float(np.median(rho))
        print(f" {name}:")
        chk("median stake per hour (USD)", hourly[name], med * 3600, tol=0.05)
        rs = np.array([crossover(x) for x in D])
        chk("median shortfall factor", short[name],
            float(np.nanmedian(rs / np.maximum(rho, 1e-12))), tol=0.06)

    print()
    print("=" * 84)
    print(f"VERIFIED {len(PASS)}   MISMATCHED {len(FAIL)}")
    print("=" * 84)
    if FAIL:
        print("\nEvery line below is a number in the paper the code does not "
              "reproduce:\n")
        for f in FAIL:
            print(f)
    else:
        print("\nEvery number checked reproduces. The paper matches the code.")


if __name__ == "__main__":
    main()
