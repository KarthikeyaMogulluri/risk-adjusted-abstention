# RCA100 replicates the refutation — and kills the salvage

*Research journal entry — 2026-09-21. Part of the [risk-adjusted abstention](../README.md) study.*

---

> **Summary:** The second dataset arrived and independently confirmed the refutation: 103 cases, a completely different collection method, none of the three substitutions the first dataset forced — and the same verdict, with the derived threshold losing by 45%. Worse for the hypothesis, the one consolation that survived the first refutation is now gone too: the window in which the method wins sits in a different place on each dataset, so no single parameter value rescues both.

---

> [!NOTE]
> **What this code/concept does**
> A second, unrelated collection of real Kubernetes failures was loaded and put through exactly the same analysis as the first, to find out whether the earlier negative result was real or an artefact of how the first dataset had to be read.
>
> The first dataset forced three compromises, because it simply did not record some things the method needs. It had no count of how many copies of each service were running, so that cost had to be guessed from processor and memory use. It recorded errors for only a handful of services out of a dozen or sixty. And it had no record of which services call which, so a published architecture diagram had to stand in.
>
> The second dataset records all three directly. That makes it not merely a second opinion but a test of whether the first answer was distorted by the compromises.

> [!NOTE]
> **Why we are doing it this way**
> The project brief fixed the rule before any data existed: *one dataset is an artefact, two is a finding*. Had the second dataset disagreed, the honest conclusion would have been that the first result was a property of RCAEval's limitations rather than of incident populations, and the paper would have said so.
>
> It agreed. That matters far more than it would have if the two datasets were similar, because almost nothing is shared between them. Different system, different cloud, different fault-injection method, different file layout, a separately written loader, and no shared substitutions. The only thing in common is the stake equations under test. When two measurements that share only the hypothesis agree, the hypothesis is what is being measured.

> [!NOTE]
> **How it works step by step**
> **1. Find the data.** The second dataset's repository API returns "not found", so the file tree cannot be listed. Raw file paths still resolve, and the case data turned out to be mirrored on a cloud object store that is far faster. The answer keys exist only in the repository.
>
> **2. Download only what is used.** A full case is about 35 megabytes, of which 26 are request traces the stake model never opens. Taking only the metrics, topology, alerts and task description reduced 3.6 gigabytes to 62 megabytes and lost nothing the analysis touches.
>
> **3. Write a separate loader.** The first dataset is wide — one column per service and measurement. The second is long — one row per service, measurement and timestamp. Nothing could be reused except the equations, which is exactly the property that makes the replication meaningful.
>
> **4. Compute the same quantities**, this time without substitutions: real replica counts, real per-service error counts, real measured call graph.
>
> **5. Run the same pre-registered gate.** It refuses again, and by a wider margin.
>
> **6. Check whether the escape hatch survives.** The first refutation left one consolation: there existed a range of parameter settings where the method did win. Sweeping the same range on the second dataset shows the winning range sits somewhere else. No single setting works for both.

> [!NOTE]
> **Key terms defined**
> - **Replication** — repeating a measurement on independent data to see whether the result was real or particular to the first source.
> - **Wide vs long format** — wide puts each measurement in its own column; long puts each measurement in its own row with a name column. Completely different parsing.
> - **Chaos drill** — deliberately injecting failures into a running system to produce labelled incidents.
> - **Substitution** — using an available quantity in place of the one the model actually wants, because the wanted one is not recorded.
> - **Blast radius** — how many services a fault can reach downstream.
> - **Burn rate** — how fast an incident consumes its allowance of failure.
> - **Dominated action** — an option that is never the best choice under any input, so it may as well not exist.
> - **Object store mirror** — a copy of a dataset served from bulk cloud storage rather than a code repository, usually much faster.

