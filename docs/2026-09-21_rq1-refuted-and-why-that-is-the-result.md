# RQ1 refuted: a parsing bug, a degenerate composition, and why the paper is better for it

*Research journal entry — 2026-09-21. Part of the [risk-adjusted abstention](../README.md) study.*

---

> **Summary:** The earlier PASS was wrong twice over. A parsing defect zeroed the failure signal on 30% of cases, and the stake composition was dominated by one term to the point where the sensitivity sweep could not move. Fixing both flips the pre-registered verdict to REFUTED — and the real finding turns out to be sharper than either branch anticipated: the sign of the headline result is chosen by a constant no telemetry can supply.

---

> [!NOTE]
> **What this code/concept does**
> Two corrections were made and the answer reversed.
>
> **The parsing bug.** The benchmark's column names change with the *kind of fault injected*, not only with the system. Cases with a CPU fault expose a column called `_load`; cases with a network-delay fault on the very same system expose `_workload` instead. The loader was written to look up column names by system, so on every delay, disk and loss case it found no traffic column at all, recorded zero requests, and therefore computed a zero failure rate. Roughly a third of the corpus was silently reported as "nothing went wrong".
>
> **The degenerate composition.** Stake was supposed to be three things added together: wasted infrastructure, failed requests, and error-budget burn. With the original exchange rates the burn term was about a hundred thousand times larger than the other two, so the sum was just the burn term. Changing the price of the dominant term only rescales everything, which a proposition in the paper already shows makes no difference — so the sensitivity sweep returned the same answer fifteen times and looked like robustness.

> [!NOTE]
> **Why we are doing it this way**
> The pre-registered gate existed precisely so that this moment would be cheap. The falsification condition was written into the paper before any data was downloaded, the negative-result wording was drafted in commented blocks before any result existed, and the decision rule (minority side ≥5%, stake spread ≥1 decade, threshold spread ≥0.10) was fixed in code before the loader worked.
>
> That meant flipping the paper took three text replacements and no argument. There was no moment of deciding whether the result was good enough to keep, because that decision had already been made in advance by someone with no stake in the outcome — an earlier version of the same person.
>
> The alternative, had the introduction been written first in the usual way, would have been a draft full of prose arguing for a conclusion the data does not support, and a strong incentive to find a parameter setting that rescued it. That incentive is exactly what the sweep revealed *does* exist here: a setting that rescues the result is available, and the honest thing is to say so rather than to adopt it.

> [!NOTE]
> **How it works step by step**
> **1. Notice the pattern is too clean.** Burn rate was exactly zero on 100% of Online Boutique delay, disk and loss cases and 0% of its cpu and mem cases. Real measurements are not that tidy. A perfectly deterministic split by category almost always means a lookup is failing, not that nature is cooperating.
>
> **2. Compare the raw files.** Five cases from the same system with different faults showed different column families — `_load` and `_latency` for two of them, `_workload` and `_latency-50`/`_latency-90` for the other three.
>
> **3. Detect the grammar per file rather than per system**, and make a zero traffic rate raise an error instead of quietly producing a zero. Cases with no measured traffic fell from 30% to zero.
>
> **4. Check what remains.** Burn rate is still zero on 36.5% of cases — but now legitimately. Sock Shop CPU faults peak at 85 ms of latency against a 500 ms objective and emit no errors. They breach no SLO. Not every injected fault is an incident, and that is a real property of the corpus rather than a defect.
>
> **5. Rebalance the composition.** Set each component's exchange rate so its 90th percentile matches the infrastructure component's. The 90th percentile rather than the median, because a third of the burn values are legitimately zero and a zero median makes the calibration undefined.
>
> **6. Re-run the gate.** Stake spread collapses from 9.30 decades to 1.51. Threshold spread collapses from 0.966 to 0.056. The population no longer straddles the boundary at all — 100% of incidents sit on one side. **REFUTED.**
>
> **7. Sweep the relative weights properly**, on a simplex rather than by scaling everything together. The derived threshold now loses to the tuned constant in twelve of twelve weightings.
>
> **8. Sweep along the one axis that matters** — how far the burn term dominates — and find a window where the method wins by up to 34%. The window sits between roughly 0.8× and 85× burn-to-infrastructure dominance, and where inside it you land is set by a constant no telemetry supplies.

> [!NOTE]
> **Key terms defined**
> - **Column grammar** — the naming convention for a dataset's columns. Here it varies by fault type, which is unusual and undocumented.
> - **Degenerate composition** — a weighted sum in which one term is so much larger that the others cannot affect the result.
> - **Common rescale** — multiplying every component by the same factor. Changes nothing that matters; equivalent to changing currency.
> - **Simplex sweep** — varying weights that must sum to one, so increasing one necessarily decreases another. This is what genuinely tests relative weighting.
> - **Threshold dispersion** — how much the derived threshold varies across incidents, measured here by interquartile range.
> - **Straddling** — having incidents on both sides of the sign-flip boundary.
> - **Pre-registration** — fixing the hypothesis, the decision rule and the reporting language before seeing data, so the result cannot be chosen after the fact.
> - **Breakdown point** — the parameter setting at which a claimed advantage disappears.

