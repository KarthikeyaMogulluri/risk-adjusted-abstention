================================================================================
ANALYSIS CODE
Risk-Adjusted Abstention for LLM-Assisted Root Cause Analysis
================================================================================
Created: 2026-09-21

This code produces Section 6 of the paper. It does not contain Section 6.
Run it on real benchmark data and the numbers appear; until then Section 6
stays empty, because a results section written before the experiments is
fabricated data, not a draft.


--------------------------------------------------------------------------------
FILES
--------------------------------------------------------------------------------

  policy.py     Section 3, executable. Both thresholds (Prop 1), the sign-flip
                test (Prop 2), the three-way policy, the fixed-threshold
                baseline. SELF-TESTING - see below.

  stakes.py     Section 4, executable. Telemetry -> stake. OpenCost infra
                rate, failed-request rate, SRE-workbook burn rate, collateral
                damage from blast radius. Dataset loaders are NOT implemented;
                see DAY 1 below.

  evaluate.py   Section 5, executable. Realised costs (Eqs 4-6), the
                perfect-information oracle, all five baselines including the
                hindsight-tuned constant, cost-weighted regret, risk-coverage
                curves, ECE, stake-decile stratification.

  run_rq1.py    The gating test. Run FIRST. Prints PASS or REFUTED against a
                pre-registered decision rule.

Dependencies: numpy only, so far. matplotlib is needed for Day 4 figures.


--------------------------------------------------------------------------------
THE SELF-TEST - run this before trusting anything
--------------------------------------------------------------------------------

    python policy.py

It verifies the paper's analytic claims numerically:

  - Proposition 1: both thresholds stay in [0,1] across 11 decades of input
  - Proposition 2: the ANALYTIC sign of d(tau_act)/d(rho) is checked against
    a central finite difference at 20,000 random points spanning 7 decades of
    stake and 8 of damage

If Proposition 2 were wrong, this catches it here rather than in review. It
currently passes. Both regimes occur in the test range (about 68% rising,
32% falling), so the test is not vacuous.

    python evaluate.py --demo

Exercises the full harness on SYNTHETIC stakes. The numbers it prints are
NOT results and must never enter the paper. The banner says so at runtime.


--------------------------------------------------------------------------------
FINDING FROM RUNNING THE CODE - needs a decision before Day 2
--------------------------------------------------------------------------------

The ordering tau_assist <= tau_act is violated on roughly 35-39% of points
across the synthetic parameter ranges.

Where it is violated, ASSIST IS DOMINATED and the three-way policy collapses
to two actions - which undercuts one of the paper's stated contributions.

This is very likely an artefact of sampling stake and damage independently
across their full ranges, which produces combinations that cannot occur in a
real cluster (a near-zero-stake service with enormous blast radius). On real
data the two are correlated and the violation rate should fall sharply.

BUT THAT IS A HYPOTHESIS, NOT AN ANSWER. Three acceptable outcomes:

  1. Violation rate is low on real data
     -> report it as a diagnostic, nothing changes.

  2. Violation rate is high on real data
     -> Section 3.6 must explain the degeneracy honestly, and contribution 1
        weakens from "three actions" to "three actions where they are
        distinguishable".

  3. The parameter defaults are wrong
     -> eta_plus / eta_minus in CostParams are the least anchored numbers in
        the model. Check them first.

Measure it on real data before writing a word about it. Do not tune the
parameters until the violation rate looks acceptable - that is fitting the
model to the conclusion.


--------------------------------------------------------------------------------
DAY 1 - what has to be implemented
--------------------------------------------------------------------------------

Two loaders in stakes.py, both currently raising NotImplementedError:

    load_rcaeval(root)
    load_rca100(root)

They are deliberately unimplemented. The on-disk layout of these datasets has
not been verified, and guessing it produces code that silently returns
plausible-looking nonsense - the worst possible failure mode in research code.

Before implementing, confirm each dataset supplies:

  [ ] per-service metric time series (CPU, memory, request rate, error rate,
      latency percentiles)
  [ ] replica or pod count over time
  [ ] service dependency graph or call graph
  [ ] ground-truth fault label (service, fault type, injection time)

If replica counts are absent, proxy infra cost from CPU and memory requests
AND RECORD THE SUBSTITUTION in Section 5.2 of the paper. A silent substitution
is a construct-validity failure.

Also set node_usd_per_hour in StakeParams to match the dataset's actual node
type. It is currently a placeholder.


--------------------------------------------------------------------------------
ORDER OF WORK
--------------------------------------------------------------------------------

  1. python policy.py                    verify the maths       DONE, passes
  2. implement the two loaders           Day 1
  3. python run_rq1.py --dataset ...     Day 2, the gate
  4. if PASS: RQ2, RQ3, RQ4              Days 3-4
     if REFUTED: switch main.tex to the negative wording and write that paper
  5. figures                             Day 4
================================================================================
