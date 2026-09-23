# The problem statement: risk-adjusted abstention for AI-assisted RCA in Kubernetes

*Research journal entry — 2026-09-20. Part of the [risk-adjusted abstention](../README.md) study.*

---

> **Summary:** The narrowed research brief written out in full — one sentence, one paragraph, then the formal version with notation, four research questions, explicit scope boundaries, five claimed contributions and the evaluation protocol that would confirm or kill each one. Built on the novelty scan in [2026-09-20_problem-statement-market-validation](2026-09-20_problem-statement-market-validation.md).

---

> [!NOTE]
> **What this code/concept does**
> A problem statement is the contract a research paper signs with its reader. It says: here is a situation, here is what nobody has worked out about it, here is exactly what I will work out, and here is how you will know whether I succeeded or failed.
>
> This particular statement is about an AI that diagnoses failures in Kubernetes — the system that runs containerised software across many machines. When something breaks, the AI reads the metrics and logs and proposes a cause. Modern systems attach a confidence number to that proposal and use a cut-off: above the cut-off the AI acts on its own, below it a human is paged.
>
> The statement's claim is that the cut-off is the wrong shape. It is one fixed number applied to every incident, and incidents are not alike. Getting it wrong on a broken internal dashboard costs almost nothing. Getting it wrong on the payment system during a sale costs a fortune. So the cut-off should be computed per incident from what that incident is actually worth, not chosen once by hand.

> [!NOTE]
> **Why we are doing it this way**
> Three design choices shape the statement, and each one is a defence against a specific way papers get rejected.
>
> **One claim, not three.** The original brief carried cost-aware prioritization *and* confidence gating *and* a Kubernetes framework. Reviewers reject papers whose only claim is "we combined A and B", and a postgraduate paper carrying three contributions does each of them shallowly. Prioritization was demoted from a contribution to an input signal. It still appears — it is what tells the gate what the stakes are — but it is not something the paper claims credit for inventing.
>
> **Stakes are estimated from telemetry, never from business labels.** No public incident dataset records what an outage cost in money. If the paper needs that number and invents it, every result downstream is invented too. So the stake estimator is built only from quantities a cluster actually emits — replica-seconds, request rate, measured error-budget burn — multiplied by published cloud unit prices. This turns the biggest reviewer attack surface into a measurable component that can be ablated.
>
> **The falsification condition is stated up front.** The paper says in advance what result would prove it wrong: if incident stakes in the benchmark turn out to be near-uniform, the derived threshold collapses to the fixed baseline and there is no paper. Saying this first is what separates a hypothesis from a sales pitch, and it is the same instinct as the falsification stage in *agentic-cinema*.

> [!NOTE]
> **How it works step by step**
> **1. Fix the setting.** A Kubernetes cluster running microservices. Several incidents are open at once. An LLM-based RCA agent observes telemetry and proposes a root cause for each, with a confidence score attached.
>
> **2. Widen the action space from two to three.** Existing gates choose between *answer* and *abstain*. This is too coarse. The real choice is: **act** (remediate autonomously), **assist** (hand the hypothesis to a human as a starting point), or **escalate** (page a human with no hypothesis at all, so a wrong guess cannot anchor them). Three actions matter because the right move on a high-stakes incident is usually *assist faster, act less* — a distinction a two-way gate cannot express.
>
> **3. Write the loss.** For each incident, name what each wrong choice costs: acting on a wrong hypothesis extends time-to-resolution and burns more error budget, and may make things worse; escalating costs engineer-hours plus the burn that accrues while the human reads in; and the agent's own token spend is a real cost that belongs in the same equation. Every term must have a unit and a source.
>
> **4. Derive the threshold rather than choosing it.** Acting is worthwhile only when expected confidence clears the point where the expected cost of acting falls below the expected cost of escalating. That point is a ratio of the incident's own quantities, so it moves per incident. On a cheap incident the escalation cost dominates and the threshold drops — the agent should be bolder. On an expensive one the cost of a wrong action dominates and the threshold rises toward certainty.
>
> **5. Estimate the stakes without business labels.** Derive them from telemetry: error-budget burn rate against the service's SLO, replica-seconds and request volume priced at published cloud rates, and dependency fan-out as a blast-radius proxy.
>
> **6. Evaluate against an oracle, not against accuracy.** The baseline is the best possible *fixed* threshold, tuned with hindsight on the test set — a deliberately generous opponent. The measure is cost-weighted regret against a perfect-information oracle, plus risk-coverage curves stratified by stake decile, plus calibration error. Accuracy alone would hide the entire effect.
>
> **7. Ablate the cost model.** Re-run everything across a wide sweep of assumptions about the cost terms. If the conclusion survives, the arbitrary-numbers objection is answered. If it does not, that is the paper's most honest finding.

