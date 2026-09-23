# Clearing every placeholder, and what filling them in revealed

*Research journal entry — 2026-09-21. Part of the [risk-adjusted abstention](../README.md) study.*

---

> **Summary:** Every deliberate gap left in the paper was filled with a measured value. Two of the gaps, once filled, said something the paper had not expected: the best possible fixed policy on one corpus is to never escalate at all, and one of the model's parameters turns out to have no effect on anything, for a reason that is itself a finding. A bug in the author's own editing script was caught by auditing the result rather than assuming the edit had landed.

---

> [!NOTE]
> **What this code/concept does**
> While a paper is being drafted, numbers that are not yet measured get written as visible markers — a word in capitals standing where a value will go. The point of a marker is that it is impossible to mistake for a real number and impossible to miss when searching.
>
> This session removed all of them, by measuring each value properly and writing it in. It also wrote the section explaining why the second research question was not answered, rather than leaving that question silently unmentioned.

> [!NOTE]
> **Why we are doing it this way**
> **Because a blank is safer than a guess.** A rough number typed in as a temporary stand-in becomes permanent, because it looks finished. A marker in capital letters cannot become permanent by accident — it can only be removed deliberately.
>
> **Because filling in a number is a measurement, not a formality.** Two of the values, once computed properly, changed what the paper claims. That only happens if the filling-in is treated as work rather than as tidying.
>
> **Because a question you cannot answer should be discussed, not omitted.** Dropping the unanswerable research question would have left a reader wondering whether it was tried and failed or never attempted. A short subsection saying what was asked, why it could not be answered with these corpora, and what data would answer it, is stronger than silence.
>
> **Because an edit is not done until you look at the result.** The script that inserted the results table wrote it over the top of a different table. Nothing errored. The only way to find that was to read the file afterwards.

> [!NOTE]
> **How it works step by step**
> **1. Fill the main results table with measured values for both corpora.** Straightforward for most cells — and then one cell was strange.
>
> **2. The first surprise: the best fixed policy is not to gate at all.** For comparison the paper computes what the best possible single fixed threshold would have been, chosen with full hindsight. On the first corpus that optimum is *zero* — meaning: never escalate to a human, always act.
>
> The reason is arithmetic, not paradox. The cost of an incident continuing is low relative to the cost of a person's time, so pausing to ask a human costs more than the mistakes it prevents. That is a real property of the corpus, and reporting it is more useful than hiding it, because it tells a reader precisely which regime the evidence comes from.
>
> **3. The second surprise: one parameter does nothing at all.** The model includes a pair of parameters describing how much a human's judgement is pulled toward a machine's suggestion. This had been flagged as an assumption needing justification.
>
> It was resolved by testing rather than arguing. The parameters were swept across a twenty-fold range — and nothing moved. Not a little: nothing. The reason is structural. Those parameters only ever enter the arithmetic through the middle option, and the middle option is never chosen on any incident in either corpus. A parameter attached to a branch that is never taken cannot affect an outcome.
>
> So it was demoted from a contested assumption to a stated modelling choice, with the supporting literature cited as motivation rather than as proof, and the sweep reported as evidence that the choice does not matter here.
>
> **4. Repair the table-placement bug.** The insertion script had landed the results table on top of the datasets table, removing it. Found by reading the file, not by any error.
>
> **5. Fix the citations.** One referenced work had no bibliography entry; three entries existed but were never cited. Both directions matter — a missing entry breaks a reference, an uncited entry is clutter suggesting the bibliography was assembled rather than used. Final state at this point: 26 citations, none missing, none unused.
>
> **6. Write the deferred-question subsection** rather than leaving the second research question unaddressed.

> [!NOTE]
> **Key terms defined**
> - **Placeholder / marker** — a deliberately conspicuous word standing where a value will go, designed to be impossible to overlook.
> - **Hindsight-tuned constant** — the best single fixed setting, chosen after seeing all the data. Not achievable in practice; used as a generous comparison.
> - **Inert parameter** — an input that has no effect on the output, whatever its value.
> - **Dominated option** — a choice that is never best. Parameters attached only to it can never matter.
> - **Sensitivity sweep** — varying a parameter across a range to see how much the result moves.
> - **Automation bias** — the tendency of a person to over-trust a machine's suggestion. The thing those inert parameters were modelling.
> - **Orphaned citation** — a bibliography entry never referred to in the text.

> [!WARNING]
> **Common mistakes to avoid**
> - **Typing a plausible number as a temporary value.** It looks finished, so it stays. Use a marker that cannot be mistaken for data.
> - **Treating placeholder-filling as tidying up.** Two of these values changed what the paper claims.
> - **Hiding an awkward measured value.** "The optimal policy is to never escalate" sounds like it undermines the paper. Reported with its reason, it defines the paper's domain of validity — which is a contribution.
> - **Arguing about an assumption you could test instead.** A sweep settles in minutes what a paragraph of justification only obscures.
> - **Assuming an edit landed.** A script that writes over the wrong region produces a valid file and no error.
> - **Checking citations in one direction only.** Missing entries break references; unused entries signal a bibliography that was assembled rather than read.
> - **Silently dropping a question you could not answer.** A reader cannot tell omission from failure, and will assume the less flattering one.

> [!TIP]
> **How this connects to the bigger picture**
> This session is where the paper's honesty stopped being a stated intention and became a set of specific uncomfortable sentences. The zero-threshold finding and the inert parameter both make the work look less impressive in isolation and more trustworthy in total.
>
> The inert-parameter finding also fed directly into the argument built two sessions later. The parameters are inert *because* the middle option is dominated — which is the same fact that [2026-09-21_owning-the-three-action-contradiction](2026-09-21_owning-the-three-action-contradiction.md) turns into the paper's scoped claim, and that figure 4 in [2026-09-21_four-figures-and-one-replaced](2026-09-21_four-figures-and-one-replaced.md) was redrawn to show.

> [!IMPORTANT]
> **Portfolio note**
> Shows the judgement to report two measured results that superficially weaken the paper — an optimal policy of never escalating, and a parameter proven to do nothing — and to settle a contested assumption by testing it rather than defending it.

---
