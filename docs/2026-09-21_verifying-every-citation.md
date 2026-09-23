# Verifying every citation, and the three that were wrong

*Research journal entry — 2026-09-21. Part of the [risk-adjusted abstention](../README.md) study.*

---

> **Summary:** All 29 bibliography entries were checked against primary sources rather than memory. Three were wrong in ways that would have passed review unnoticed: a paper attributed to the wrong first author entirely, and two recorded as preprints when both had been published with page ranges. The author placeholders are gone, seven entries now carry DOIs, and the one remaining soft spot is documented rather than hidden.

---

> [!NOTE]
> **What this code/concept does**
> A bibliography entry makes three factual claims: who wrote the thing, what it is called, and where it appeared. Any of the three can be wrong, and a wrong one is invisible to the person who wrote it, because it looks exactly like a right one.
>
> This pass checked every entry against a source that is not memory. For preprints, the arXiv programmatic interface, which returns the real author list and title as recorded by the archive. For anything with a digital object identifier, the identifier itself was resolved and the publisher's own record read back. For machine-learning conference papers, which the identifier registries index poorly, the publisher's proceedings pages. For project websites, an actual HTTP request.

> [!NOTE]
> **Why we are doing it this way**
> The paper's whole claim to credibility is that its numbers were measured rather than assumed, and that unwelcome results were reported rather than tuned away. A fabricated author list would undercut all of that for a reader in one glance, and it costs nothing to prevent.
>
> The specific risk here was known in advance and written into the bibliography's own header weeks earlier: many entries carried a marker saying the identifier was correct but the author list had not been read. That marker existed precisely so this pass could not be skipped by forgetting it was needed.
>
> The verification order was chosen by reliability, not convenience. The archive's own interface beats a search engine; a resolved identifier beats a search engine; the publisher's page beats a third-party index. A search was used only where the better sources failed.

> [!NOTE]
> **How it works step by step**
> **1. Batch the preprints.** All fifteen archive identifiers went to the archive's interface in one request, which returned real titles, full author lists, publication dates and, where the authors had recorded one, the eventual publication venue.
>
> **2. Resolve every identifier.** Each digital object identifier was fetched with a request asking for structured citation data, returning the publisher's own record of authors, venue, year and pages.
>
> **3. Handle the machine-learning venues separately.** Identifier registries index conference proceedings from that field badly: querying by title returned completely unrelated papers, including one about mass spectrometry and one about quantum mechanics. Those four were checked against the publishers' proceedings pages instead.
>
> **4. Fetch the project websites.** One responded normally, one refused a non-browser request, and one refused the connection outright. Refusing a robot is not the same as being dead, and the entries say which happened.
>
> **5. Rewrite the file from what came back**, not from what was there before, so nothing unverified could survive by inertia.
>
> **6. Check the result mechanically.** Twenty-nine entries, all unique, all cited, none missing, none orphaned, no unsubstituted placeholders, no stray non-Latin characters.

> [!NOTE]
> **Key terms defined**
> - **Bibliography entry** — one record describing a cited work: authors, title, venue, year, pages.
> - **Digital object identifier** — a permanent code for a published work that resolves to the publisher's record. The most reliable thing to check against.
> - **Content negotiation** — asking a web address to return structured data instead of a human-readable page, by stating the format you want.
> - **Preprint** — a paper posted publicly before or without formal publication. Many are later published, and the entry should then cite the published version.
> - **Orphaned entry** — a bibliography record that nothing in the paper cites. Harmless but untidy, and often a sign of a citation that was removed without cleaning up.
> - **Author list inference** — guessing who wrote something from the topic or the project. The specific failure mode this pass existed to catch.

> [!WARNING]
> **Common mistakes to avoid**
> - **Trusting a familiar-sounding author.** The worst error found was attributing a well-known system to the wrong first author, entirely from association with a research group. The real list has eighteen names and the first is not the one assumed.
> - **Citing the preprint when a published version exists.** Two entries did this. The published version has page numbers, a venue, and a permanent identifier; the preprint has none of those and signals that the citing author did not check.
> - **Trusting a title search on an identifier registry.** For machine-learning conference papers this returned unrelated work with confident-looking metadata. A near-miss result is more dangerous than no result, because it can be pasted in without a second thought.
> - **Marking a website dead because a script could not reach it.** Two of three refused programmatic requests. That is bot protection, not absence, and the distinction belongs in the entry.
> - **Leaving a placeholder because it is only in one field.** A single unverified author field is enough to make a reader wonder what else was not checked.
> - **Letting a renamed key rot.** Correcting the author meant the old key was misleading, so it was renamed — and every use of it in the paper had to be updated in the same step, or the document stops compiling.

> [!TIP]
> **How this connects to the bigger picture**
> This is the last of the project's verification passes, and it found the same class of problem as all the others: something that looked right, had never been checked, and was wrong. The novelty scan found the topic was two-thirds published. The numerical self-test would have caught a wrong derivative. The measurement audit found a parsing defect that had silently zeroed a third of the corpus. Now the bibliography.
>
> The common thread is that none of these were found by thinking harder. Each was found by building something that compares a belief against an external source, and then running it. Care is a procedure, not an attitude.

> [!IMPORTANT]
> **Portfolio note**
> Demonstrates verifying a full bibliography against primary sources rather than memory, catching a misattributed first author and two unpublished-version citations that would each have passed peer review unnoticed.

---

## What was checked, and how

| Source type | Count | Method |
|---|---|---|
| arXiv preprints | 15 | arXiv Atom API — real authors, titles, dates, journal refs |
| DOI-bearing works | 3 | doi.org content negotiation → Crossref citeproc JSON |
| ML venue papers | 4 | Publisher proceedings pages (Crossref returned unrelated work) |
| Classics with DOI | 2 | Crossref |
| Books | 2 | Not independently re-checked — flagged in the header |
| Project websites | 3 | Direct HTTP fetch |

## The three that were wrong

**1. Wrong first author, and wrong publication status.**
Recorded as *"Ahmed et al.", arXiv preprint*. It is **Yinfang Chen and 17 others**, published at **EuroSys '24**, pages 674–688, DOI `10.1145/3627703.3629553`. The key was renamed `ahmed2023` → `chen2024rcacopilot` and both uses in the paper updated.

**2. Published, recorded as a preprint.**
`stalled2026` — actually IEEE/ACM 3rd Int. Conf. on AI Foundation Models and Software Engineering, **pages 172–183**, DOI `10.1145/3793655.3793732`.

**3. Published, venue buried in a free-text note.**
`rcaeval` — **WWW '25 Companion, pages 777–780**, DOI `10.1145/3701716.3715290`.

## Final state

```
entries      : 29   (all unique)
cited        : 29   (0 missing, 0 orphaned)
with DOI     :  7
placeholders :  0
non-ASCII    :  0   (Michał escaped as Micha{\l})
```

## Documented soft spots, not hidden

- **sre2016 / srewb2018** — standard O'Reilly volumes, editor lists from the books. Not independently re-checked.
- **opencost** — opencost.io refused a programmatic connection. The project is live; the fetch was blocked.
- **focus** — focus.finops.org returns 403 to non-browser agents. Confirm the exact spec version before submitting.

---
