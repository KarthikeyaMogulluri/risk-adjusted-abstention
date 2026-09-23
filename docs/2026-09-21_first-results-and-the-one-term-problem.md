# First results, and the one-term problem the sensitivity sweep exposed

*Research journal entry — 2026-09-21. Part of the [risk-adjusted abstention](../README.md) study.*

---

> **Summary:** The first real numbers. The derived threshold beats the hindsight-tuned fixed threshold by 9.8% on 249 real cases, and the advantage holds in 15 of 15 parameter settings. But the robustness is *too* clean — the advantage is identical to one decimal place across four decades of one parameter, which is not strength, it is a symptom. The stake model is behaving as a one-term model because the error-budget component swamps the other two by five orders of magnitude.

---

> [!NOTE]
> **What this code/concept does**
> Three things were measured for the first time on real benchmark data rather than on made-up numbers.
>
> **RQ1** asked whether real incidents differ enough from each other that a single confidence cut-off cannot fit them all. Answer: yes.
>
> **RQ3** asked whether computing the cut-off per incident actually beats the best possible single cut-off. Answer: yes, by about 10%.
>
> **RQ4** asked whether that advantage survives if the cost assumptions are wrong. Answer: it survives everything tested — and that is the part that turned out to be a problem rather than a victory.

> [!NOTE]
> **Why we are doing it this way**
> The sweep varied two exchange rates independently: the price of a failed request and the price of a unit of error budget. The point of varying them *independently* is to test whether the conclusion depends on the relative weighting of the stake components, not merely on the overall price level.
>
> Proposition 3 already proves the result is invariant to scaling every component by a common factor, because that is just a change of currency. So a sweep that produced identical numbers under *common* scaling would be expected. A sweep that produces identical numbers under *independent* variation should not.
>
> It did. Fifteen settings, advantage of -9.8% in thirteen of them and -10.3% in the other two. That is not robustness; it is evidence that one of the two parameters is doing nothing, because the term it prices is negligible next to another.

> [!NOTE]
> **How it works step by step**
> **1. Load real stakes.** 249 cases from RCAEval RE1 across Online Boutique and Sock Shop, with stake, collateral damage and resolution time computed from telemetry.
>
> **2. Simulate the confidence signal only.** Real stakes, simulated confidence at the calibration levels reported in the literature. This is the paper's declared scope; it does not claim an end-to-end agent result.
>
> **3. Compare against five baselines**, the strongest being a single fixed threshold tuned with hindsight on the test set — an opponent deliberately given information no deployable system could have.
>
> **4. Measure cost-weighted regret** against a perfect-information oracle, not accuracy.
>
> **5. Sweep the two exchange rates** across four decades and two decades respectively.
>
> **6. Look at the spread of the answer.** The spread was 0.5 percentage points across the entire sweep. Investigating why revealed the composition problem: infrastructure cost is on the order of one thousandth of a dollar per second, while the error-budget term reaches hundreds of thousands. The sum is the error-budget term, and the other two components are rounding error.
>
> **7. Recognise what that means for the claim.** With one term dominating, scaling its own price is a pure rescale of the whole stake vector, which Proposition 3 says cancels. The sweep therefore re-proved Proposition 3 rather than testing misspecification, which is what it was supposed to do.

> [!NOTE]
> **Key terms defined**
> - **Regret** — how much worse a policy did than one with perfect knowledge. Zero is the oracle.
> - **Hindsight-tuned baseline** — the single best constant threshold, chosen by looking at the test answers. An unfair opponent, used on purpose.
> - **Exchange rate (lambda)** — a declared constant converting failed requests or error budget into money.
> - **Common scaling** — multiplying every cost component by the same factor. Equivalent to changing currency; changes nothing that matters.
> - **Independent variation** — changing the components' prices relative to each other. This *should* change results, and is what a real sensitivity analysis tests.
> - **Coverage** — the fraction of incidents the system handled rather than handing over with no hypothesis.
> - **ECE** — how far stated confidence drifts from actual accuracy.
> - **Dominant term** — a component so much larger than the others that the sum is effectively just that component.

