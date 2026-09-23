# Owning a contradiction by finding where it stops being true

*Research journal entry — 2026-09-21. Part of the [risk-adjusted abstention](../README.md) study.*

---

> **Summary:** The paper argues for three possible responses to an incident, but measured that the middle one is never worth choosing. Rather than admitting the contradiction and moving on, the algebra was pushed until it gave the exact stake above which the middle option starts to pay — about $111 per hour of incident burn. Both corpora sit 34 and 80 times below it. A collapsed contribution turned into a scoped claim with a testable prediction attached.

---

> [!NOTE]
> **What this code/concept does**
> The system can do one of three things when it suspects a cause: act on it, hand it to a person with a suggestion, or hand it to a person with nothing. The paper's framing depends on all three being live options.
>
> The measurements said otherwise. On every incident in both corpora, the middle option — suggest and hand over — was never the cheapest. It was always beaten by one of the other two. A whole part of the paper's structure was describing a choice that never gets made.
>
> This session did not fix that by softening the claim. It asked a sharper question: **is the middle option worthless, or is it worthless *here*?** Those are very different statements, and only one of them is true.

> [!NOTE]
> **Why we are doing it this way**
> **Because "this never happened in my data" and "this never happens" are not the same sentence,** and the gap between them is where the honest contribution lives. Admitting the contradiction would have been truthful but uninformative — it tells a reader the framing failed without telling them when it would succeed.
>
> **Because the algebra was already there.** Both thresholds were already written as equations. Comparing their behaviour at very low and very high stake is arithmetic, not new theory, and it answers the question directly.
>
> **Because a crossing point is a prediction.** Saying "the middle option becomes worthwhile above roughly $111 per hour" is a claim that can be checked by anyone with a higher-stake system. A paper that only reports what it measured is a record; a paper that says where its conclusion flips is testable.
>
> **Because it explains an external disagreement.** Industry practice at the time had converged on exactly the ordering this paper's data contradicts. A crossing point reconciles the two: both can be right, in different regimes.

> [!NOTE]
> **How it works step by step**
> **1. Take limits at both ends.** The two thresholds were examined as stake goes to zero and as stake grows large. At low stake the middle option is dominated, exactly as measured. At high stake it is **not**. The two curves therefore cross somewhere in between — and because they cross, there is a single finite stake at which the middle option starts to earn its place.
>
> **2. Solve for where.** The crossing has no clean closed form, so it was solved numerically: **about 0.031 US dollars per second, roughly $111 per hour** of incident burn.
>
> **3. Check it is not an artefact of one assumption.** The crossing point was re-computed across the range of collateral-damage values the corpora actually contain. It barely moves. A threshold that shifted wildly with a nuisance parameter would be a curiosity; one that stays put is a property.
>
> **4. Measure both corpora against it.** The first corpus has a median incident burn of about $3.24 per hour — roughly 34 times below the crossing. The second is about $1.38 per hour — about 80 times below. And the single highest-stake incident in either corpus still falls short, by factors of 3 and 32.
>
> That last check matters most. Medians being low could mean the corpora are merely typical. The *maximum* being low means these benchmarks contain nothing in the regime where the framing applies. The claim is now about the benchmarks, which is a fact, rather than about the world, which would be a guess.
>
> **5. Write it everywhere it changes the meaning.** Not one sentence in one section. The abstract, the first contribution, the part describing the three options (as a forward reference, so a reader meets the caveat before the framing), a new results subsection with the limit algebra and the shortfall table, the future work, the conclusion, and the caption of the figure that shows the domination.

> [!NOTE]
> **Key terms defined**
> - **Dominated option** — a choice that is never the best one available.
> - **Taking a limit** — asking what an equation does as one of its inputs becomes very small or very large. Often clearer than the general case.
> - **Crossing point** — the input value at which two curves swap order; here, where the middle option stops being dominated.
> - **Incident burn** — cost per unit time while an incident continues, expressed here per hour.
> - **Domain of validity** — the range of conditions under which a conclusion holds.
> - **Near-invariant** — barely changes when a secondary parameter is varied.
> - **Testable prediction** — a statement specific enough that someone else's data could contradict it.

> [!WARNING]
> **Common mistakes to avoid**
> - **Treating "never happened in my data" as "never happens".** The first is a measurement; the second is a much larger claim the data does not support.
> - **Quietly dropping the collapsed part of the framing.** A reader who notices the gap will assume you did not.
> - **Admitting a contradiction and stopping there.** Honest but uninformative. The useful version says where the contradiction ends.
> - **Reporting only the median.** The maximum is what establishes that *nothing* in the corpus reaches the relevant regime.
> - **Not checking the result against its nuisance parameters.** A crossing point that moves with an arbitrary constant is not a finding.
> - **Patching one sentence.** A scoped claim has to appear everywhere the unscoped one did, or the paper contradicts itself — a mistake made in exactly this way three sessions later, in [2026-09-21_pre-submission-rescan](2026-09-21_pre-submission-rescan.md).
> - **Putting the caveat after the framing.** A reader who meets the three options without the caveat has already formed the wrong expectation.

> [!TIP]
> **How this connects to the bigger picture**
> This is the turn where the paper's weakest point became its most defensible one. It is the same move as the negative result itself: not "our method works", but "here is precisely when it does and does not, and here is how you would check".
>
> It also joins up several earlier sessions. The domination was what made a parameter inert in [2026-09-21_clearing-the-markers](2026-09-21_clearing-the-markers.md); it was what figure 4 in [2026-09-21_four-figures-and-one-replaced](2026-09-21_four-figures-and-one-replaced.md) was redrawn to show; and the external industry evidence that this crossing point explains is the third finding of [2026-09-21_pre-submission-rescan](2026-09-21_pre-submission-rescan.md).

> [!IMPORTANT]
> **Portfolio note**
> Demonstrates converting a structural flaw into a scoped, testable claim — deriving the exact boundary at which the paper's own framing begins to apply, and showing with the maximum rather than the median that the available benchmarks never reach it.

---

## The numbers

| | Crossing point | Median burn | Short by | Max burn short by |
|---|---|---|---|---|
| Derived threshold | $111/hr (0.031 USD/s) | — | — | — |
| Corpus 1 | — | $3.24/hr | 34x | 3x |
| Corpus 2 | — | $1.38/hr | 80x | 32x |

---
