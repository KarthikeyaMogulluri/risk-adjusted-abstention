# The loss function page — every term, its unit, its source

*Research journal entry — 2026-09-21. Part of the [risk-adjusted abstention](../README.md) study.*

---

> **Summary:** Day 0, task 1 of the Kubernetes AIOps paper. Every cost term named, given a unit, and traced to a telemetry source or an explicitly-swept parameter. Working the algebra through produced a result stronger than the one the problem statement claimed: the threshold does not simply rise with stake — its *direction* of movement flips sign depending on the ratio of collateral damage to human-response cost. A fixed threshold is therefore wrong in both directions at once, which cannot be fixed by tuning it more conservatively.

---

> [!NOTE]
> **What this code/concept does**
> A loss function is a price list for being wrong. It says, for every choice the system can make and every way that choice can turn out, exactly what it costs.
>
> Here the system is an AI watching a Kubernetes incident. It has proposed a cause and attached a confidence number to it. It now has three choices: fix the problem itself, hand the proposal to an on-call engineer as a starting point, or wake the engineer with the evidence but no proposal at all.
>
> Each choice has a good branch and a bad branch. Fixing it yourself is fastest when you are right and worst when you are wrong, because now the real fault is still there *and* you have changed something. Handing over a wrong guess is worse than handing over nothing, because a human who is told "it's the database" will go and look at the database.
>
> This page prices all six of those branches, and then solves for the confidence level at which each choice becomes the best one. That confidence level is the threshold — and the whole paper is the claim that it is not one number.

> [!NOTE]
> **Why we are doing it this way**
> **Every term must have a unit and a source, or it is deleted.** This was the rule set on Day 0 and it is the entire defence against the biggest reviewer objection: "your cost model is arbitrary." Four terms that would have been natural to include — reputational damage, SLA penalties, customer churn, on-call fatigue — were cut for having no measurable source in any public benchmark. They are listed in §8 with reasons, because showing what was rejected is stronger evidence of discipline than showing what was kept.
>
> **Everything reduces to time, and time converts to money through a burn rate.** This is the structural choice that makes the model tractable. Rather than inventing a separate cost for each kind of failure, every outcome is described by how long the incident stays open, multiplied by what an open second costs. That collapses a sprawling model into two quantities per branch.
>
> **The unavoidable free parameters are declared, not hidden.** Converting error-budget burn into money needs an exchange rate that no dataset provides. Rather than pretending otherwise, the exchange rates are named, given symbols, and swept across orders of magnitude in the sensitivity analysis. A declared and swept parameter is defensible; a buried constant is not.
>
> **Dividing through by the engineer cost rate removes one parameter for free.** Expressing everything in engineer-second equivalents rather than dollars eliminates a term without losing any content, and it makes the remaining ratios scale-free.

> [!NOTE]
> **How it works step by step**
> **1. Name what the agent produces.** A hypothesis and a confidence number between 0 and 1. Calibration means that when it says 0.8, it is right about 80% of the time. This paper *consumes* calibration from prior work and does not try to improve it.
>
> **2. Name the three actions.** Act, assist, escalate.
>
> **3. Write the time ordering.** Acting correctly is fastest. Assisting correctly is next. Escalating with no hypothesis is the neutral middle. Assisting *wrongly* is worse than escalating, because the wrong hypothesis anchors the engineer and they spend time on the wrong thing before restarting. Acting wrongly is worst of all, because the fault is still there and the system has been changed underneath it.
>
> **4. Price an open second.** While the incident is unresolved, money burns: wasted infrastructure, failed requests, and error budget draining away. Call that rate the *stake*.
>
> **5. Price the collateral damage of a wrong autonomous action separately.** This one does not scale with time — it is a one-off harm that scales with how many downstream services the wrong action can reach.
>
> **6. Write the expected cost of each action** as confidence times the good branch plus one-minus-confidence times the bad branch.
>
> **7. Solve for where the lines cross.** The confidence at which acting becomes cheaper than escalating is the act threshold. The confidence at which assisting becomes cheaper than escalating is the assist threshold. Both come out as ratios of the incident's own quantities, so both move per incident.
>
> **8. Check which way the threshold moves as stakes rise.** This is where the surprise is, and §5 is the result.