> [!NOTE]
> **Key terms defined**
> - **Problem statement** — the part of a paper that names the gap and commits to what will be done about it, in terms specific enough to be graded.
> - **Selective prediction** — a model allowed to decline to answer. Trades coverage (how often it answers) for accuracy (how often it is right when it does).
> - **Risk-sensitive** — the loss depends not just on whether you were wrong but on how expensive being wrong was in that particular case.
> - **Abstention threshold** — the confidence level above which the model is permitted to answer or act.
> - **Regret** — the gap between what your policy cost and what a perfect-knowledge policy would have cost. Lower is better; zero is an oracle.
> - **Coverage** — the fraction of cases the model chooses to answer rather than defer.
> - **Risk-coverage curve** — error rate plotted against coverage. The standard picture for showing a deferral mechanism works.
> - **ECE (Expected Calibration Error)** — how far stated confidence drifts from real accuracy.
> - **Error-budget burn rate** — how fast an incident is consuming the failure allowance implied by the SLO.
> - **Blast radius** — how many downstream services a failure can reach. Proxied by dependency fan-out.
> - **Ablation** — removing or varying one component to show how much of the result depended on it.
> - **Oracle baseline** — an upper bound using information the real system could not have had. Nobody beats it; the point is how close you get.

> [!WARNING]
> **Common mistakes to avoid**
> - **Letting prioritization creep back into being a contribution.** It is an input. The moment the paper starts claiming a novel ranking algorithm, it is two papers again and both get thinner.
> - **Comparing against a weak baseline.** Beating an untuned threshold proves nothing. The opponent must be the best fixed threshold tuned with hindsight on the test set. If the method cannot beat that, it has no result.
> - **Reporting accuracy.** The whole claim is about *which* errors happen, not how many. An accuracy table makes the contribution invisible.
> - **Skipping the sensitivity sweep.** Without it, a reviewer needs one sentence — "the cost numbers are made up" — to end the paper.
> - **Hiding the failure condition.** State up front that near-uniform stakes would collapse the method into the baseline. A reviewer who finds that themselves treats it as a flaw; a reviewer who is told it treats it as rigour.
> - **Describing an implementation instead of a problem.** "We build a system that…" is an architecture. "Existing work assumes X, which is false when Y, and the consequence is Z" is a problem.

> [!TIP]
> **How this connects to the bigger picture**
> The statement is the hinge between the novelty scan and the actual work. The scan established that two thirds of the original brief was already published and that one gap was open; this document spends that finding by turning the surviving gap into something with research questions, boundaries and a falsification condition — the point at which a topic becomes a paper.
>
> It also closes a loop with *agentic-cinema*, where an agent must disprove its own hypotheses before it is allowed to report, and whose S4 decoy scenario has "page nobody" as the correct answer. That decoy is an abstention test case that already exists and already runs. The broader thread across both is the same: the interesting engineering problem in agentic operations is no longer making the machine capable, it is making its silence principled.

> [!IMPORTANT]
> **Portfolio note**
> Demonstrates the ability to convert a broad, fashionable brief into a falsifiable research contract — action space, loss function, research questions, scope boundaries, generous baseline and a stated condition under which the whole thesis fails — which is the skill that distinguishes a researcher from someone with an interesting idea.

---

## The statement

### One sentence

Confidence-gated AI root cause analysis uses a single fixed threshold to decide when the machine may act, but incident stakes in production Kubernetes vary by orders of magnitude, so this work derives the abstention threshold per incident from its measured error-budget burn and cost exposure and shows that doing so reduces cost-weighted error regret against the best hindsight-tuned fixed threshold.

### One paragraph

Kubernetes operations teams increasingly delegate incident diagnosis to LLM-based agents, and the mechanism that makes this safe is a confidence gate: the agent proposes a root cause with a confidence score, and a threshold decides whether it acts autonomously or hands over to a human. Prior work has concentrated on making that confidence score well calibrated and has treated the threshold itself as a fixed hyperparameter, uniform across incidents. This assumption is false in production. The cost of an incorrect autonomous action on a low-traffic internal service and on a revenue-critical payment path differ by orders of magnitude, so a single threshold is simultaneously too conservative on cheap incidents and unsafe on expensive ones. This work reframes RCA autonomy as risk-sensitive selective prediction over a three-way action space — act, assist, escalate — derives the per-incident threshold from a loss function over error-budget burn, infrastructure and revenue exposure, engineer time and inference cost, and estimates every stake term from cluster telemetry rather than unavailable business-cost labels. The evaluation, on public microservice RCA benchmarks, measures cost-weighted regret against a perfect-information oracle and against the strongest hindsight-tuned fixed threshold, with a sensitivity sweep over the cost model.

