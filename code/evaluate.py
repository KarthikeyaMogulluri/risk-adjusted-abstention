"""
Evaluation harness -- Section 5 of the paper, executable.

Realised costs (Eqs. 4-6), the perfect-information oracle, all five baselines,
cost-weighted regret, risk-coverage curves and ECE.

Nothing here invents a measurement. Given real stake arrays from stakes.py and
a real or simulated confidence signal, it produces the numbers that populate
Section 6. Run it on benchmark data and Section 6 fills itself.

    python evaluate.py --demo      # harness self-check on synthetic stakes
"""

from __future__ import annotations

import argparse
import numpy as np

from policy import (CostParams, ACT, ASSIST, ESCALATE, ACTION_NAMES,
                    tau_act, tau_assist, derived_policy, fixed_policy)


# ---------------------------------------------------------------------------
# Realised cost -- Eqs. (4)-(6), evaluated with the outcome known
# ---------------------------------------------------------------------------

def realised_cost(action: np.ndarray, Y: np.ndarray, rho: np.ndarray,
                  D: np.ndarray, T_e: np.ndarray, p: CostParams) -> np.ndarray:
    """Cost actually incurred, per incident. Y=1 means the hypothesis was right."""
    c = np.empty(len(action), dtype=float)

    m = action == ACT
    c[m] = np.where(
        Y[m] == 1,
        rho[m] * (T_e[m] - p.delta_plus_act),
        rho[m] * (T_e[m] + p.delta_minus_act) + p.wHe + D[m],
    )

    m = action == ASSIST
    c[m] = np.where(
        Y[m] == 1,
        rho[m] * (T_e[m] - p.delta_plus_assist) + p.w * (p.H_e - p.eta_plus),
        rho[m] * (T_e[m] + p.delta_minus_assist) + p.w * (p.H_e + p.eta_minus),
    )

    m = action == ESCALATE
    c[m] = rho[m] * T_e[m] + p.wHe

    return c


def oracle_cost(Y, rho, D, T_e, p) -> tuple[np.ndarray, np.ndarray]:
    """Perfect information: knows Y, picks the cheapest action. Lower bound."""
    n = len(Y)
    costs = np.stack([
        realised_cost(np.full(n, a), Y, rho, D, T_e, p)
        for a in (ACT, ASSIST, ESCALATE)
    ])
    best = np.argmin(costs, axis=0)
    return costs[best, np.arange(n)], best


def regret(action, Y, rho, D, T_e, p) -> float:
    """Cost-weighted regret against the oracle. The paper's primary metric.

    Normalised by the oracle's total cost so it is comparable across datasets
    and invariant to the currency unit (Proposition 3).
    """
    oc, _ = oracle_cost(Y, rho, D, T_e, p)
    pc = realised_cost(action, Y, rho, D, T_e, p)
    return float((pc.sum() - oc.sum()) / oc.sum())


# ---------------------------------------------------------------------------
# Baselines -- Section 5.3, in increasing order of strength
# ---------------------------------------------------------------------------

def tune_fixed_threshold(q, Y, rho, D, T_e, p, grid=401) -> tuple[float, float]:
    """Baseline 4: the best possible CONSTANT, tuned ON THE TEST SET.

    This grants the baseline information no deployable system could have. That
    is deliberate -- beating an untuned threshold would prove nothing. If our
    method cannot beat this, we have no result and the paper says so.
    """
    taus = np.linspace(0.0, 1.0, grid)
    regrets = [regret(fixed_policy(q, t, rho, D, p), Y, rho, D, T_e, p)
               for t in taus]
    i = int(np.argmin(regrets))
    return float(taus[i]), float(regrets[i])


def all_baselines(q, Y, rho, D, T_e, p) -> dict:
    n = len(q)
    out = {}
    out["always_act"] = regret(np.full(n, ACT), Y, rho, D, T_e, p)
    out["always_escalate"] = regret(np.full(n, ESCALATE), Y, rho, D, T_e, p)
    out["fixed_0.80"] = regret(fixed_policy(q, 0.80, rho, D, p),
                               Y, rho, D, T_e, p)
    tau_star, r_star = tune_fixed_threshold(q, Y, rho, D, T_e, p)
    out["fixed_hindsight"] = r_star
    out["_hindsight_tau"] = tau_star

    actions, diag = derived_policy(q, rho, D, p)
    out["derived"] = regret(actions, Y, rho, D, T_e, p)
    out["_diagnostics"] = diag
    out["_coverage"] = coverage(actions)
    return out


# ---------------------------------------------------------------------------
# Secondary metrics
# ---------------------------------------------------------------------------

def coverage(action: np.ndarray) -> float:
    """Fraction of incidents the system did not hand over without a hypothesis."""
    return float(np.mean(action != ESCALATE))