> [!NOTE]
> **Key terms defined**
> - **Loss function** — the cost assigned to every combination of decision and outcome.
> - **Expected loss** — the average cost of a decision, weighting each outcome by how likely it is.
> - **Confidence (q)** — the agent's stated probability that its hypothesis is correct.
> - **Calibrated** — a confidence number that matches reality over many cases.
> - **Stake (ρ)** — what one second of unresolved incident costs. The composite of infrastructure waste, failed-request exposure, and error-budget burn.
> - **Collateral damage (D)** — the one-off harm from a wrong autonomous action, over and above the delay it causes.
> - **Blast radius** — how many downstream services a fault or a bad fix can reach. Counted from the call graph.
> - **Burn rate** — how fast an incident is consuming its error budget. Standard SRE quantity with a standard formula.
> - **Replica-seconds** — pods multiplied by seconds running. The unit infrastructure cost is billed in.
> - **Anchoring** — a wrong suggestion making a human slower than no suggestion, because they investigate the suggestion first.
> - **Sunk cost** — money already spent that cannot be recovered, and therefore must not influence the next decision.
> - **Exchange rate (λ)** — a declared constant converting one unit into another, here error budget and failed requests into money.
> - **Sensitivity sweep** — re-running everything across a wide range of parameter values to show the conclusion does not depend on any single guess.
> - **Well-posed** — a formula that always produces a sensible answer; here, a threshold guaranteed to land between 0 and 1.

> [!WARNING]
> **Common mistakes to avoid**
> - **Letting inference cost into the threshold.** By the time the gate runs, the tokens are already spent. Sunk costs must not change the decision. Including it would be a textbook error and a reviewer would catch it immediately. It belongs to a different decision — whether to invoke the agent at all, or whether to keep investigating — which is §7's extension, not this paper.
> - **Assuming the threshold rises with stake.** It does not always. §5 shows the direction flips, and the original problem statement's phrasing was too simple. Repeating the simple version in the paper would be stating something the paper's own maths contradicts.
> - **Hiding the exchange rates.** Two constants convert error budget and failed requests into money, and no dataset supplies them. Naming and sweeping them is the defence. Burying them in code is the failure.
> - **Forgetting to check the thresholds are ordered.** The three-action policy only makes sense if the assist threshold sits below the act threshold. This is not automatic. It must be asserted in the code and reported, and if it fails the policy degenerates to two actions — which is itself a finding worth reporting.
> - **Using dollars when ratios would do.** Dividing through by the engineer cost rate removes a parameter at no cost. Any parameter that can be eliminated should be.
> - **Inventing the time constants silently.** No benchmark records how long a human took. They must be anchored to published incident-management figures, declared as estimates, and swept.

> [!TIP]
> **How this connects to the bigger picture**
> This page turns the problem statement from a claim into something checkable. Before it, the paper asserted that the threshold should depend on stakes; after it, the dependence is written down, and it turned out to be more interesting than asserted.
>
> That is the ordinary function of doing the algebra: it either confirms the claim, kills it, or sharpens it. Here it sharpened it, and the sharpened version is the better paper — "a fixed threshold is wrong in both directions simultaneously" cannot be answered by the obvious reviewer response, which is "so just tune the threshold more conservatively."
>
> It also fixes what RQ1 must measure. The Day 2 plot is no longer the distribution of stake alone. It is the distribution of two ratios, and specifically whether a realistic incident population straddles the sign-flip boundary.

> [!IMPORTANT]
> **Portfolio note**
> Demonstrates deriving a decision rule from first principles rather than tuning one, and reporting a result that contradicted and improved the original hypothesis instead of quietly restating the hypothesis as though the maths had agreed with it.

---

# 1. Notation — every term, its unit, its source

## 1.1 Given by the agent

| Symbol | Name | Unit | Source |
|---|---|---|---|
| $q_i$ | Confidence in hypothesis for incident $i$ | dimensionless, $[0,1]$ | Agent output, calibrated per PACE-LM (arXiv 2309.05833). **Consumed, not contributed.** |
| $Y_i$ | Correctness indicator | $\{0,1\}$ | Benchmark ground-truth root-cause label |

## 1.2 Stake — what one open second costs

$$\rho_i \;=\; \rho^{\text{infra}}_i \;+\; \lambda_{\text{exp}}\, r^{\text{fail}}_i \;+\; \lambda_{\text{slo}}\, b_i$$

