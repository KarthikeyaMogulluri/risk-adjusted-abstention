# Checking the dataset actually contains what the model needs

*Research journal entry — 2026-09-21. Part of the [risk-adjusted abstention](../README.md) study.*

---

> **Summary:** Before running anything, every field the cost model needs was checked against the real data rather than against the dataset's description of itself. Three of the needed fields do not exist and had to be replaced by stand-ins, which is recorded rather than hidden. With that done, the first pre-registered test ran on 249 real incidents and passed — a result that was overturned a few hours later, for reasons that only became visible because this step was done carefully.

---

> [!NOTE]
> **What this code/concept does**
> The research needs a number for each incident: how much that incident costs per second while it continues. That number is built from several measured quantities — how much traffic is failing, how many users sit behind the failing part, how bad the knock-on damage is.
>
> A public dataset of real failures was obtained to supply those quantities. This step asked the only question that matters first: **for each quantity the model needs, is there actually a column in the data that contains it?** Not "does the dataset sound like it has it", but "open the files and look".
>
> The answer was mostly yes and partly no. Three needed quantities have no counterpart in the data, so each was replaced by the closest available stand-in, and each substitution was written down as a substitution rather than quietly treated as the real thing.

> [!NOTE]
> **Why we are doing it this way**
> **Because a missing field does not announce itself.** If a quantity is absent and something plausible is used instead, every downstream number still computes. Nothing crashes. The results look complete. The substitution becomes invisible the moment it is made, and it stays invisible until a reviewer asks where a number came from — or, worse, until nobody asks and the paper is wrong in public.
>
> **Because the data was fetched directly rather than through the convenience package.** The packaged version hides the file layout behind a function call, which is exactly the layer that would have prevented this check. Downloading the raw archive meant the actual column names were visible.
>
> **Because the test was written before the data arrived.** The pass/fail condition for the first research question was fixed in advance, in writing. That is what makes a "pass" mean something — it cannot be adjusted after seeing the numbers, because it was committed to before there were numbers.

> [!NOTE]
> **How it works step by step**
> **1. Get the real thing.** The full first corpus was downloaded straight from the hosting service — 375 incident cases, about 120 MB, nothing missing. Going direct rather than through the packaged loader was deliberate: the goal was to see the files.
>
> **2. List what the model needs, then look for each one.** Every quantity in the cost equations was written out, and the data was opened to find its column. Most were present. Three were not, and each got a documented stand-in rather than a silent guess.
>
> **3. Build the map of what talks to what.** The cost of a failure depends partly on what else depends on the broken part. Rather than trying to infer that from the recorded traffic — which only shows the paths that happened to be exercised — the known structure of the two example systems was written down directly. A structure taken from the system's design is complete; one inferred from observed traffic is only as complete as the traffic.
>
> **4. Write a reader that knows the files differ.** The three systems in the corpus do not share a layout. The reader was written to detect which layout it is looking at rather than assuming one. *(This turned out to be not quite enough — see the session that followed.)*
>
> **5. Run the pre-registered test.** 249 usable incidents. One case was skipped because it contained fewer than two faulty samples, which is too few to compute anything from, and the skip is recorded.
>
> **6. Report the result as preliminary.** It passed — the spread of incident stakes covered more than nine orders of magnitude, and the resulting thresholds moved in both directions rather than one. But it was one corpus with one unbalanced weighting, and the write-up said so.

> [!NOTE]
> **Key terms defined**
> - **Corpus** — the collection of recorded real incidents used as evidence.
> - **Field / column** — one named quantity recorded for each incident.
> - **Substitution** — using an available quantity in place of a needed one that does not exist, and saying so.
> - **Stake** — how much an incident costs per unit of time while it continues.
> - **Threshold** — the confidence level above which the system should act rather than escalate to a person.
> - **Pre-registered test** — a pass/fail condition written down before the data is seen, so the result cannot be tuned after the fact.
> - **Topology** — the map of which parts of a system depend on which other parts.
> - **Static vs trace-derived** — taken from the system's design, versus inferred from traffic that happened to be recorded.

> [!WARNING]
> **Common mistakes to avoid**
> - **Trusting the dataset's description instead of its files.** Documentation describes intent. Files contain reality.
> - **Using the convenience package for a data-integrity check.** The layer that makes loading easy is the layer that hides what you need to see.
> - **Substituting silently.** A stand-in that is not labelled a stand-in becomes a fact by the second time it is read.
> - **Inferring structure from observed traffic when the real structure is available.** Traffic shows the paths that were exercised, not the paths that exist.
> - **Assuming one file layout per dataset.** Three systems, three layouts — and the assumption that layout varies only by system is what caused the bug found in the next session.
> - **Reporting a single-corpus result without the word "preliminary".** One dataset with one weighting is one data point.
> - **Dropping unusable cases without recording them.** One skipped case, named and explained, costs a line. An unexplained count mismatch costs a reviewer's trust.

> [!TIP]
> **How this connects to the bigger picture**
> This is the point where the paper stopped being algebra and started being measurement. Everything afterwards — the refutation, the replication on a second corpus, the figures, the final claim — rests on whether the quantities being measured are the quantities the equations describe.
>
> It also set up its own correction. The reader written here handled differences between systems but not differences *within* a system, and that gap produced silently wrong values on nearly a third of cases. That bug is the subject of [2026-09-21_rq1-refuted-and-why-that-is-the-result](2026-09-21_rq1-refuted-and-why-that-is-the-result.md), and it was findable only because this session had established what each number was supposed to mean.

> [!IMPORTANT]
> **Portfolio note**
> Shows the discipline of verifying that data contains what a model assumes before running the model — and of writing down three substitutions that would have been invisible and unfalsifiable if left unstated.

---

## Result as recorded at the time

```
incidents          249        stake spread   9.30 decades
tau_act spread     0.988      tau_act IQR    0.966
rises with stake   39.8%      falls          60.2%
VERDICT            PASS       (preliminary — one corpus, unbalanced weighting)
```

Skipped: `re1ob_productcatalogservice_cpu_3` — fewer than two faulty samples.

---