> [!WARNING]
> **Common mistakes to avoid**
> - **Treating a second dataset as confirmation shopping.** The value of the replication comes entirely from having fixed the decision rule beforehand. A second dataset examined after the fact, with freedom to adjust, confirms nothing.
> - **Downloading everything because it is there.** Traces were 75% of the corpus by size and are untouched by this analysis. Taking them would have cost hours for nothing.
> - **Reusing the first loader.** Sharing parsing code between the two datasets would have shared its bugs, and the whole point was to test whether the first answer survived a completely separate reading.
> - **Reporting the winning window without checking it transfers.** It does not. Reporting "there exists a setting where the method wins" while knowing the setting differs per dataset would be technically true and substantively misleading.
> - **Quietly dropping the three-action claim.** At the balanced composition assist is dominated on 100% of incidents in both corpora. That contradicts a stated contribution and belongs in the results, not in a footnote.

> [!TIP]
> **How this connects to the bigger picture**
> This closes the empirical arc of the project. The novelty scan cut the original brief by two thirds; the loss-function derivation strengthened the claim; the sensitivity sweep refuted it; the replication confirmed the refutation and removed the last escape route.
>
> Each of those reversals came from an instrument built before there was anything at stake in its design — the scan before the topic was chosen, the gate before the loader worked, the second-dataset rule before any data existed. That ordering is the entire reason the project can report an unwelcome result without argument.
>
> What remains is a genuine contribution of a different shape than intended: proven mathematics whose practical reach is, on every benchmark available, determined by a constant that no telemetry supplies.

> [!IMPORTANT]
> **Portfolio note**
> Demonstrates independently replicating an unwelcome finding on a second dataset chosen precisely because it removes the compromises of the first, and reporting that the one remaining salvage does not transfer between them.

---

## Structural comparison

| | RCAEval RE1 | RCA100 |
|---|---|---|
| Cases | 249 | 103 |
| Format | wide | long |
| Replica counts | absent — proxied | **measured** |
| Error signal | 3–5 services + latency | **per entity** |
| Call graph | static published | **measured in-window** |
| Cases with zero burn | 36.5% | 1.0% |
| Blast radius range | 0–9 | 0–68 |
| Infrastructure spread | 5.6× | **1.07×** |

## The gate, on both

| | n | decades | τ IQR | rises | hindsight | derived | Δ | verdict |
|---|---|---|---|---|---|---|---|---|
| RCAEval RE1 | 249 | 1.51 | 0.056 | 100% | 0.0727 | 0.1015 | +39.6% | **REFUTED** |
| RCA100 | 103 | 0.56 | 0.016 | 100% | 0.0172 | 0.0250 | +45.0% | **REFUTED** |

## The salvage does not transfer

| boost | RCAEval Δ | RCA100 Δ |
|---|---|---|
| 1 | +39.6% | +45.0% |
| 3 | +8.4% | +46.8% |
| 10 | **−6.5%** | +42.0% |
| 30 | **−34.0%** | +22.5% |
| 100 | **−26.1%** | +17.7% |
| 300 | **−8.7%** | **−9.5%** |
| 1000 | +0.1% | **−4.4%** |
| 10000 | +5.5% | +28.7% |

RCAEval wins at 10–300×. RCA100 wins at 300–1000×. **No single λ works for both.**

## Three findings beyond the refutation

1. **Infrastructure cost carries no variance in benchmark data** — 1.07× across RCA100. Chaos-drill benchmarks hold cluster size fixed, so a composite stake cannot be composite on such data regardless of weighting.
2. **Assist is dominated on 100% of incidents in both corpora** at the balanced composition (vs 25.7% at the initial unbalanced weighting, 35–39% synthetic). Where stake is small relative to human cost, τ_assist → η⁻/(η⁺+η⁻) while τ_act → 0. The three-action contribution collapses to two throughout the measured regime.
3. **Direct error measurement changes the failure picture entirely** — zero-burn cases fall from 36.5% to 1.0% when errors are recorded per entity rather than inferred from latency.

---
