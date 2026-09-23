# Correcting an overclaim properly, and finding a better pitch inside it

*Research journal entry — 2026-09-21. Part of the [risk-adjusted abstention](../README.md) study.*

---

> **Summary:** The previous session narrowed an overclaimed contribution — in one place. An audit found the same claim asserted in three more, including the abstract, so the paper contradicted itself. Fixing all four forced a sharper question: if the established literature already covers the varying cost, what is genuinely left? The answer turned out to be a better claim than the original — not that the threshold varies, but that it varies *non-monotonically* and changes direction.

---

> [!NOTE]
> **What this code/concept does**
> A claim in a paper is rarely written once. It appears in the abstract, in the introduction, in the contributions list, in the related-work section, in a comparison table, and in the conclusion — because those are all the places a reader looks for it.
>
> That means correcting a claim is not an edit. It is a search. This session searched for every assertion of novelty in the paper and checked each one against what the previous session had learned was actually true.
>
> It found the overclaim in **four** places, not the one that had been fixed.

> [!NOTE]
> **Why we are doing it this way**
> **Because a partly corrected paper is worse than an uncorrected one.** An uncorrected paper makes one wrong claim. A partly corrected one makes a wrong claim in the abstract and a careful one in section 2.3, which reads as either carelessness or an attempt to have it both ways.
>
> **Because the abstract is the version most people read.** Correcting the body and leaving the abstract overclaiming corrects the version almost nobody reads.
>
> **Because a forced narrowing is a chance to find the real claim.** Being made to say precisely what is left after the prior art is subtracted is uncomfortable, and it is exactly the process that produces a defensible contribution. The claim that survived is narrower, more specific, and more interesting than the one it replaced.
>
> **Because a sweeping statement about a large field is almost always false.** "Prior work has without exception..." is a claim about an entire fast-moving literature that no one person can verify. Softening those to describe your own reading costs nothing and removes a whole class of error.

> [!NOTE]
> **How it works step by step**
> **1. Audit every novelty claim rather than fixing the one you remember.** Four sites:
> - *The abstract* said prior work had treated the threshold as fixed "without exception" — a claim about an entire literature.
> - *The introduction* said the deferral literature models the cost as "a constant independent of the instance" — which the previous session had just established is untrue.
> - *Section 2.3* still said "first to instantiate", and additionally carried a dangling sentence fragment left behind by the earlier partial patch.
> - *The positioning table* listed the whole field as threshold-fixed, repeating the abstract's error in a form readers scan rather than read.
>
> **2. Notice the partial patch made things worse.** The earlier fix had edited one site and left a fragment behind at another. So the paper had an overclaim, a correction, and a piece of broken prose, all describing the same point.
>
> **3. Ask what is actually left.** Instance-dependent costs are established. And a threshold that varies with the instance follows *algebraically* from costs that vary with the instance — so claiming varying thresholds as a contribution claims a consequence of someone else's result.
>
> What is not in that literature is the **shape** of the variation. The paper measures that the threshold does not simply rise or fall with stake: it is non-monotone, and its direction of movement changes sign at a specific boundary. That is a claim about behaviour, not about existence, and nothing in the deferral literature makes it.
>
> **4. Rewrite all four sites plus the table's surrounding prose** so they say the same narrower thing.
>
> **5. Soften the remaining survey-style assertions.** Sweeping claims about what an entire field has or has not done became descriptions of the authors' own reading of it. This is not hedging for its own sake — it is the difference between a claim that can be falsified by one paper anyone finds, and a claim that is accurate as stated.
>
> **6. Recompile and re-check.** Clean compile, 32 citations, none missing, none unused, now 11 pages.

> [!NOTE]
> **Key terms defined**
> - **Overclaim** — asserting more originality than the literature supports.
> - **Positioning table** — a table placing the paper against related work along a few axes. Scanned rather than read, so errors in it are especially sticky.
> - **Monotone** — always moving in one direction as its input increases.
> - **Non-monotone** — rising over part of the range and falling over another.
> - **Sign change** — the point where the direction of movement reverses. The paper's surviving novel claim.
> - **Algebraic consequence** — something that follows automatically from an established result, and therefore cannot be claimed as new.
> - **Survey claim** — a statement about what an entire field has done. Very hard to verify, very easy to falsify.
> - **Dangling fragment** — leftover broken text from an incomplete edit.

> [!WARNING]
> **Common mistakes to avoid**
> - **Fixing the site you remember.** Claims propagate to every place a reader looks. Search for all of them.
> - **Leaving the abstract for last, or not at all.** It is the most-read part of the paper.
> - **Forgetting the tables.** A positioning table repeats claims in a form that is scanned, not read, so errors in it survive proofreading.
> - **Not re-reading after a patch.** The first correction left a broken fragment behind — the same failure mode as [2026-09-21_compiling-and-the-heredoc-corruption](2026-09-21_compiling-and-the-heredoc-corruption.md): an edit applied and its result unchecked.
> - **Claiming an algebraic consequence of prior work.** If it follows automatically from someone else's result, it is theirs.
> - **Writing "without exception" about a large field.** Unverifiable by anyone, falsifiable by one counterexample.
> - **Treating a forced narrowing as a loss.** It produced the better claim here, and usually does.

> [!TIP]
> **How this connects to the bigger picture**
> This is the last substantive change before submission, and it repeats the pattern the whole project has run on: the uncomfortable correction produced the stronger result. The negative result was better than the hoped-for positive one; the dominated middle option became a derived boundary; and here the narrowed claim is sharper than the broad one it replaced.
>
> It also closes the loop on [2026-09-21_pre-submission-rescan](2026-09-21_pre-submission-rescan.md) — that session found the problem, this one found out how far it had spread.

> [!IMPORTANT]
> **Portfolio note**
> Shows auditing a correction rather than trusting it — finding the same overclaim in four places including the abstract — and using the forced narrowing to locate a sharper, genuinely novel claim about the *shape* of a relationship rather than its existence.

---

## Before and after

| | Claim |
|---|---|
| Before | First to treat the deferral threshold as varying with the instance |
| After | The threshold's variation is **non-monotone and changes sign** — a claim about shape, absent from the deferral literature |

Final state: 11 pages · clean compile · 32 citations · 0 missing · 0 unused

---
