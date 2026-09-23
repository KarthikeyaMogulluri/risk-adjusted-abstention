# Risk-Adjusted Abstention for Root Cause Analysis

**When an AI diagnoses a broken server, it has to decide whether to fix things
itself or wake a human. This project asks whether that decision should depend
on how expensive the outage is — and finds that on every public benchmark, it
cannot be made to.**

A complete, reproducible research study: three proved theorems, two independent
datasets, 352 real failures, and a hypothesis that its own authors refuted.

**In the vocabulary of the field:** this is a study of **risk-sensitive
selective prediction** for **LLM-assisted root cause analysis (RCA)** in
**Kubernetes** microservice deployments. It derives a per-incident
**abstention threshold** over a three-way action space from a loss function on
**SLO error-budget burn rate**, infrastructure cost and **blast radius**, all
estimated from **OpenTelemetry**-style **telemetry** rather than from
business-cost labels. It evaluates against a **perfect-information oracle**
using **cost-weighted regret**, **risk–coverage curves** and **expected
calibration error (ECE)**, on two chaos-injection **AIOps** benchmarks.

Keywords: AIOps · LLM agents · root cause analysis · selective prediction ·
learning to defer · abstention · confidence calibration · site reliability
engineering · service level objectives · error budgets · FinOps · Kubernetes ·
microservices · observability · negative results · pre-registration

> [!NOTE]
> **The manuscript is not in this repository.** It is under preparation, and an
> unsubmitted paper on a public remote can count as prior publication at some
> venues. Everything that *produces* its numbers is here, and
> `verify_paper.py` checks all 43 of them.

