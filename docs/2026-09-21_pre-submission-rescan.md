# The pre-submission novelty re-scan, and the three things it found

*Research journal entry — 2026-09-21. Part of the [risk-adjusted abstention](../README.md) study.*

---

> **Summary:** A second search of the literature, run deliberately just before submission rather than only at the start. It found that the paper's first contribution claimed more than it was owed, that another group had reached a structurally identical conclusion eight days earlier from a different field, and that industry practice had converged on the opposite ordering to the paper's own result — which turned out to be explainable rather than contradictory.

---

> [!NOTE]
> **What this code/concept does**
> A novelty scan asks whether the thing you are about to claim as new is actually new. It is usually done once, at the beginning, when the idea is formed.
>
> This is the second one, run at the end. The reason is simple: months pass between forming an idea and submitting it, and in a fast-moving field the literature moves during that gap. The project's own brief required this re-scan, so it could not be skipped by enthusiasm at the finish line.
>
> It found three things, and all three changed the paper.

> [!NOTE]
> **Why we are doing it this way**
> **Because the scan at the start checked a different claim.** The paper that exists at submission is not the paper that was planned. This one had turned into a negative result along the way. The original scan tested the original idea; nobody had ever checked the final one.
>
> **Because an overclaim found by a reviewer is much more expensive than one found by the author.** The same correction costs an afternoon now, or a rejection and a resubmission cycle later.
>
> **Because concurrent work is a fact to report, not a race to lose.** Another group reaching a similar conclusion independently, at almost the same time, is corroboration. Presenting it that way is both honest and stronger than hoping nobody notices.
>
> **Because evidence that appears to contradict you deserves more attention than evidence that agrees.** Industry practice pointed the opposite way to the measured result. The temptation is to not mention it. The better move was to check whether both could be true at once — and they could.

> [!NOTE]
> **How it works step by step**
> **Finding 1 — the first contribution was overclaimed.**
> The paper claimed it was first to treat the cost of handing a decision to a human as something that varies from case to case. That is not true. The established literature on learning when to defer to an expert already models costs that depend on the specific instance — one line of work from 2016, and a 2024 paper handling costs that depend on both the instance and the correct answer, under workload limits.
>
> The claim was narrowed to what is genuinely the paper's own: not that these costs vary, but that they can be **derived from operational telemetry** rather than assumed or supplied as given. That is a smaller claim and a true one.
>
> **Finding 2 — concurrent work, eight days old.**
> A preprint submitted on 13 September — eight days before this scan — reaches a structurally identical negative conclusion: that the available benchmarks lack what an abstention method needs to be evaluated. It comes from network operations rather than container-orchestration diagnosis, and it gets there by measuring the impact of each action rather than the stake of each incident.
>
> Different field, different method, same conclusion. It was added as corroboration. Two independent routes to the same negative result is a stronger claim than one.
>
> **Finding 3 — industry went the other way.**
> Through the summer of 2026, industry practice converged on offering a suggestion and escalating to a person, while withholding autonomous action. That is the **opposite** ordering to what the corpora show, where acting dominates and suggesting is never chosen.
>
> Rather than a contradiction, this is a consistency check that passes. The crossing point derived in [2026-09-21_owning-the-three-action-contradiction](2026-09-21_owning-the-three-action-contradiction.md) says the ordering flips above about $111 per hour of incident burn. Production systems plausibly sit above that; the benchmark corpora sit 34 and 80 times below it. Both observations are then correct, in different regimes — and industry's behaviour becomes weak external evidence that real systems live above the threshold.
>
> It is weak evidence and is labelled as such. Industry practice is shaped by liability and caution as well as by expected cost.
>
> **Then: write all three in, and recompile.** 32 citations, none missing, none unused, compiles clean.

> [!NOTE]
> **Key terms defined**
> - **Novelty scan** — a search to check whether a claimed contribution is already published.
> - **Overclaim** — asserting more originality than the literature supports.
> - **Learning to defer** — the research area on deciding when a model should hand a case to a human expert.
> - **Instance-dependent cost** — a cost that varies case by case rather than being one fixed number.
> - **Operational telemetry** — the measurements a running production system already emits.
> - **Concurrent work** — research published so close in time that neither group could have known about the other.
> - **Corroboration** — independent evidence pointing to the same conclusion.
> - **Regime** — a range of conditions within which a particular conclusion holds.

> [!WARNING]
> **Common mistakes to avoid**
> - **Scanning only at the start.** The literature moves, and so does your paper. The claim you submit was never checked.
> - **Skipping the re-scan because the paper feels finished.** That is exactly the feeling the rule exists to overrule.
> - **Claiming a whole idea when you own a piece of it.** "First to derive these from telemetry" survives scrutiny; "first to treat them as varying" does not.
> - **Hiding concurrent work.** Reviewers in a small field know the recent preprints. Finding it yourself and framing it as corroboration is strictly better.
> - **Ignoring evidence that points the other way.** The reconciliation turned out to be one of the more interesting paragraphs in the paper.
> - **Overstating weak external evidence.** Industry behaviour is shaped by liability as much as by cost; it is a hint, not a measurement.
> - **Assuming one edit fixes an overclaim.** It did not — the claim had spread to four places, which is the subject of [2026-09-21_correcting-the-overclaim-properly](2026-09-21_correcting-the-overclaim-properly.md).

> [!TIP]
> **How this connects to the bigger picture**
> This is the same discipline the rest of the project runs on, aimed at the paper's own novelty rather than at its numbers: check the claim against a source that is not your memory. It is the citation-verification pass of [2026-09-21_verifying-every-citation](2026-09-21_verifying-every-citation.md) applied to originality instead of attribution.
>
> It also directly caused the next session. The narrowed claim was written into one place and left contradicting itself in three others — and the repair of that turned out to produce a better pitch than the original.

> [!IMPORTANT]
> **Portfolio note**
> Demonstrates running a novelty re-scan at submission rather than only at inception, narrowing an own contribution after finding prior art, and turning both a concurrent result and apparently contradictory industry practice into supporting evidence.

---