### Formal version

**Setting.** A Kubernetes cluster of microservices under an SLO regime. At time *t* a set of concurrent incidents is open. An LLM-based RCA agent observes telemetry per incident and emits a root-cause hypothesis with a confidence score.

**Action space.** For each incident the system chooses one of three actions:

| Action | Meaning | Dominant risk |
|---|---|---|
| **Act** | Apply the remediation implied by the hypothesis, autonomously | A wrong hypothesis extends MTTR and may worsen the fault |
| **Assist** | Hand the hypothesis to an on-call engineer as a starting point | A wrong hypothesis anchors the human and misdirects the search |
| **Escalate** | Page a human with evidence but no hypothesis | Full human latency; the budget burns while they read in |

**Stake vector per incident**, all telemetry-derived: error-budget burn rate against the service SLO; infrastructure cost rate as replica-seconds at published cloud unit prices; request-volume exposure as a revenue proxy; dependency fan-out as blast radius; and the agent's own cumulative inference cost for this investigation.

**Loss.** Each (action, correctness) pair carries a cost expressed in the stake vector's units. The optimal policy acts only when confidence exceeds the point at which the expected cost of acting falls below the expected cost of escalating — a ratio of the incident's own quantities, and therefore incident-specific.

**Central hypothesis.** The optimal threshold is a monotone function of stake, not a constant. Consequently a fixed-threshold policy incurs regret that grows with the variance of stake across the incident population.

---

## Research questions

| # | Question | Decided by |
|---|---|---|
| **RQ1** | Does stake vary enough across realistic incident populations for a fixed threshold to be measurably wrong? | Distribution of the telemetry-derived stake vector across the benchmarks; variance across stake deciles |
| **RQ2** | Can stake be estimated from cluster telemetry alone, with no business-cost labels, accurately enough to order incidents correctly? | Rank correlation between the telemetry estimator and injected ground-truth severity |
| **RQ3** | Does a stake-derived threshold reduce cost-weighted error regret against the best hindsight-tuned fixed threshold, at equal or better coverage? | Regret versus oracle; risk-coverage curves stratified by stake decile |
| **RQ4** | How much of the gain survives a wrong cost model? | Sensitivity sweep over every cost term; the breakdown point at which the advantage disappears |

---

## Scope boundaries

**In scope:** the decision layer — when the agent may act, assist or escalate, and how that boundary is computed.

**Explicitly out of scope**, each with the reason:

- **A new RCA algorithm.** The agent is held fixed and treated as a black box emitting a hypothesis and a confidence. Changing it would confound the result.
- **A new calibration method.** PACE-LM and successors own this ground. Calibration is consumed, not contributed.
- **Autoscaling and resource allocation.** Well covered by existing SLO- and cost-aware control work. This paper is about triage, not provisioning.
- **Executing remediation.** Actions are scored under the loss, not performed against a live cluster. Safety and reproducibility both require this.
- **Multi-cluster and multi-tenant settings.** Single-cluster only; the generalisation is future work.

---

## Claimed contributions

1. **A formalisation** of RCA autonomy as risk-sensitive selective prediction over a three-way action space, replacing the binary answer/abstain framing used by prior work.
2. **A telemetry-only stake estimator** that scores incident cost and error-budget exposure without business-cost labels, making the method runnable on any instrumented cluster and on public benchmarks that carry no cost annotations.
3. **A derived per-incident threshold** with its dependence on stake made explicit, in place of a hand-tuned constant.
4. **An evaluation protocol** — cost-weighted regret against a perfect-information oracle, and risk-coverage curves stratified by stake decile — that makes the effect visible where accuracy metrics conceal it.
5. **A sensitivity analysis** establishing how wrong the cost model can be before the advantage disappears.

---

## Evaluation plan

**Benchmarks.** RCAEval, Cloud-OpsBench, AIOps2025 / RCA100, on Sock Shop, Train Ticket and the OpenTelemetry Demo. No testbed is built.

**Baselines,** in increasing order of difficulty:
1. Always act (no gate).
2. Always escalate (no autonomy).
3. Fixed threshold at a conventional value.
4. **Fixed threshold tuned with hindsight on the test set** — the real opponent, deliberately given an unfair advantage.
5. Perfect-information oracle — the upper bound.

**Primary metric:** cost-weighted regret against the oracle.
**Secondary:** coverage at matched regret; ECE of the underlying confidence signal; stake-stratified risk-coverage curves; total inference cost per incident.

**Falsification condition, stated in advance:** if the stake distribution across the benchmarks proves near-uniform, the derived threshold collapses to the fixed baseline and the central hypothesis is refuted. RQ1 is therefore run first and is a genuine gate on the rest of the work, not a formality.

---