> [!WARNING]
> **Common mistakes to avoid**
> - **Reading flat sweep results as robustness.** An advantage identical to one decimal place across four decades of a parameter is a signal that the parameter is inert, not that the method is bulletproof. Suspicion is the correct response to a result that is too clean.
> - **Reporting a composite model that is secretly a single term.** The paper describes stake as a three-component composite. On this data it is one component plus noise. Publishing the composite description without saying so would misrepresent what was actually measured.
> - **Fixing it by tuning until the numbers look balanced.** The correct fix is to normalise the components to comparable scale *before* weighting — for instance so each contributes equally at the population median — and then sweep the relative weights. Adjusting constants until the output looks plausible is fitting the model to the desired conclusion.
> - **Quoting 9.30 decades of stake spread as a headline.** Median burn rate is zero on half the cases, so the spread is partly a bimodal detection artefact: cases where the injected fault produced no latency violation above the objective sit at the infrastructure-only floor, and cases where it did sit five decades higher. That is a detector property as much as a stake property.
> - **Forgetting how far the oracle still is.** The derived policy's regret is 0.208 against an oracle at 0. The improvement over the best constant is real but the absolute gap to perfect information remains large, and the paper should say so.

> [!TIP]
> **How this connects to the bigger picture**
> The sweep was built to defend against a reviewer saying "your cost numbers are invented". It did its job in an unexpected direction: instead of confirming the defence, it exposed that the cost model is not doing the work the paper claims for it.
>
> This is the same pattern as the loss-function derivation, which produced a stronger claim than the one originally written down, and the novelty scan, which killed two thirds of the original brief. Each time, the instrument built to check the work changed the work. That is what distinguishes a method from a hope.
>
> It also validates the decision to run RQ1 first and to refuse to write Section 6 before the data existed. Had the results section been drafted in advance, it would now describe a three-component stake model that the measurements do not support.

> [!IMPORTANT]
> **Portfolio note**
> Demonstrates reading a favourable result sceptically — treating an unnaturally stable sensitivity sweep as a defect in the instrument rather than a confirmation of the hypothesis, and diagnosing the cause before reporting the number.

---

## The numbers

Real stakes, 249 cases, RCAEval RE1, Online Boutique + Sock Shop. Confidence simulated at ECE 0.070.

| Policy | Regret vs oracle | vs hindsight |
|---|---|---|
| always act | 1.2665 | — |
| always escalate | 0.2475 | — |
| fixed tau = 0.80 | 0.2648 | — |
| **fixed, hindsight-tuned** (tau* = 0.845) | **0.2306** | — |
| **derived (ours)** | **0.2081** | **-9.8%** |
| oracle | 0.0000 | — |

Coverage 0.727. Derived tau_act range [0.012, 1.000]. Ordering violations 25.7%.

## The sweep

| | lambda_slo range | lambda_exp range | Settings | Advantage |
|---|---|---|---|---|
| Result | 1 to 10,000 | 0.001 to 0.1 | 15 | -9.8% to -10.3% |

Derived beats the hindsight-tuned constant in **15 of 15**. Median advantage -9.8%.

**And that is the problem.** Thirteen of fifteen settings return exactly -9.8%.

## Diagnosis

| Component | Typical magnitude | Share of stake |
|---|---|---|
| infrastructure (CPU + memory) | ~1e-3 USD/s | negligible |
| failed-request exposure | ~1e-1 USD/s | negligible |
| error-budget burn | up to ~4e5 USD/s | effectively all of it |

With one term dominating, varying its price is a common rescale, which Proposition 3 proves cancels. The sweep therefore confirmed a proposition instead of testing misspecification.

## Open items this creates

- [ ] Normalise the three stake components to comparable scale before weighting, then re-sweep the *relative* weights
- [ ] Investigate why median burn is zero on half the cases — is the latency objective too loose for cpu/mem faults?
- [ ] Re-run RQ1 after rebalancing; the 9.30-decade figure will change
- [ ] Load RCA100 as the second population
- [ ] Ordering violation fell from ~35-39% synthetic to 25.7% real, as predicted — still needs a decision

---