| Symbol | Name | Unit | Source — exactly how it is obtained |
|---|---|---|---|
| $\rho^{\text{infra}}_i$ | Infrastructure waste rate | USD/s | Replica-seconds × node hourly price ÷ pods-per-node, via the **OpenCost** (CNCF) cost model. Pod counts from `kube_pod_container_status_running`; prices from published AWS/GCP on-demand lists. |
| $r^{\text{fail}}_i$ | Failed-request rate | req/s | `rate(http_requests_total{status=~"5.."}[1m])`, plus latency-SLO violations counted as failures |
| $b_i$ | Error-budget burn rate | budget-fraction/s | **Sloth / Pyrra** standard rule: error ratio ÷ (1 − SLO target). SLO fixed **uniformly** at 99.9% availability + one latency objective across every service — so variance comes from the data, never from a per-service choice |
| $\lambda_{\text{exp}}$ | Value per failed request | USD/req | **Declared parameter. Swept.** No dataset supplies it |
| $\lambda_{\text{slo}}$ | Value per unit error budget | USD/budget-fraction | **Declared parameter. Swept.** No dataset supplies it |

## 1.3 Collateral damage — the one-off harm of a wrong autonomous action

$$D_i \;=\; \kappa \,\bigl|\mathrm{down}(i)\bigr| \,\bar{\rho}$$

| Symbol | Name | Unit | Source |
|---|---|---|---|
| $\bigl\lvert\mathrm{down}(i)\rvert$ | Blast radius — services reachable downstream of the faulty one | count | Call graph from benchmark traces |
| $\bar\rho$ | Mean stake across those downstream services | USD/s | Computed from §1.2 |
| $\kappa$ | Expected extra outage seconds caused per downstream service by a wrong action | s | **Declared parameter. Swept.** |

Note $D_i$ does **not** scale with incident duration. It is a level, not a rate. This is what makes §5 happen.

## 1.4 Human cost

| Symbol | Name | Unit | Source |
|---|---|---|---|
| $w$ | Engineer cost rate | USD/s | Published SRE salary ÷ working seconds per year. **Eliminated by normalisation — see §6.1** |
| $H_e, H^{+}, H^{-}$ | Engineer-seconds consumed under escalate / correct assist / wrong assist | s | Anchored to incident-management literature; swept |

## 1.5 Time to resolution

| Symbol | Name | Unit | Source |
|---|---|---|---|
| $T_e$ | MTTR when a human gets evidence but no hypothesis | s | Reference point. Benchmark incident durations |
| $\Delta^{+} = T_e - T^{+}_{\text{act}}$ | Seconds saved by a **correct** autonomous action | s | Estimated; swept |
| $\Delta^{-} = T^{-}_{\text{act}} - T_e$ | Seconds lost by a **wrong** autonomous action | s | Estimated; swept. Anchored to the published finding that mis-triage causes up to 10× delay |
| $\delta^{+} = T_e - T^{+}_{\text{assist}}$ | Seconds saved by a **correct** hypothesis handed to a human | s | Estimated; swept |
| $\delta^{-} = T^{-}_{\text{assist}} - T_e$ | Seconds lost to **anchoring** on a wrong hypothesis | s | Estimated; swept |

## 1.6 Inference cost — present, and deliberately excluded from the gate

| Symbol | Name | Unit | Source |
|---|---|---|---|
| $c^{\text{inf}}_i$ | Tokens consumed investigating incident $i$, priced | USD | API accounting |

**Sunk at the moment the gate runs.** It is identical across all three actions and therefore cancels out of every comparison. It is *not* in the threshold. See §7.

---

# 2. The outcome model

One ordering assumption carries the whole model, and it must be stated explicitly and defended in the paper:

$$T^{+}_{\text{act}} \;<\; T^{+}_{\text{assist}} \;<\; T_e \;<\; T^{-}_{\text{assist}} \;<\; T^{-}_{\text{act}}$$

In words: a correct automated fix is fastest; a correct hypothesis handed to a human is next; a human working from evidence alone is the neutral reference; **a wrong hypothesis is worse than no hypothesis** because of anchoring; and a wrong automated action is worst of all, because the fault persists and the system has been changed underneath the engineer who now has to diagnose it.

The fourth inequality is the one a reviewer will challenge. It is the anchoring claim, and it must be cited, not assumed.

