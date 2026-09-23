"""
Thresholds and the three-way policy.

This module is the executable form of Section 3 of the paper. Every formula
here has a numbered equation in main.tex and the names match the notation.

    tau_act      Eq. (7),  Proposition 1
    tau_assist   Eq. (8),  Proposition 1
    sign_flip    Eq. (10), Proposition 2

The self-test at the bottom VERIFIES PROPOSITION 2 NUMERICALLY. Run it before
trusting anything downstream -- if the derivative in the paper is wrong, this
is where it gets caught, and it is far cheaper to catch it here than in review.

    python policy.py
"""

from __future__ import annotations

from dataclasses import dataclass
import numpy as np


# ---------------------------------------------------------------------------
# Parameters that are NOT measurable from telemetry. Every one of these is
# swept in Section 5.5. Defaults are anchors, not findings -- no result may
# depend on a single setting of them.
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CostParams:
    # Automation asymmetry: seconds lost when wrong vs saved when right.
    # Anchored on the published finding that mis-triage can cause up to 10x
    # delay in mitigation.
    delta_plus_act: float = 300.0      # Delta^+  seconds saved by correct act
    delta_minus_act: float = 1800.0    # Delta^-  seconds lost by wrong act

    # Anchoring asymmetry for assist. delta_minus_assist > 0 encodes
    # Assumption 1: a wrong hypothesis is worse than no hypothesis.
    # NOTE: this is the paper's most contestable assumption. The sweep MUST
    # include values <= 0 so the conclusion does not depend on it.
    delta_plus_assist: float = 240.0
    delta_minus_assist: float = 420.0

    # Engineer-seconds. H_e is the escalate branch; eta are the deltas.
    H_e: float = 2700.0                # 45 min of engineer time
    eta_plus: float = 900.0            # saved when the hypothesis is right
    eta_minus: float = 600.0           # wasted when it is wrong

    # Engineer cost rate (USD/s). Eliminated by normalisation (Sec 4.3) but
    # kept explicit so the code matches the paper's equations literally.
    w: float = 60.0 / 3600.0           # USD 60/hr

    @property
    def wHe(self) -> float:
        return self.w * self.H_e


# ---------------------------------------------------------------------------
# Proposition 1 -- the two thresholds
# ---------------------------------------------------------------------------

def tau_act(rho: np.ndarray, D: np.ndarray, p: CostParams) -> np.ndarray:
    """Eq. (7). Confidence above which acting beats escalating.

    rho : stake, USD/s, per incident
    D   : collateral damage of a wrong autonomous action, USD, per incident
    """
    num = rho * p.delta_minus_act + D
    den = rho * (p.delta_plus_act + p.delta_minus_act) + p.wHe + D
    return num / den


def tau_assist(rho: np.ndarray, p: CostParams) -> np.ndarray:
    """Eq. (8). Confidence above which assisting beats escalating.

    No D term: a human reviews the hypothesis before anything changes, so
    assisting causes no collateral damage. This is why assist sits below act.
    """
    num = rho * p.delta_minus_assist + p.w * p.eta_minus
    den = (rho * (p.delta_plus_assist + p.delta_minus_assist)
           + p.w * (p.eta_plus + p.eta_minus))
    return num / den


# ---------------------------------------------------------------------------
# Proposition 2 -- the sign flip
# ---------------------------------------------------------------------------

def dtau_dstake_sign(D: np.ndarray, p: CostParams) -> np.ndarray:
    """Sign of d(tau_act)/d(rho). Eq. (10).

    Positive  ->  higher stake demands higher confidence (the intuitive case)
    Negative  ->  higher stake demands LOWER confidence, because waiting for a
                  human costs more than a wrong action

    Note this depends on D but NOT on rho -- every rho term cancels in the
    derivative. That is the whole content of Proposition 2.
    """
    return np.sign(p.delta_minus_act * p.wHe - D * p.delta_plus_act)


def boundary_ratio(D: np.ndarray, p: CostParams) -> np.ndarray:
    """LHS of Eq. (10): D / (w * H_e). Compare against delta^-/delta^+."""
    return D / p.wHe


def automation_asymmetry(p: CostParams) -> float:
    """RHS of Eq. (10): Delta^- / Delta^+."""
    return p.delta_minus_act / p.delta_plus_act


def straddles_boundary(D: np.ndarray, p: CostParams) -> dict:
    """RQ1's gating test. Does the population span the sign-flip boundary?

    Returns the fraction on each side. The paper's hypothesis needs mass on
    BOTH -- a population entirely on one side is refutation (Sec 1,
    pre-registered falsification condition).
    """
    signs = dtau_dstake_sign(D, p)
    n = len(signs)
    frac_rising = float(np.sum(signs > 0)) / n
    frac_falling = float(np.sum(signs < 0)) / n
    return {
        "n": n,
        "frac_threshold_rises_with_stake": frac_rising,
        "frac_threshold_falls_with_stake": frac_falling,
        "straddles": bool(frac_rising > 0.0 and frac_falling > 0.0),
        "minority_side_fraction": float(min(frac_rising, frac_falling)),
        "boundary_rhs": automation_asymmetry(p),
    }


# ---------------------------------------------------------------------------
# The policy
# ---------------------------------------------------------------------------