> [!WARNING]
> **Common mistakes to avoid**
> - **Reading a clean categorical split as signal.** A metric that is exactly zero for three fault types and never zero for two others is a failing lookup, not a discovery. Suspicion should scale with tidiness.
> - **Letting a zero mean "nothing happened".** The loader now raises on zero traffic rather than returning it. A silent zero propagates through every downstream calculation wearing the costume of a measurement.
> - **Accepting a flat sensitivity sweep.** Fifteen identical answers meant the parameter was inert, not that the method was robust. The sweep was measuring the wrong thing and said so by being too quiet.
> - **Calibrating on a median that is legitimately zero.** A third of burn values are genuinely zero; the 90th percentile is the right anchor.
> - **Adopting the parameter setting that rescues the result.** One exists. Using it without saying it was selected for that purpose would be the dishonest move available at exactly this point, and it is the reason the sweep was built.
> - **Confusing the gate's two conditions.** The pre-registered rule required both straddling and dispersion. The data shows dispersion alone predicts the advantage — the method wins at weightings where 100% of incidents are on one side. The gate was, in that respect, the wrong test, and the paper now says so.

> [!TIP]
> **How this connects to the bigger picture**
> Three times now an instrument built to check the work has changed the work. The novelty scan cut two thirds of the original brief. The loss-function derivation produced a stronger claim than the one written down. The sensitivity sweep has now refuted the empirical claim entirely.
>
> This is the pattern that separates research from advocacy, and it is worth noticing that each instrument was built *before* it was needed, when there was nothing at stake in its design. The gate was coded before the loader worked. The negative wording was drafted before any number existed. Neither could have been written honestly afterwards.
>
> The paper that results is not the one intended, but it is a real contribution: the sufficiency of a fixed confidence threshold is assumed everywhere in this literature and, as far as the novelty scan found, has never been tested. It has now been tested, and the answer is that on public benchmarks the question is not decided by the incident population at all.

> [!IMPORTANT]
> **Portfolio note**
> Demonstrates finding and reporting two errors that reversed a favourable result — including one that would have survived review undetected — and publishing the refutation of a pre-registered hypothesis rather than the parameter setting that would have rescued it.

---

## The reversal in one table

| | First run | After both fixes |
|---|---|---|
| Cases with zero measured traffic | 30% | **0%** |
| Cases with zero burn | 59.8% | 36.5% *(legitimate)* |
| Stake spread | 9.30 decades | **1.51 decades** |
| τ_act IQR | 0.966 | **0.056** |
| Threshold rises / falls with stake | 39.8% / 60.2% | **100% / 0%** |
| Derived vs hindsight-tuned | −9.8% *(wins)* | **+39.6%** *(loses)* |
| Pre-registered verdict | PASS | **REFUTED** |

## The burn-dominance sweep — where the answer actually comes from

| burn/infra | τ_act IQR | hindsight | derived | Δ |
|---|---|---|---|---|
| 0.085 | 0.056 | 0.0727 | 0.1015 | +39.6% |
| 0.25 | 0.080 | 0.1134 | 0.1230 | +8.4% |
| 0.85 | 0.158 | 0.2375 | 0.2221 | −6.5% |
| **2.5** | **0.319** | 0.3938 | 0.2599 | **−34.0%** |
| 8.5 | 0.529 | 0.4379 | 0.3234 | −26.1% |
| 25 | 0.579 | 0.3615 | 0.3300 | −8.7% |
| 85 | 0.441 | 0.2731 | 0.2733 | +0.1% |
| 850 | 0.017 | 0.2234 | 0.2356 | +5.5% |

The method wins only between roughly 0.8× and 85×. **The sign of the headline result is selected by λ_slo, which no telemetry supplies.**

## Two secondary findings worth keeping

1. **Dispersion, not straddling, predicts the advantage.** The method wins wherever τ_act IQR exceeds about 0.15, including at weightings where 100% of incidents sit on one side of the boundary. The pre-registered gate conjoined the two conditions and was the wrong test.
2. **The ordering violation fell from 35–39% synthetic to 25.7% measured**, exactly as predicted when it was first flagged. Stake and blast radius are correlated in real systems.

## Paper status

Abstract, introduction contribution 4, introduction paragraph 3 and the conclusion switched to the refuted wording. Section 6 now written with real numbers. Outstanding: RQ2 deferred, figures, second dataset, author list.

---