---

# 3. Expected loss of each action

Engineer time under **act**: zero if correct, $H_e$ if wrong — the human still has to do the whole job afterwards.

$$L_i(\text{act}) \;=\; q_i\,\rho_i\bigl(T_e - \Delta^{+}\bigr) \;+\; (1-q_i)\Bigl[\rho_i\bigl(T_e + \Delta^{-}\bigr) + wH_e + D_i\Bigr]$$

$$L_i(\text{assist}) \;=\; q_i\Bigl[\rho_i\bigl(T_e - \delta^{+}\bigr) + w\bigl(H_e - \eta^{+}\bigr)\Bigr] \;+\; (1-q_i)\Bigl[\rho_i\bigl(T_e + \delta^{-}\bigr) + w\bigl(H_e + \eta^{-}\bigr)\Bigr]$$

$$L_i(\text{escalate}) \;=\; \rho_i T_e \;+\; w H_e$$

where $\eta^{+} = H_e - H^{+}$ and $\eta^{-} = H^{-} - H_e$.

---

# 4. The two thresholds

## 4.1 Act versus escalate

$L(\text{act}) < L(\text{escalate})$ reduces to $(1-q)\bigl[\rho\Delta^{-} + D\bigr] < q\bigl[\rho\Delta^{+} + wH_e\bigr]$, giving

$$\boxed{\;\tau^{\text{act}}_i \;=\; \frac{\rho_i\Delta^{-} + D_i}{\rho_i\bigl(\Delta^{+} + \Delta^{-}\bigr) + wH_e + D_i}\;}$$

## 4.2 Assist versus escalate

$$\boxed{\;\tau^{\text{assist}}_i \;=\; \frac{\rho_i\delta^{-} + w\eta^{-}}{\rho_i\bigl(\delta^{+} + \delta^{-}\bigr) + w\bigl(\eta^{+} + \eta^{-}\bigr)}\;}$$

No $D$ term appears — a human reviews the hypothesis before anything changes, so assisting causes no collateral damage. This is structurally why assist sits below act.

## 4.3 The policy

$$a^{*}_i \;=\; \begin{cases} \text{act} & q_i \ge \tau^{\text{act}}_i \\[2pt] \text{assist} & \tau^{\text{assist}}_i \le q_i < \tau^{\text{act}}_i \\[2pt] \text{escalate} & q_i < \tau^{\text{assist}}_i \end{cases}$$

## 4.4 Well-posedness

$\tau^{\text{act}} \in [0,1]$ always, since the denominator exceeds the numerator by $\rho\Delta^{+} + wH_e > 0$. Same for $\tau^{\text{assist}}$.

**Assertion to put in the code:** $\tau^{\text{assist}}_i \le \tau^{\text{act}}_i$. This is *not* guaranteed for all parameter settings. Where it fails, assist is dominated and the policy degenerates to two actions — report that rather than suppressing it.

---

# 5. The structural result — and it is not what the problem statement claimed

Differentiating $\tau^{\text{act}}$ with respect to stake:

$$\frac{\partial \tau^{\text{act}}}{\partial \rho} \;\propto\; \Delta^{-} w H_e \;-\; D\,\Delta^{+}$$

$$\boxed{\;\frac{\partial \tau^{\text{act}}}{\partial \rho} > 0 \iff \frac{D}{wH_e} \;<\; \frac{\Delta^{-}}{\Delta^{+}}\;}$$

Two readable ratios:

- $D / (wH_e)$ — **collateral damage relative to the cost of simply paging a human**
- $\Delta^{-} / \Delta^{+}$ — **the asymmetry of automation**: seconds lost when wrong versus seconds saved when right

**The threshold rises with stake when damage is cheap relative to human response.** The familiar intuition: bigger incident, be more careful.

**The threshold *falls* with stake when damage is expensive relative to human response.** Less obvious and correct on inspection: when an incident is burning fast enough, waiting for a human costs more than a bad guess. The building is on fire; try something.

### Why this is the better paper

The problem statement said stakes should *raise* the threshold. The algebra says stakes *move* it, and the direction flips at $D/(wH_e) = \Delta^{-}/\Delta^{+}$.

