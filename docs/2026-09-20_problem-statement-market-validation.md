# Market and novelty validation: cost- and SLO-aware incident prioritization with confidence-gated AI RCA in Kubernetes

*Research journal entry — 2026-09-20. Part of the [risk-adjusted abstention](../README.md) study.*

---

> **Summary:** A proposed postgraduate research topic was checked against the September 2026 literature and industry landscape. Verdict: the *problem* is real and commercially hot, but the topic as written is three separate papers stapled together, and one of the three (confidence estimation for LLM root cause analysis) was already solved in 2023-24. The defensible contribution is narrower and sharper: make the AI's decision to act or escalate depend on what the incident is worth.

---

> [!NOTE]
> **What this code/concept does**
> The proposed research asks a computer system to do two jobs during a production outage.
>
> **Job one — prioritization.** When twenty alerts fire at once, decide which one a human should look at first. Today most systems rank by severity or by how loud the alert is. The proposal says rank by two better things instead: how much money the incident is burning (cloud spend, lost revenue) and how much of the "error budget" it is eating. An error budget is a pre-agreed allowance of failure — if you promise 99.9% uptime, the 0.1% is the budget, and every incident spends some of it.
>
> **Job two — confidence-gated diagnosis.** An AI reads the logs and metrics and proposes a root cause. But instead of always answering, it is allowed to say "I am not sure enough — a human should take this." The gate is the rule that decides when it answers and when it stays quiet.
>
> Kubernetes is the setting: the software that runs containers across many machines, where these failures actually happen.

> [!NOTE]
> **Why we are doing it this way**
> The topic was evaluated rather than accepted because of a lesson already learned on the quantum decoder project: a novelty scan killed a first research plan *after* work had started, because the idea was already published. Doing the scan first is cheaper than doing it late.
>
> The scan found that the three ingredients have very different novelty values:
>
> - **Confidence estimation for LLM root cause analysis is already done.** Microsoft published PACE-LM / LM-PACE in 2023-24, which produces calibrated confidence scores for cloud incident root causes and cuts calibration error to roughly a third of naive prompting. Proposing "add confidence scores to RCA" in 2026 is proposing a 2023 paper.
> - **SLO-aware and cost-aware control is a crowded field, but on the wrong side of the problem.** The existing work applies cost and SLO awareness to *autoscaling* — how many replicas to run — not to *incident triage*. That is a genuine gap.
> - **The combination itself is not a contribution.** Reviewers reject papers whose only claim is "we joined A and B". The claim has to be that joining them reveals something neither one shows alone.
>
> So the recommendation is to keep the domain and throw away two thirds of the scope, keeping the one part that is both unpublished and intellectually interesting: the gate threshold should not be a fixed number.

> [!NOTE]
> **How it works step by step**
> **1. Restate the problem as a decision under uncertainty.** An AI facing an incident has three choices: act autonomously, hand over to a human with its findings, or abstain entirely. Each choice has a cost if it is wrong.
>
> **2. Notice that existing work uses one fixed threshold.** Today's systems say something like "if confidence is above 0.8, answer; otherwise abstain." That single number is applied to every incident equally.
>
> **3. Observe why that is wrong.** Being wrong about a stale cache on an internal dashboard costs almost nothing. Being wrong about the payment service during a sale costs a great deal. The same 0.8 confidence means two completely different risks. A fixed threshold is therefore too cautious on cheap incidents and far too reckless on expensive ones.
>
> **4. Derive the threshold instead of picking it.** Write a loss function containing the things that actually cost money: error-budget burn rate, cloud spend, engineer time pulled away from other work, and the AI's own inference cost in tokens. The optimal abstention threshold falls out of that loss function, and it is different for every incident.
>
> **5. Feed prioritization in as a signal, not as a second contribution.** The cost and SLO ranking becomes the input that sets the stakes for the gate. It stops being a separate paper and becomes a component of one paper.
>
> **6. Evaluate on existing public benchmarks.** RCAEval, the AIOps2025 and RCA100 datasets, and Cloud-OpsBench already provide labelled microservice failures on systems like Sock Shop, Train Ticket and the OpenTelemetry Demo. None of them label cost, so a cost model has to be derived from measurable proxies — replica-seconds consumed, request volume multiplied by published cloud unit prices — and then stress-tested with a sensitivity analysis.
>
> **7. Report the right numbers.** Not accuracy alone. Expected calibration error, risk-coverage curves, and cost-of-errors avoided versus a fixed-threshold baseline.

