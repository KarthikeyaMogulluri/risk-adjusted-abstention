"""
RQ1 -- the gating question. Run this FIRST. Everything else waits on it.

    Does a realistic incident population straddle the sign-flip boundary of
    Proposition 2, and is stake variance large enough that a fixed threshold
    is measurably wrong?

The paper's pre-registered falsification condition (Section 1) is tested here.
This script prints one of two verdicts and the paper follows whichever it
gets. The negative-result wording is already drafted in main.tex -- search for
`IF RQ1 IS REFUTED`. There is no cost to an honest answer.

    python run_rq1.py --dataset rcaeval --root <path>
"""

from __future__ import annotations

import argparse
import numpy as np

from policy import CostParams, straddles_boundary, tau_act
from stakes import sanity_check, load_rcaeval, load_rca100


# Pre-registered decision rule. Fixed BEFORE seeing data, so it cannot be
# adjusted afterwards to produce the answer we would prefer.
MIN_MINORITY_FRACTION = 0.05   # >=5% of incidents on the minority side
MIN_STAKE_DECADES = 1.0        # >=1 decade of stake spread
MIN_TAU_SPREAD = 0.10          # >=0.10 spread in derived tau_act


def verdict(rho, D, p: CostParams) -> dict:
    s = straddles_boundary(D, p)
    decades = float(np.log10(rho.max() / max(rho.min(), 1e-12)))
    ta = tau_act(rho, D, p)
    tau_spread = float(ta.max() - ta.min())

    passes = (
        s["minority_side_fraction"] >= MIN_MINORITY_FRACTION
        and decades >= MIN_STAKE_DECADES
        and tau_spread >= MIN_TAU_SPREAD
    )
    return {**s, "stake_decades": decades, "tau_spread": tau_spread,
            "tau_act_iqr": float(np.subtract(*np.percentile(ta, [75, 25]))),
            "PASS": passes}


def report(v: dict) -> None:
    print("\n" + "=" * 64)
    print("RQ1 -- PRE-REGISTERED GATING TEST")
    print("=" * 64)
    print(f"incidents                        : {v['n']:,}")
    print(f"stake spread                     : {v['stake_decades']:.2f} decades"
          f"   (need >= {MIN_STAKE_DECADES})")
    print(f"derived tau_act spread           : {v['tau_spread']:.3f}"
          f"        (need >= {MIN_TAU_SPREAD})")
    print(f"tau_act IQR                      : {v['tau_act_iqr']:.3f}")
    print()
    print(f"boundary RHS (Delta-/Delta+)     : {v['boundary_rhs']:.2f}")
    print(f"threshold RISES with stake       : "
          f"{v['frac_threshold_rises_with_stake']:.1%} of incidents")
    print(f"threshold FALLS with stake       : "
          f"{v['frac_threshold_falls_with_stake']:.1%} of incidents")
    print(f"minority side                    : "
          f"{v['minority_side_fraction']:.1%}"
          f"        (need >= {MIN_MINORITY_FRACTION:.0%})")
    print("=" * 64)

    if v["PASS"]:
        print("VERDICT: PASS -- population straddles the boundary.")
        print("  A fixed threshold errs in both directions here.")
        print("  Proceed to RQ2-RQ4. Keep the main wording in main.tex.")
    else:
        print("VERDICT: REFUTED -- the central hypothesis does not hold here.")
        print("  Report this in full. Switch main.tex to the negative-result")
        print("  wording: search for `IF RQ1 IS REFUTED`.")
        print("  This remains publishable: the sufficiency of a fixed")
        print("  threshold is assumed throughout the literature and, to our")
        print("  knowledge, has never been tested.")
    print("=" * 64 + "\n")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", choices=["rcaeval", "rca100"], required=True)
    ap.add_argument("--root", required=True, help="dataset directory")
    args = ap.parse_args()

    loader = {"rcaeval": load_rcaeval, "rca100": load_rca100}[args.dataset]
    rho, D, T_e = loader(args.root)      # raises NotImplementedError until Day 1

    sanity_check(rho, D, T_e)
    report(verdict(rho, D, CostParams()))


if __name__ == "__main__":
    main()
