"""
Component rebalancing and a sensitivity sweep that actually tests something.

WHY THIS EXISTS
---------------
The first sweep varied lambda_exp and lambda_slo across four and two decades
and returned -9.8% in thirteen of fifteen settings. That flatness was not
robustness. With the error-budget term five orders of magnitude larger than
the other two, rho was effectively a one-term model, and varying that one
term's price is a common rescale -- which Proposition 3 proves cancels. The
sweep re-proved a proposition instead of testing misspecification.

THE FIX
-------
Calibrate the exchange rates so each component contributes comparably, then
sweep the RELATIVE weights on a simplex. Three changes follow:

  1. lambda is calibrated by equalising each component's 90th percentile
     against the infrastructure component's. The 90th percentile is used
     rather than the median because burn is legitimately zero on ~36% of
     cases (faults that never breached the SLO), and a zero median makes the
     calibration undefined.

  2. The sweep varies (w_infra, w_exp, w_slo) on a simplex summing to 1.
     Moving along a simplex changes the components RELATIVE to each other,
     which is what misspecification means. Scaling all three together is the
     change of currency Proposition 3 already covers.

  3. Dollar denomination is preserved, so D and w*H_e stay commensurable and
     the loss function is unchanged.

    python rebalance.py
"""

from __future__ import annotations

import itertools

import numpy as np

from rcaeval_loader import build_dataset
from stakes import StakeParams
from policy import CostParams, tau_act, straddles_boundary
from evaluate import all_baselines, simulate_confidence


def calibrate(df, anchor_q: float = 0.90) -> tuple[float, float, dict]:
    """Equalise each component's `anchor_q` quantile against infrastructure."""
    a_inf = float(np.quantile(df["rho_infra"], anchor_q))
    a_exp = float(np.quantile(df["r_fail"], anchor_q))
    a_slo = float(np.quantile(df["burn"], anchor_q))

    lam_exp = a_inf / a_exp if a_exp > 0 else 0.0
    lam_slo = a_inf / a_slo if a_slo > 0 else 0.0
    return lam_exp, lam_slo, {"infra": a_inf, "exp": a_exp, "slo": a_slo}


def compose(df, lam_exp, lam_slo, w) -> np.ndarray:
    """rho under relative weights w = (w_infra, w_exp, w_slo), sum(w) = 1."""
    wi, we, ws = w
    return (3.0 * (wi * df["rho_infra"].to_numpy()
                   + we * lam_exp * df["r_fail"].to_numpy()
                   + ws * lam_slo * df["burn"].to_numpy()))


def simplex(step: int = 4):
    """Weight triples on a simplex, excluding all-zero corners."""
    for i, j in itertools.product(range(step + 1), repeat=2):
        k = step - i - j
        if k < 0:
            continue
        w = (i / step, j / step, k / step)
        if sum(x > 0 for x in w) >= 2:       # need at least two live terms
            yield w


def main() -> None:
    p = CostParams()
    sp0 = StakeParams()
    _, _, _, df = build_dataset("RE1", ("ob", "ss"), sp=sp0, verbose=True)
    D_raw = df["blast"].to_numpy()
    T_e = df["T_faulty"].to_numpy()

    lam_exp, lam_slo, anchors = calibrate(df)
    print(f"\ncalibrated at the 90th percentile")
    print(f"  p90 infra {anchors['infra']:.4e} USD/s")
    print(f"  p90 r_fail {anchors['exp']:.4e} req/s  -> lambda_exp {lam_exp:.4e}")
    print(f"  p90 burn  {anchors['slo']:.4e} /s      -> lambda_slo {lam_slo:.4e}")

    # balanced point
    wbal = (1 / 3, 1 / 3, 1 / 3)
    rho = compose(df, lam_exp, lam_slo, wbal)
    shares = [np.median(3 * w * c) for w, c in zip(
        wbal, [df["rho_infra"], lam_exp * df["r_fail"], lam_slo * df["burn"]])]
    print(f"\ncomponent medians at the balanced point (USD/s)")
    for nm, s in zip(("infra ", "exposure", "burn  "), shares):
        print(f"  {nm} {s:.4e}")

    print(f"\nrho spread {np.log10(rho.max()/max(rho.min(),1e-12)):.2f} decades"
          f"  (was 9.30 with the unbalanced lambda)")

    # --- RQ1 under the balanced composition ---------------------------------
    D = sp0.kappa * D_raw * float(np.mean(rho))
    v = straddles_boundary(D, p)
    ta = tau_act(rho, D, p)
    print(f"\nRQ1 rises {v['frac_threshold_rises_with_stake']:.1%} / "
          f"falls {v['frac_threshold_falls_with_stake']:.1%}   "
          f"tau_act IQR {np.subtract(*np.percentile(ta,[75,25])):.3f}")

    # --- the sweep that actually varies relative weighting -------------------
    rng_seed = 0
    print(f"\n{'w_infra':>8}{'w_exp':>8}{'w_slo':>8} |{'decades':>9}"
          f"{'hindsight':>11}{'derived':>9}{'delta':>9}")
    print("-" * 64)
    deltas, rows = [], []
    for w in simplex(4):
        r = compose(df, lam_exp, lam_slo, w)
        d = sp0.kappa * D_raw * float(np.mean(r))
        rng = np.random.default_rng(rng_seed)
        q, Y = simulate_confidence(len(r), rng, base_accuracy=0.62, miscal=0.08)
        res = all_baselines(q, Y, r, d, T_e, p)
        delta = (res["derived"] - res["fixed_hindsight"]) / res["fixed_hindsight"] * 100
        dec = np.log10(r.max() / max(r.min(), 1e-12))
        deltas.append(delta)
        rows.append((w, dec, res["fixed_hindsight"], res["derived"], delta))
        print(f"{w[0]:8.2f}{w[1]:8.2f}{w[2]:8.2f} |{dec:9.2f}"
              f"{res['fixed_hindsight']:11.4f}{res['derived']:9.4f}{delta:+9.1f}%")

    deltas = np.array(deltas)
    print("-" * 64)
    print(f"derived wins in {np.sum(deltas < 0)}/{len(deltas)} weightings")
    print(f"delta range {deltas.min():+.1f}% to {deltas.max():+.1f}%   "
          f"median {np.median(deltas):+.1f}%   spread {deltas.ptp():.1f} pts")
    if deltas.ptp() < 1.0:
        print("\nWARNING: still flat. A live sweep should move the answer.")
    else:
        print("\nSweep now varies the answer -- it is testing misspecification.")
    worst = rows[int(np.argmax(deltas))]
    print(f"breakdown point: w={tuple(round(x,2) for x in worst[0])} "
          f"-> {worst[4]:+.1f}%")


if __name__ == "__main__":
    main()