> [!NOTE]
> **Key terms defined**
> - **SLO (Service Level Objective)** — a promise about how well a service behaves, for example "99.9% of requests succeed". The measurable target a team commits to.
> - **Error budget** — the allowed amount of failure implied by an SLO. At 99.9%, the budget is 0.1% of requests. Incidents spend it.
> - **RCA (Root Cause Analysis)** — working out what actually broke, as opposed to what merely looks broken downstream.
> - **AIOps** — using machine learning and AI to run IT operations: detecting anomalies, grouping alerts, diagnosing causes.
> - **FinOps** — the practice of treating cloud spend as an engineering concern rather than a finance report that arrives too late.
> - **Kubernetes** — the orchestrator that schedules containers across a fleet of machines and restarts them when they fail.
> - **Calibration** — whether a stated confidence is honest. If a model says "80% sure" a thousand times, it should be right about 800 times. If it is right 400 times it is badly calibrated.
> - **ECE (Expected Calibration Error)** — a single number measuring how far stated confidence drifts from actual accuracy. Lower is better.
> - **Abstention / selective prediction** — letting a model decline to answer when unsure, trading coverage for accuracy.
> - **Risk-coverage curve** — a graph showing how error rate falls as the model is allowed to answer fewer cases. The standard way to show an abstention mechanism works.
> - **MTTR (Mean Time To Resolution)** — average time from an incident starting to it being fixed. The headline SRE metric.
> - **Novelty scan** — searching the literature for prior art *before* committing to a research plan, not after.

> [!WARNING]
> **Common mistakes to avoid**
> - **Proposing a combination as the contribution.** "We combined cost awareness with confidence gating" is not a finding. "A fixed abstention threshold is provably wrong when incident stakes vary by orders of magnitude, and here is the threshold that is right" is a finding.
> - **Reinventing PACE-LM.** Any proposal built around "calibrated confidence for cloud RCA" as its main novelty is three years late. Cite it and build past it.
> - **Inventing a cost model with no defence.** This is the single biggest reviewer attack surface. No public incident dataset carries a business-cost label, so the cost numbers will be constructed. If they are constructed arbitrarily, every downstream result is arbitrary too. Derive them from observable quantities and publish a sensitivity analysis showing the conclusions hold across a wide range of assumptions.
> - **Keeping all three components.** A postgraduate paper carrying prioritization plus gating plus a Kubernetes framework will do all three shallowly and be rejected for lack of depth in any.
> - **Trusting LLM self-reported confidence.** Models are known to be confidently wrong, and 2026 work documents systematic reasoning failures in exactly this task. The gate is only as good as the confidence signal feeding it.
> - **Ignoring the clock.** This subfield publishes fast. An idea that is novel today may be published by someone else within two quarters. Re-run the novelty scan before writing, and again before submitting.

> [!TIP]
> **How this connects to the bigger picture**
> This sits directly on top of the Agentic Cinema control-room work, where a six-stage agent diagnoses streaming outages and is required to disprove its own hypotheses before reporting. Falsification-before-reporting and confidence-gated abstention are the same instinct — do not let the machine speak until it has earned the right. That project already has a working telemetry pipeline, synthetic scenario generation, a scoring harness and a decoy scenario whose correct answer is to page nobody. That decoy is, in effect, an abstention test case that already exists.
>
> Wider still: the blocker on agentic operations in 2026 is not capability, it is trust. Teams will not let an AI touch production until it can be relied on to know when to stop. Any research that makes the stop-condition principled rather than hand-tuned is aimed at the actual bottleneck.

> [!IMPORTANT]
> **Portfolio note**
> Demonstrates the ability to take a broad, fashionable research brief and subject it to a prior-art scan that rejects two thirds of it — arriving at a narrower claim that is both unpublished and defensible, which is the difference between a topic and a paper.

---

## Findings table

| Component | Prior art status | Verdict |
|---|---|---|
| Confidence estimation for LLM RCA | PACE-LM / LM-PACE, 2023-24, plus 2026 follow-ups on reasoning failures | Solved — cite, do not claim |
| Graph-guided / auditable RCA for Kubernetes | arXiv 2606.08590 (Jun 2026) — no cost, no SLO, no abstention | Adjacent, leaves the gap open |
| SLO- and cost-aware control | Applied to autoscaling (arXiv 2512.23415) and orchestration times (ACM TOIT 2026) | Crowded, but aimed at resource allocation, not triage |
| Agentic RCA benchmarks | RCAEval, Cloud-OpsBench, AIOps2025 / RCA100 | Usable off the shelf — no testbed to build |
| Cost-aware *incident prioritization* | No direct match found | Open |
| Stakes-dependent abstention threshold | No direct match found | **The contribution** |

## Recommended narrowed title

> Risk-Adjusted Abstention for LLM-Assisted Root Cause Analysis: Making the Autonomy Threshold a Function of Error-Budget and Cost Stakes in Kubernetes

---