This is stronger, because it forecloses the obvious reviewer reply. Against "the threshold should be higher on big incidents", a reviewer says *so tune it more conservatively and you are done*. Against "the correct threshold is higher on some incidents and lower on others, and a realistic population contains both", there is no tuning answer. **A single constant is wrong in both directions at once.**

### What this changes downstream

**RQ1 is re-specified.** The Day 2 plot is no longer the distribution of $\rho$ alone. It must show the joint distribution of $D/(wH_e)$ and $\Delta^{-}/\Delta^{+}$, and specifically **whether a realistic incident population straddles the sign-flip boundary**. Straddling it is now the premise the paper needs.

**The falsification condition is re-specified.** The thesis is refuted if the population sits entirely on one side of the boundary *and* stake variance is low — because then one conservative constant really would suffice.

---

# 6. Free parameters and the sensitivity sweep

## 6.1 One parameter eliminated for free

Divide every loss by $w$. All quantities become **engineer-second equivalents**, $w$ vanishes, and the remaining terms are scale-free ratios. Define $\tilde\rho_i = \rho_i / w$ — the incident's burn rate measured in engineers.

## 6.2 What must be swept

| Parameter | Meaning | Sweep range |
|---|---|---|
| $\lambda_{\text{exp}}$ | USD per failed request | 4 orders of magnitude |
| $\lambda_{\text{slo}}$ | USD per unit error budget | 4 orders of magnitude |
| $\kappa$ | Extra outage seconds per downstream service | 3 orders of magnitude |
| $\Delta^{-}/\Delta^{+}$ | Automation asymmetry | 1× to 20×, anchored on the published 10× mis-triage figure |
| $\delta^{-}/\delta^{+}$ | Anchoring asymmetry | 0.5× to 10× |
| $H_e, \eta^{\pm}$ | Engineer-seconds per branch | ±1 order of magnitude |

## 6.3 The invariance that answers "your numbers are made up"

The **ranking** of incidents by $\rho$ is invariant to scaling all $\lambda$ by a common factor. Since the contribution is about relative ordering and threshold *movement*, the absolute price level cancels. State this explicitly — it converts the largest attack surface into a one-line proof.

---

# 7. What is excluded, and what is the extension

**Inference cost is sunk at the gate.** $c^{\text{inf}}_i$ is identical across act, assist and escalate at the moment of decision, so it cancels from every comparison and does not appear in either threshold. Including it would be an error.

**It is not irrelevant — it belongs to a different decision.** If the agent may *continue investigating* to raise $q$, there is a stopping rule: keep spending tokens while the marginal reduction in expected loss exceeds the marginal token cost. On a low-stake incident that budget is nearly zero; on a high-stake one it is large.

This is the **compute-optimal RCA** extension. Named as future work in this paper. Do not attempt it this week — it needs the agent runs the short paper is explicitly avoiding.

---

# 8. Terms considered and rejected

Rejected under the Day 0 rule: *a term with no measurable source is deleted, not estimated.*

| Rejected term | Why it is real | Why it is out |
|---|---|---|
| Reputational damage | Genuinely the largest cost of a public outage | No measurable source in any benchmark, and no defensible proxy. Including it would make every result a function of one invented number |
| SLA financial penalties | Directly monetary, contractually exact | Contract-specific and absent from all public datasets. Would apply to a real deployment; cannot be evaluated here |
| Customer churn | Well-documented consequence | Requires longitudinal business data no benchmark contains |
| On-call fatigue / alert burnout | Real, and a major driver of SRE attrition | No unit, no source, no way to price it without inventing the number outright |

Each is named in the paper's limitations section as a term a production deployment would add. Naming what was cut, and why, is stronger evidence of discipline than showing only what was kept.

---

# 9. Day 0 checklist

- [x] Every term has a symbol, a unit and a source
- [x] Every term without a measurable source is either swept or deleted
- [x] The free parameters are named and their sweep ranges fixed
- [x] One parameter eliminated by normalisation
- [x] Sunk cost identified and excluded, with reasoning
- [x] Rejected terms documented with reasons
- [x] Both thresholds derived and shown well-posed
- [ ] The $\tau^{\text{assist}} \le \tau^{\text{act}}$ ordering asserted in code — Day 1
- [ ] RQ1 re-specified in the draft to target the sign-flip boundary — Day 0, tonight
- [ ] The anchoring assumption ($T^{-}_{\text{assist}} > T_e$) given a real citation — Day 1

---