def expected_calibration_error(q: np.ndarray, Y: np.ndarray,
                               bins: int = 15) -> float:
    edges = np.linspace(0.0, 1.0, bins + 1)
    idx = np.clip(np.digitize(q, edges) - 1, 0, bins - 1)
    ece = 0.0
    for b in range(bins):
        m = idx == b
        if not m.any():
            continue
        ece += (m.mean()) * abs(Y[m].mean() - q[m].mean())
    return float(ece)


def risk_coverage_curve(q, Y, rho, D, T_e, p, points=50):
    """Risk against coverage, sweeping a constant threshold.

    Section 5.4 requires this STRATIFIED BY STAKE DECILE -- the stratification
    is what makes the effect visible. Pass a stake-decile mask as a subset.
    """
    taus = np.linspace(1.0, 0.0, points)
    cov, risk = [], []
    for t in taus:
        a = fixed_policy(q, t, rho, D, p)
        cov.append(coverage(a))
        risk.append(regret(a, Y, rho, D, T_e, p))
    return np.array(cov), np.array(risk)


def stake_decile_masks(rho: np.ndarray, k: int = 10) -> list[np.ndarray]:
    edges = np.quantile(rho, np.linspace(0, 1, k + 1))
    return [(rho >= edges[i]) & (rho <= edges[i + 1]) for i in range(k)]


# ---------------------------------------------------------------------------
# Confidence simulation -- Section 5.6
# ---------------------------------------------------------------------------

def simulate_confidence(n, rng, base_accuracy=0.62, miscal=0.0):
    """Generate (q, Y) at a stated calibration quality.

    True correctness probability p_i ~ Beta centred on base_accuracy; Y drawn
    from it, so the signal is calibrated BY CONSTRUCTION. `miscal` injects
    additive noise to reach a target ECE, reported rather than assumed.

    Used ONLY for the decision-layer study (Sec 5.6). Stake arrays are always
    measured, never simulated. The end-to-end agent study is follow-on work.
    """
    a = base_accuracy * 4.0
    b = (1.0 - base_accuracy) * 4.0
    p_true = rng.beta(a, b, n)
    Y = (rng.random(n) < p_true).astype(int)
    q = np.clip(p_true + rng.normal(0.0, miscal, n), 1e-6, 1 - 1e-6)
    return q, Y


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def report(res: dict, ece: float) -> None:
    print(f"{'Policy':<24}{'Regret':>10}{'vs hindsight':>15}")
    print("-" * 49)
    hs = res["fixed_hindsight"]
    for k in ("always_act", "always_escalate", "fixed_0.80",
              "fixed_hindsight", "derived"):
        delta = ""
        if k == "derived":
            delta = f"{(res[k] - hs) / hs * 100:+.1f}%" if hs else "n/a"
        label = "DERIVED (ours)" if k == "derived" else k
        print(f"{label:<24}{res[k]:>10.4f}{delta:>15}")
    print("-" * 49)
    print(f"{'oracle':<24}{0.0:>10.4f}")
    print()
    print(f"hindsight-tuned tau*      : {res['_hindsight_tau']:.3f}")
    print(f"derived tau_act range     : "
          f"[{res['_diagnostics']['tau_act_range'][0]:.3f}, "
          f"{res['_diagnostics']['tau_act_range'][1]:.3f}]")
    print(f"coverage (derived)        : {res['_coverage']:.3f}")
    print(f"ordering violations       : "
          f"{res['_diagnostics']['ordering_violation_fraction']:.2%}")
    print(f"ECE of confidence signal  : {ece:.4f}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo", action="store_true",
                    help="harness self-check on SYNTHETIC stakes")
    ap.add_argument("--n", type=int, default=5000)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    if not args.demo:
        print(__doc__)
        print("Real stakes come from stakes.py once datasets are verified "
              "(Day 1). Use --demo to exercise the harness.")
        return

    print("=" * 60)
    print("HARNESS SELF-CHECK -- SYNTHETIC STAKES, NOT A RESULT")
    print("These numbers verify the code runs. They are not measurements")
    print("and must never appear in the paper.")
    print("=" * 60 + "\n")

    rng = np.random.default_rng(args.seed)
    n = args.n
    p = CostParams()

    rho = 10.0 ** rng.uniform(-5, 0, n)
    D = 10.0 ** rng.uniform(-2, 4, n)
    T_e = rng.lognormal(np.log(3600), 0.8, n)
    q, Y = simulate_confidence(n, rng, miscal=0.08)

    res = all_baselines(q, Y, rho, D, T_e, p)
    report(res, expected_calibration_error(q, Y))


if __name__ == "__main__":
    main()