> [!IMPORTANT]
> **No large language model is run in the results reported here.** The agent's
> confidence signal is simulated at calibration levels reported in the
> literature; the stake side is measured from real telemetry. A complete
> harness for running a real LLM agent ships in `code/agent.py`
> ([§9](#9-the-agent-study-optional-costs-money)) — it has not been run, and
> the repository title deliberately does not claim "LLM-assisted" results.

---

## Contents

1. [The problem, in plain English](#1-the-problem-in-plain-english)
2. [What we actually did](#2-what-we-actually-did)
3. [What we found](#3-what-we-found)
4. [Why this is worth having](#4-why-this-is-worth-having)
5. [The datasets](#5-the-datasets)
6. [Install](#6-install)
7. [Run it](#7-run-it)
8. [Reading the output](#8-reading-the-output)
9. [The agent study](#9-the-agent-study-optional-costs-money)
10. [How the code fits together](#10-how-the-code-fits-together)
11. [Limitations](#11-limitations-read-this)
12. [Troubleshooting](#12-troubleshooting)
13. [Research journal](#13-research-journal)

---

## 1. The problem, in plain English

Modern web services run as dozens of small programs talking to each other
inside Kubernetes. When something breaks, an engineer has to work out *which*
program broke — the others are usually just reacting to it. That job is called
**root cause analysis**, and AI agents are increasingly doing it.

The agent produces a guess plus a **confidence score**: "it's the payment
service, I'm 80% sure." A **threshold** then decides what happens next. Above
it, the agent fixes things on its own. Below it, a human is paged.

Today that threshold is a single fixed number — the same 0.8 for every
incident a company will ever have.

**That struck us as obviously wrong.** Consider two incidents where the agent
says 80%:

| | Incident A | Incident B |
|---|---|---|
| What broke | a stale cache on an internal dashboard | the payment path, mid–sales-peak |
| Who notices | three engineers | every customer |
| Cost per minute | ~nothing | a great deal |
| Cost of a wrong automated fix | trivial | severe |

The same 80% means completely different risk. So the threshold should move with
what's at stake. **That is the hypothesis this project set out to prove.**

### The twist

Writing down the actual cost equation produced something we did not expect.
The threshold does **not** simply rise as stakes rise. Its direction *flips*,
at a boundary you can write on one line:

```
threshold rises with stake   ⟺   D / (w·Hₑ)  <  Δ⁻ / Δ⁺
                                 ↑              ↑
                    damage from a wrong     time lost when wrong
                    automated fix, vs       vs time saved when right
                    the cost of paging
                    a human
```

Read the right-hand side as *how asymmetric automation is*. Read the left as
*how much worse a bad robot is than a slow human*.

- When damage is cheap → higher stakes demand **more** confidence. Intuitive.
- When damage is expensive → higher stakes demand **less**. On an incident
  burning fast enough, waiting for a human costs more than a bad guess. The
  building is on fire; try something.

So a single fixed threshold isn't merely suboptimal — it's **wrong in both
directions at once**, and no amount of conservative tuning fixes that. That
result (Proposition 2) is proved in the write-up and verified numerically here.

Formally this is **selective prediction with a reject option** (Chow, 1970)
made **risk-sensitive**: the cost of deferring is not a constant but a measured
property of the instance. Instance-dependent deferral costs already exist in
the **learning-to-defer** literature; what is new here is deriving them from
operational telemetry, and characterising the *shape* of the resulting
threshold — which turns out to be non-monotone.

---

## 2. What we actually did

To test the hypothesis you need to know what each incident is *worth*. No
public dataset records that — nobody labels outages with dollars.

So we derive it from what a cluster already emits:

```
stake ρ  =  wasted infrastructure  +  failed requests  +  error-budget burn
            (replica-seconds ×        (rate of 5xx and    (how fast the
             cloud unit price)         slow responses)     reliability
                                                           allowance drains)
```

Plus **blast radius** — how many services a bad fix could take down — from the
service call graph.

Then we:

1. **Pre-registered** the test. The falsification condition went into the paper
   and the decision rule into code *before the data loader worked*. There was
   no way to move the goalposts afterwards.
2. Ran it on **two independent corpora** with **separately written loaders**
   that share nothing but the equations.
3. Compared against a deliberately unfair opponent: the single best fixed
   threshold, **tuned with hindsight on the test set**. Beating a badly-chosen
   constant would prove nothing.
4. Measured **cost-weighted regret** against a perfect-information oracle —
   not accuracy, because the claim is about *which* errors happen.

---

## 3. What we found

**The hypothesis is refuted.** Both corpora, same verdict.

| | RCAEval | RCA100 |
|---|---|---|
| Incidents on one side of the boundary | 100% | 100% |
| Spread of the derived threshold (IQR) | 0.056 | 0.016 |
| Derived threshold vs tuned constant | **+39.6% worse** | **+45.0% worse** |
| Pre-registered verdict | **REFUTED** | **REFUTED** |

Four findings came out of chasing why.

**① The answer is chosen, not measured.** There *is* a window where our method
wins — by up to 34%. But where that window sits is set by an exchange rate no
telemetry supplies, and **the value that rescues one dataset fails on the
other** (RCAEval wins at 10–300×, RCA100 at 300–1000×). A result whose sign you
can select is not a result.

**② On RCAEval, the best fixed policy is no gate at all.** The hindsight-tuned
optimum is τ\* = 0.000 — always act. Not "our gate loses to a better gate" but
"any gate loses to no gate."

**③ The flatness is our composition, not the data.** Failure signals span
**4–5 decades**. But infrastructure cost barely varies (benchmark clusters
don't autoscale), and when weighted comparably it contributes ~72% of the
median and *floors* the composite. Remove it and 4 decades of spread return.
This generalises: **any benchmark built by chaos-injecting a fixed-size cluster
has this floor.** It's a property of how the data was collected.

**④ Our own third action is dead weight.** We introduced *assist* (hand the
human a hypothesis) alongside *act* and *escalate*. It's dominated on **every
incident in both corpora**. We derived when it wouldn't be: above **≈\$111/hour**
of incident burn. These corpora run at **\$3.24** and **\$1.38** an hour — 34×
and 80× short. Real payment systems clear that easily, which makes it a
testable prediction rather than an excuse.

---

## 4. Why this is worth having

**If you are doing research:**

- A **pre-registration template** that works. The falsification condition, the
  decision rule, and the negative-result wording were all fixed before the
  data existed. When the result reversed, publishing it cost three text
  replacements and no argument.
- A **verification harness** (`verify_paper.py`) that recomputes all 43
  numbers the write-up claims and fails loudly if code and text diverge.
- An honest account of **two bugs that reversed a favourable result** — a
  parser that silently zeroed 30% of cases, and a degenerate cost composition.
  Both are documented where they happened.

**If you build AIOps systems:**

- A **stake model needing no business-cost labels** — it runs on telemetry any
  instrumented cluster already emits.
- **ρ\* ≈ \$111/hour**: below this, a three-way policy is pointless and you
  should just let the agent act. Checkable against your own numbers in an
  afternoon.
- Evidence that on cheap incidents, **gating destroys value**. Always-escalate
  is 21× worse than always-act here.

**If you benchmark RCA:**

- The **trivial baseline** almost nobody reports: pick the service with the
  largest anomaly. It scores **75.8% on RCAEval** and **41.7% on RCA100**. An
  agent paper that doesn't report this is hiding most of its performance.
- A concrete demonstration that benchmark collection method determines what
  can be studied on it.

---

## 5. The datasets

**Not committed to this repo** — they total ~1 GB and are fully reproducible.
Both downloaders are resumable. Licences belong to the original authors.

### RCAEval RE1 — 375 cases, ~120 MB

Fault-injection experiments on three open-source microservice demos.

| | |
|---|---|
| Systems | Online Boutique (12 svc), Sock Shop (15), Train Ticket (64) |
| Faults | cpu, memory, disk, network delay, packet loss — 5 reps each |
| Per case | `metrics.parquet` (time series), `inject_time.txt` |
| Source | HuggingFace `phamquiluan/RCAEval` |
| Paper | arXiv 2412.17015; WWW '25 Companion |

```bash
python download.py --suite RE1
```

**We use Online Boutique + Sock Shop.** Train Ticket is excluded — 64
services, and its call graph was not transcribed rather than guessed.

Two case counts appear in the outputs and both are correct:

| | Cases | Why |
|---|---|---|
| Stake analysis (`compare.py`, `verify_paper.py`) | **249** | needs ≥2 samples after injection |
| Agent study (`agent.py`) | **248** | also needs ≥2 samples *before*, to compute a shift |

> **Watch out:** the column grammar varies by *fault type*, not just by system.
> `cpu`/`mem` cases expose `_load` and `_latency`; `delay`/`disk`/`loss` expose
> `_workload` and `_latency-50/90`. A loader keyed on system silently returns
> zero throughput on a third of cases. `rcaeval_loader.py` detects per file.

### RCA100 v1.1 — 103 cases, ~62 MB lean

Chaos drills against the OpenTelemetry demo store on Alibaba Cloud ACK.
Validated by a 5,532-team competition.

| | |
|---|---|
| Modalities | metrics, logs, traces, events, alerts, **topology** |
| Per case | `task.json`, `metrics.parquet`, `topology.json` (~277 entities, 353 edges), `alerts.parquet` |
| Ground truth | `answer_key/tNNN.gt.json` — root-cause entities and fault types |
| Source | `aiops.cn` GitLab; case data mirrored on Alibaba OSS |
| Licence | CC BY-NC-SA 4.0 |
| Paper | arXiv 2606.29193 |

```bash
python download_rca100.py          # lean: 62 MB
python download_rca100.py --full   # adds traces + logs: ~3.6 GB
```

Lean skips traces and logs — 75% of the bytes, untouched by this analysis.

### Why two, and why RCA100 matters

RCAEval doesn't record everything the stake model wants. Each gap is
substituted and **declared in the write-up**; a silent substitution is a
construct-validity failure.

| Needed | RCAEval | RCA100 |
|---|---|---|
| replica counts | absent → proxied from CPU + memory | **measured** |
| per-service errors | 3–5 services → latency violations carry it | **per entity** |
| call graph | 0% traces → published static topology | **measured in-window** |

RCA100 needs **none** of them. So the replication isn't a second opinion — it
tests whether the first result was an artefact of the substitutions. It wasn't.

---

## 6. Install

Python 3.11+. No GPU, no cluster, no Kubernetes. ~1 GB disk.

```bash
git clone <your-repo-url> && cd k8s-aiops-research
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

---

## 7. Run it

### Everything, one command

```bash
cd code && python run_all.py
```

Download → gate → comparison → verification → figures, in order, stopping at
the first failure. About 20 minutes, most of it downloading.

### Just the maths (10 seconds, no data)

```bash
cd code && python run_all.py --quick
```

### Step by step

```bash
cd code
python policy.py                                       # verify the theorems
python download.py --suite RE1                         # RCAEval, ~120 MB
python download_rca100.py                              # RCA100, ~62 MB
python run_rq1.py --dataset rcaeval --root ../data     # the gate
python compare.py                                      # both corpora
python verify_paper.py                                 # all 43 claimed numbers
python figures.py                                      # four PDFs -> figures/
```

---

## 8. Reading the output

### `policy.py` — run this first

```
Proposition 1 verified: both thresholds in [0,1] on 20,000 points.
Proposition 2 verified on 20,000 points across 7 decades of stake and 8 of damage.
Both regimes present: 67.8% rising, 32.2% falling.
```

Checks the analytic derivative against a finite difference. **If Proposition 2
fails, the paper is wrong and nothing downstream matters.**

### `run_rq1.py` — the pre-registered gate

```
stake spread     1.51 decades   (need >= 1.0)
tau_act spread   0.257          (need >= 0.10)
rises / falls    100% / 0%      (need >= 5% minority)
VERDICT: REFUTED
```

The thresholds were fixed in code before the loader worked. **REFUTED is the
correct, expected result** — it is what the write-up reports.

### `verify_paper.py` — the contract

```
VERIFIED 43   MISMATCHED 0
```

Anything else means code and paper have diverged. Treat as a bug in one.

### Key terms

| Term | Meaning |
|---|---|
| **stake (ρ)** | What one second of unresolved incident costs |
| **blast radius** | Services a bad fix could break downstream |
| **error budget** | Allowed failure implied by an SLO. 99.9% → 0.1% is the budget |
| **burn rate** | How fast an incident drains that budget |
| **regret** | How much worse than a perfect-knowledge policy. 0 = oracle |
| **coverage** | Fraction of incidents handled without paging a human |
| **ECE** | How honest the confidence is. Say 70% → be right 70% of the time |
| **dominated** | An action never worth choosing, so it may as well not exist |

---

## 9. The agent study (optional, costs money)

The pipeline takes `(q, Y, ρ, D, Tₑ)`. Only `q` and `Y` — the **large
language model** agent's self-reported confidence and whether its root-cause
hypothesis was correct — are simulated in the write-up. This
replaces them with a real model. Nothing else changes, so any shift in
conclusions is attributable to the confidence signal alone.

**Estimate first — makes no API calls:**

```bash
python agent.py --estimate --reps 3
```

```
claude-haiku-4-5     $  2.22
claude-sonnet-4-5    $  6.66     1,053 calls, both corpora, 3 reps
claude-opus-4-5      $ 11.10
```

**Then:**

The agent is prompted with a deterministic per-service anomaly report and
replies through a **structured tool call** (`root_cause_service`,
`fault_type`, `confidence`, `reasoning`), so parsing is exact and the
confidence is a first-class field rather than something scraped from prose.

```bash
export ANTHROPIC_API_KEY=sk-ant-...          # Windows: set ANTHROPIC_API_KEY=...
python agent.py --corpus rca100 --limit 5    # smoke test, ~2 cents
python agent.py --corpus rca100              # full run, resumable
python agent_results.py --corpus rca100
```

> **Read the trivial baseline before the agent's score.** Picking the largest
> anomaly gets **75.8%** on RCAEval and **41.7%** on RCA100 with no model at
> all. RCAEval is nearly solved by ranking; RCA100 carries the difficulty. An
> agent that can't beat it hasn't earned its place. `agent_results.py` always
> prints both.

---

## 10. How the code fits together

```
 download.py ─┐
              ├─► data/ ──► rcaeval_loader.py ─┐
download_rca100.py          rca100_loader.py ──┤   (separate loaders,
                                               │    shared equations only)
                            topology.py ───────┤
                                               ▼
                                          stakes.py          ρ, D, Tₑ
                                          rebalance.py       λ calibration
                                               │
                                               ▼
                                          policy.py     ◄── SELF-VERIFYING
                                          Prop 1 · Prop 2 · act/assist/escalate
                                               │
                        ┌──────────────────────┼──────────────────────┐
                        ▼                      ▼                      ▼
                  run_rq1.py             evaluate.py             figures.py
                  the gate          oracle · 5 baselines        4 PDFs
                                     regret · ECE
                                           │
                        ┌──────────────────┴──────────────────┐
                        ▼                                     ▼
                  compare.py                          verify_paper.py
                  both corpora                        43 checks vs paper

  optional:  summarise.py ─► agent.py ─► agent_results.py ─► (same pipeline)
```

| File | Does |
|---|---|
| `policy.py` | The mathematics. Both thresholds, the sign flip. **Self-verifying** |
| `stakes.py` | Stake composition, Eq. 12–13, and its parameters |
| `topology.py` | Static call graphs; blast radius |
| `rcaeval_loader.py` | RCAEval (wide). Schema detected **per file** |
| `rca100_loader.py` | RCA100 (long). Independent of the above |
| `rebalance.py` | p90 calibration; simplex sweep |
| `evaluate.py` | Realised cost, oracle, five baselines, regret, ECE |
| `run_rq1.py` | The pre-registered gate |
| `compare.py` | Cross-corpus comparison |
| `verify_paper.py` | Recomputes all 43 claimed numbers |
| `figures.py` | The four figures -> `figures/` |
| `summarise.py` | Telemetry → agent context, deterministic |
| `agent.py` | The agent study |
| `agent_results.py` | Real (q, Y) → the verified pipeline |
| `run_all.py` | Everything, in order |

---

## 11. Limitations — read this

- **No live agent in the paper's results.** Confidence is simulated at
  literature-reported calibration levels; stake is measured. §9 closes this
  but has not been run.
- **RQ2 is unanswerable on public data.** Neither corpus labels severity, so
  the stake estimator is never validated against ground truth.
- **Δ±, δ±, η±, Hₑ are estimates.** ρ\* ≈ \$111/hr rests on them. They're
  swept, but the ranges are chosen too.
- **Train Ticket excluded** — 64 services, topology not transcribed rather
  than guessed.
- **Assumption 1 (anchoring) is motivated, not established.** The cited work
  shows bad decision support flips correct human judgements; it does not show
  a wrong hypothesis is slower on average than none.

---

## 12. Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `MISMATCHED > 0` in `verify_paper.py` | Code and paper diverged. Investigate — don't edit the paper to match |
| `no cases loaded` | Data not downloaded. Run the `download*.py` steps |
| `zero throughput ... schema grammar may have changed` | Deliberate hard failure. RCAEval changed its columns; fix `detect_schema` |
| `ANTHROPIC_API_KEY is not set` | Only `agent.py` needs it. Everything else runs without |
| RCA100 download stalls | `aiops.cn` GitLab is slow for answer keys. Resumable — re-run |
| `NotImplementedError` in `topology.py` | You asked for Train Ticket. Not supported by design |
| Figures look wrong after edits | `python figures.py` regenerates all four |
| Numbers change after editing a module | Stale bytecode. `rm -rf code/__pycache__` and re-run — this bit us once and produced a wrong cross-check |
| `249` vs `248` RCAEval cases | Both correct — see [the datasets](#5-the-datasets). Different window requirements |

---

## 13. Research journal

The working notes kept while the study ran are in **[`docs/`](docs/)**, in
order. They are published because the provenance is the point — the hypothesis
was pre-registered, then refuted by its own authors, and each reversal is
recorded at the moment it happened rather than reconstructed afterwards.

Three worth reading even if you skip the rest:

- **[The result reverses](docs/2026-09-21_rq1-refuted-and-why-that-is-the-result.md)**
  — a parser bug and a degenerate cost model turn a favourable result into a
  refutation.
- **[The overclaim](docs/2026-09-21_correcting-the-overclaim-properly.md)** — a
  pre-submission scan finds the paper claiming novelty a 2024 paper already
  held, in four places.
- **[The project brief](docs/PROJECT-BRIEF.txt)** — the plan written *before*
  any data was downloaded: requirements, the falsification condition, eight
  pre-killed reviewer objections, and the definition of done.

## Citing

The manuscript and its bibliography are not published here yet. Every
reference was verified against a primary source, and three corrections were
recorded that would otherwise have survived review as plausible-looking
citations — see
[the citation audit](docs/2026-09-21_verifying-every-citation.md).

Dataset credit belongs to the RCAEval and RCA100 authors — cite them directly
if you use the data.

## Licence

MIT for this code — see `LICENSE`. The datasets carry their own licences
(RCA100 is CC BY-NC-SA 4.0).