ACT, ASSIST, ESCALATE = 0, 1, 2
ACTION_NAMES = {ACT: "act", ASSIST: "assist", ESCALATE: "escalate"}


def derived_policy(q: np.ndarray, rho: np.ndarray, D: np.ndarray,
                   p: CostParams) -> tuple[np.ndarray, dict]:
    """Eq. (11). Returns (actions, diagnostics).

    Diagnostics reports the fraction of incidents where tau_assist > tau_act.
    That ordering is NOT guaranteed (Sec 3.6). Where it fails, assist is
    dominated and the policy degenerates to two actions. The paper commits to
    reporting this number rather than suppressing it.
    """
    ta = tau_act(rho, D, p)
    ts = tau_assist(rho, p)

    violations = ts > ta
    actions = np.full(len(q), ESCALATE, dtype=int)
    actions[q >= ts] = ASSIST
    actions[q >= ta] = ACT

    diagnostics = {
        "ordering_violation_fraction": float(np.mean(violations)),
        "tau_act_mean": float(np.mean(ta)),
        "tau_act_std": float(np.std(ta)),
        "tau_assist_mean": float(np.mean(ts)),
        "tau_act_range": (float(np.min(ta)), float(np.max(ta))),
    }
    return actions, diagnostics


def fixed_policy(q: np.ndarray, tau: float, rho: np.ndarray, D: np.ndarray,
                 p: CostParams) -> np.ndarray:
    """Baseline: one constant for every incident.

    The assist band is placed at the population-median tau_assist so the
    baseline is given a fair three-way policy rather than being handicapped
    into two actions. Making the baseline strong is the point.
    """
    ts_med = float(np.median(tau_assist(rho, p)))
    actions = np.full(len(q), ESCALATE, dtype=int)
    actions[q >= min(ts_med, tau)] = ASSIST
    actions[q >= tau] = ACT
    return actions


# ---------------------------------------------------------------------------
# Self-test: verify Proposition 2 numerically
# ---------------------------------------------------------------------------

def _verify_proposition_2(seed: int = 0, n: int = 20000) -> None:
    """Check the analytic sign against a finite difference of tau_act.

    If this fails, the derivative in the paper is wrong. Fix the paper.
    """
    rng = np.random.default_rng(seed)
    p = CostParams()

    rho = 10.0 ** rng.uniform(-6, 1, n)     # USD/s, 7 decades
    D = 10.0 ** rng.uniform(-3, 5, n)       # USD,   8 decades

    h = rho * 1e-6
    numeric = (tau_act(rho + h, D, p) - tau_act(rho - h, D, p)) / (2 * h)
    analytic = dtau_dstake_sign(D, p)

    # Ignore points where the numeric derivative is at float noise.
    live = np.abs(numeric) > 1e-14
    agree = np.sign(numeric[live]) == analytic[live]

    assert agree.all(), (
        f"Proposition 2 FAILS on {np.sum(~agree)}/{live.sum()} points. "
        "The derivative in main.tex Eq. (10) is wrong."
    )
    print(f"  Proposition 2 verified on {live.sum():,} points "
          f"across 7 decades of stake and 8 of damage.")

    # Both signs must actually occur, or the test proved nothing.
    assert (analytic > 0).any() and (analytic < 0).any(), \
        "Test range degenerate: only one sign present."
    print(f"  Both regimes present: "
          f"{np.mean(analytic > 0):.1%} rising, {np.mean(analytic < 0):.1%} falling.")


def _verify_thresholds_well_posed(seed: int = 1, n: int = 20000) -> None:
    """Proposition 1: both thresholds must land in [0, 1] for all inputs."""
    rng = np.random.default_rng(seed)
    p = CostParams()
    rho = 10.0 ** rng.uniform(-8, 3, n)
    D = 10.0 ** rng.uniform(-4, 6, n)

    ta, ts = tau_act(rho, D, p), tau_assist(rho, p)
    assert np.all((ta >= 0) & (ta <= 1)), "tau_act left [0,1]"
    assert np.all((ts >= 0) & (ts <= 1)), "tau_assist left [0,1]"
    print(f"  Proposition 1 verified: both thresholds in [0,1] on {n:,} points.")
    print(f"  tau_act spans [{ta.min():.3f}, {ta.max():.3f}] "
          f"-- a fixed constant cannot cover this.")


def _report_ordering(seed: int = 2, n: int = 20000) -> None:
    """How often does tau_assist > tau_act? Reported, never suppressed."""
    rng = np.random.default_rng(seed)
    p = CostParams()
    rho = 10.0 ** rng.uniform(-6, 1, n)
    D = 10.0 ** rng.uniform(-3, 5, n)
    frac = float(np.mean(tau_assist(rho, p) > tau_act(rho, D, p)))
    print(f"  Ordering tau_assist <= tau_act violated on {frac:.2%} of points.")
    if frac > 0:
        print("    -> where violated the policy degenerates to two actions;")
        print("       Section 3.6 commits to reporting this figure.")


if __name__ == "__main__":
    print("Verifying the paper's analytic claims:\n")
    _verify_thresholds_well_posed()
    _verify_proposition_2()
    _report_ordering()
    print("\nAll analytic claims hold. Safe to build the evaluation on them.")
