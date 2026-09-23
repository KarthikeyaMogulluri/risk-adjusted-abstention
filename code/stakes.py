"""
Stake estimation from telemetry -- Section 4 of the paper, executable.

    rho_i = rho_infra_i + lambda_exp * r_fail_i + lambda_slo * b_i     Eq. (12)
    D_i   = kappa * |down(i)| * mean_stake                             Eq. (13)

Every term comes from something an instrumented cluster emits. No term
requires a business-cost label. That is what makes the method evaluable on
public benchmarks and deployable without financial instrumentation.

DAY 1 WORK IS MARKED `TODO(day1)`. The dataset loaders are deliberately
unimplemented: the exact on-disk layout of RCAEval and RCA100 has not been
verified, and guessing it here would produce code that silently returns
plausible-looking nonsense. Implement against the real files.
"""

from __future__ import annotations

from dataclasses import dataclass
import numpy as np


# ---------------------------------------------------------------------------
# Exchange rates: the three constants telemetry cannot supply.
# Declared here, swept in Section 5.5. Never silently fixed.
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class StakeParams:
    lambda_exp: float = 0.01      # USD per failed request
    lambda_slo: float = 1000.0    # USD per unit error-budget fraction
    kappa: float = 60.0           # extra outage seconds per downstream service

    # Uniform SLO -- Section 4.1. Identical for EVERY service, deliberately.
    # All variance in burn rate then originates in the measured data and none
    # in our choices. This is the stake model's principal neutrality defence
    # and is non-negotiable.
    slo_availability: float = 0.999
    slo_latency_ms: float = 500.0

    # Node pricing for the OpenCost formula. Published on-demand rate.
    node_usd_per_hour: float = 0.192      # TODO(day1): match dataset's node type
    pods_per_node: float = 16.0


# ---------------------------------------------------------------------------
# Components of Eq. (12)
# ---------------------------------------------------------------------------

def infra_rate(replica_count: np.ndarray, sp: StakeParams) -> np.ndarray:
    """rho_infra, USD/s. OpenCost model: replica-seconds x unit price.

    Already denominated in currency -- needs no exchange rate. This is the one
    stake component with no free parameter, which is why it anchors the others.
    """
    usd_per_pod_second = sp.node_usd_per_hour / sp.pods_per_node / 3600.0
    return replica_count * usd_per_pod_second


def failed_request_rate(requests_total: np.ndarray, errors_total: np.ndarray,
                        latency_p99_ms: np.ndarray,
                        sp: StakeParams) -> np.ndarray:
    """r_fail, req/s. Error responses PLUS latency-objective violations.

    Counting slow-but-successful requests as failures is what makes the SLO a
    latency SLO and not merely an availability one.
    """
    slow = requests_total * (latency_p99_ms > sp.slo_latency_ms)
    return errors_total + slow


def burn_rate(requests_total: np.ndarray, failed: np.ndarray,
              sp: StakeParams) -> np.ndarray:
    """b, budget-fraction per second. Standard multi-window burn rate.

    Sloth / SRE-workbook formulation: observed error ratio divided by the
    error budget (1 - SLO target).
    """
    with np.errstate(divide="ignore", invalid="ignore"):
        ratio = np.where(requests_total > 0, failed / requests_total, 0.0)
    return ratio / (1.0 - sp.slo_availability)


def compose_stake(rho_infra, r_fail, b, sp: StakeParams) -> np.ndarray:
    """Eq. (12)."""
    return rho_infra + sp.lambda_exp * r_fail + sp.lambda_slo * b


def collateral_damage(downstream_count: np.ndarray, rho: np.ndarray,
                      sp: StakeParams) -> np.ndarray:
    """Eq. (13). A LEVEL, not a rate -- it does not scale with duration.

    That asymmetry against rho, which does scale with duration, is precisely
    what produces the sign flip in Proposition 2.
    """
    return sp.kappa * downstream_count * float(np.mean(rho))


# ---------------------------------------------------------------------------
# Dataset loaders -- Day 1
# ---------------------------------------------------------------------------

REQUIRED_FIELDS = (
    "per-service metric time series (CPU, memory, request rate, error rate, "
    "latency percentiles)",
    "replica or pod count over time",
    "service dependency graph / call graph",
    "ground-truth fault label (service, fault type, injection time)",
)


def load_rcaeval(suite: str = "RE1", systems=("ob", "ss")):
    """IMPLEMENTED 2026-09-21. See rcaeval_loader.py for the schema facts.

    Field verification result:
      [x] per-service metric series  -- cpu, mem, throughput, latency present
      [ ] replica / pod counts       -- ABSENT. Proxied from CPU + memory.
      [ ] call graph                 -- ABSENT in RE1 (0% traces). Static
                                        topology used instead; see topology.py
      [x] ground-truth fault label   -- root_cause_service, fault, inject_time

    Two substitutions were forced and BOTH are recorded in Section 5.2.
    """
    from rcaeval_loader import build_dataset
    rho, D, T_e, _df = build_dataset(suite, tuple(systems))
    return rho, D, T_e


def load_rca100(root: str):
    """TODO(day2): RCA100 / AIOps2025, the second independent population."""
    raise NotImplementedError(
        "Day 2. RCAEval is loading; RCA100 is the second dataset required by "
        "Section 5.2 (one dataset is an artefact, two is a finding)."
    )


def sanity_check(rho: np.ndarray, D: np.ndarray, T_e: np.ndarray) -> None:
    """Run on every real dataset before any analysis. Cheap, catches a lot."""
    assert np.all(np.isfinite(rho)), "non-finite stake"
    assert np.all(rho >= 0), "negative stake"
    assert np.all(np.isfinite(D)) and np.all(D >= 0), "bad damage"
    assert np.all(T_e > 0), "non-positive resolution time"
    spread = np.log10(rho.max() / max(rho.min(), 1e-12))
    print(f"  stake spans {spread:.1f} decades  "
          f"[{rho.min():.3e}, {rho.max():.3e}] USD/s")
    if spread < 1.0:
        print("  WARNING: under one decade of stake variance.")
        print("  This is evidence AGAINST the paper's premise. See RQ1.")
