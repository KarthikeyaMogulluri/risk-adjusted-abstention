# Complete Guide

Everything in this project, top to bottom. The [README](README.md) orients you;
this is the reference. Nothing here assumes you have read the paper.

---

## Contents

1. [Mental model — what the system actually does](#1-mental-model)
2. [Prerequisites](#2-prerequisites)
3. [Install, step by step](#3-install-step-by-step)
4. [The datasets, in full](#4-the-datasets-in-full)
5. [Command reference — every script, every flag](#5-command-reference)
6. [Module reference — every file](#6-module-reference)
7. [The mathematics](#7-the-mathematics)
8. [Every parameter](#8-every-parameter)
9. [Output reference — what each number means](#9-output-reference)
10. [Extending this work](#10-extending-this-work)
11. [Troubleshooting](#11-troubleshooting)
12. [Glossary](#12-glossary)
13. [FAQ](#13-faq)
14. [Complete file manifest](#14-complete-file-manifest)
14. [Complete file manifest](#14-complete-file-manifest)

---

## 1. Mental model

One sentence: **an agent diagnoses a broken Kubernetes service, and this code
decides whether it should be allowed to act on that diagnosis.**

The pipeline has two halves that meet at one point.

```
  TELEMETRY HALF                          CONFIDENCE HALF
  ──────────────                          ───────────────
  benchmark metrics                       agent says "it's the payment
         │                                 service, I'm 80% sure"
         ▼                                         │
  per-incident stake ρ                             │
  (what a second of this                           │
   outage costs)                                   │
         │                                         │
         └──────────────┬──────────────────────────┘
                        ▼
              τ = f(ρ, D, w·Hₑ, Δ±)
              the threshold, DERIVED not chosen
                        │
          ┌─────────────┼─────────────┐
          ▼             ▼             ▼
        ACT          ASSIST       ESCALATE
    fix it myself  give human a  wake human,
                   hypothesis    no hypothesis
```

**The research question:** should τ move with ρ? Everyone currently uses a
fixed τ. We derived what τ *should* be and tested whether deriving it helps.

**The answer: no, on every public benchmark.** Not because the idea is wrong —
the mathematics holds — but because benchmark incidents don't differ enough in
stake for a varying threshold to have anything to vary over. Section 4
explains why that is a property of how benchmarks are built.

**What you can run:** everything except the agent half, which needs an API
key. The telemetry half is fully reproducible from two public datasets.

---

## 2. Prerequisites

| | Requirement | Notes |
|---|---|---|
| Python | **3.11 or 3.12** | 3.10 untested. CI runs both supported versions |
| Disk | **~1 GB** | RCAEval 120 MB + RCA100 62 MB + working room |
| RAM | 8 GB comfortable | pandas over ~90k-row frames |
| Network | yes, for downloads | HuggingFace + Alibaba OSS |
| GPU | **not needed** | no training happens anywhere |
| Kubernetes | **not needed** | no cluster is ever deployed |
| LaTeX | only to build the paper | the paper is not in this repo |
| API key | only for `agent.py` | everything else runs without |

Six Python packages: `numpy pandas pyarrow scipy matplotlib requests`, plus
`anthropic` for the optional agent study.

---

## 3. Install, step by step

**Step 1 — clone**

```bash
git clone https://github.com/KarthikeyaMogulluri/risk-adjusted-abstention
cd risk-adjusted-abstention
```

**Step 2 — virtual environment**

```bash
python -m venv .venv
```

```bash
source .venv/bin/activate          # Windows PowerShell: .venv\Scripts\Activate.ps1
```

**Step 3 — dependencies**

```bash
pip install -r requirements.txt
```

**Step 4 — verify before anything else.** This needs no data and takes
seconds:

```bash
cd code && python policy.py
```

Expect exactly this shape:

```
Proposition 1 verified: both thresholds in [0,1] on 20,000 points.
tau_act spans [0.000, 1.000] -- a fixed constant cannot cover this.
Proposition 2 verified on 20,000 points across 7 decades of stake and 8 of damage.
Both regimes present: 67.8% rising, 32.2% falling.
Ordering tau_assist <= tau_act violated on 35.23% of points.
All analytic claims hold. Safe to build the evaluation on them.
```

> **If Proposition 2 fails here, stop.** The entire paper rests on it. A
> failure means either the code or the mathematics is wrong, and nothing
> downstream is meaningful until that is resolved.

**Step 5 — the rest**

```bash
python run_all.py
```

---

## 4. The datasets, in full

Three public corpora were examined. **Two are usable; the third is not, and
why it is not became a finding.**

### 4.1 RCAEval RE1 — primary

| | |
|---|---|
| Cases downloaded | **375** |
| Cases used for stake | **249** (Online Boutique + Sock Shop) |
| Cases used for agent study | **248** |
| Size | ~120 MB |
| Source | HuggingFace `phamquiluan/RCAEval` |
| Paper | arXiv 2412.17015 · WWW '25 Companion |
| Systems | Online Boutique (12 svc), Sock Shop (15), Train Ticket (64) |
| Faults | cpu, memory, disk, network delay, packet loss — 5 repetitions each |

**Per case:** `metrics.parquet` (wide format, one column per service-metric),
`inject_time.txt` (unix seconds).

**Why two case counts.** The stake analysis needs ≥2 samples *after*
injection; the agent study also needs ≥2 *before*, to compute a shift. Both
numbers are correct in their own context.

**Train Ticket is excluded.** 64 services, and its call graph was not
transcribed rather than guessed. `topology.py` raises rather than invent it.

> ⚠️ **The schema trap.** RCAEval's column grammar varies by *fault type*, not
> just by system. Online Boutique `cpu`/`mem` cases expose `_load` and
> `_latency`; its `delay`/`disk`/`loss` cases expose `_workload` and
> `_latency-50`/`_latency-90`. A loader keyed on system silently returns zero
> throughput on 30% of cases, which zeroes the error ratio and the burn rate.
> This bug produced a false positive result that stood for a day.
> `rcaeval_loader.detect_schema()` detects per file and raises on zero
> throughput rather than returning it.

```bash
python download.py --suite RE1
```

### 4.2 RCA100 v1.1 — the replication

| | |
|---|---|
| Cases | **103** |
| Size (lean) | ~62 MB — full corpus is ~3.6 GB |
| Source | `aiops.cn` GitLab; case data mirrored on Alibaba OSS |
| Paper | arXiv 2606.29193 |
| Licence | **CC BY-NC-SA 4.0** |
| System | OpenTelemetry demo store on Alibaba Cloud ACK |
| Collection | chaos drills, validated by a 5,532-team competition |

**Per case:** `task.json` (alert window, entity), `metrics.parquet` (**long
format** — one row per entity/metric/timestamp), `topology.json` (~277
entities, ~353 edges), `alerts.parquet`, `events.parquet`, plus
`answer_key/tNNN.gt.json` with root-cause entities and fault types.

**Lean download skips traces and logs** — 75% of the bytes, never opened by
this analysis. `--full` fetches them.

> ⚠️ **Ground truth spans three entity kinds**: 83 service, **17 node**, 3 pod.
> The node-level ones (`cn-hongkong.10.0.1.69`) are invisible unless node
> metrics are included, which caps achievable accuracy at 83.5% for reasons
> unrelated to reasoning. `summarise.py`'s `M_MAP` includes
> `node_cpu_usage_rate`, `node_memory_usage_rate`, `node_disk_usage_rate` and
> `node_ready_status` for exactly this reason.

```bash
python download_rca100.py          # lean
python download_rca100.py --full   # + traces and logs
```

### 4.3 Cloud-OpsBench — examined and rejected

| | |
|---|---|
| Cases | 754 (Online Boutique 550, Train Ticket 204) |
| Fault types | 57, across 12 system/category groups |
| Source | HuggingFace `LLM4Ops/Cloud-OpsBench` |
| Paper | arXiv 2603.00468 |
| Size | 3.83 GB |

**It cannot support the stake model.** Cloud-OpsBench exposes a fixed
ten-tool diagnostic interface:

```
GetResources · DescribeResource · GetAlerts · GetErrorLogs
GetServiceDependencies · CheckNodeServiceStatus · CheckServiceConnectivity
GetAppYAML · GetClusterConfiguration · ListCodeFiles
```

There is **no metrics tool**. Across admission, performance, infrastructure
and scheduling cases, `latency`, `throughput`, `qps` and `duration_seconds`
appear **zero times**. Two of the three stake components cannot be computed.

**But measuring it changed the paper's claim.** On a stratified 48-case
sample:

| | within-system replicas | unready pods |
|---|---|---|
| Online Boutique | 2.70× (CV 0.36) | 0–30, **CV 3.03** |
| Train Ticket | 1.52× (CV 0.21) | 0–14, **CV 2.98** |

Unready pods are structured by fault class — infrastructure faults mean 10,
scheduling and startup 2, the other five classes zero. **Cluster state is
dynamic here**, so the infrastructure floor that drove the refutation on the
other two corpora is *not* universal.

```bash
python cloudops_probe.py --sample 48
```

### 4.4 Why three, and what each is missing

| | RCAEval | RCA100 | Cloud-OpsBench |
|---|---|---|---|
| Traffic / error telemetry | partial | ✓ | **—** |
| Replica counts | — | ✓ | ✓ |
| Cluster state varies | — | — | **✓** |
| Call graph | static | ✓ | ✓ |
| **Usable for stake** | degraded | ✓ | **no** |

**No public benchmark carries both cluster dynamics and traffic telemetry** —
which is exactly what evaluating a stake-dependent threshold requires. That is
the sharpest form of this project's negative finding.

RCAEval forces three substitutions, each **declared, never silent**:

| Wanted | RCAEval | RCA100 |
|---|---|---|
| replica counts | absent → CPU + memory proxy | **measured** |
| per-service errors | 3–5 services → latency violations | **per entity** |
| call graph | 0% traces → published static topology | **measured in-window** |

RCA100 needs none of them, which makes the replication a test of whether the
first result was an artefact of the substitutions. It was not.

---

## 5. Command reference

### Everything at once

```bash
cd code && python run_all.py
```

| Flag | Effect |
|---|---|
| `--quick` | propositions + paper verification only; **no data needed**, ~10 s |
| `--skip-download` | assume data is already present |

Runs in order, stopping at the first failure: propositions → download →
gate → comparison → verification → figures.

### Data acquisition

```bash
python download.py --suite RE1
```

| Flag | Default | Effect |
|---|---|---|
| `--suite` | `RE1` | `RE1`, `RE2` or `RE3` |
| `--workers` | 12 | parallel downloads |
| `--optional` | off | also try `traces.csv` / `logs.csv` |
| `--limit` | 0 | cap cases, for testing |

```bash
python download_rca100.py
```

| Flag | Default | Effect |
|---|---|---|
| `--full` | off | add traces + logs (~3.6 GB instead of 62 MB) |
| `--workers` | 8 | parallel downloads |

Both are **resumable** — re-run after an interruption and they skip what
exists.

### Analysis

| Command | What it does |
|---|---|
| `python policy.py` | Verify Propositions 1 and 2. No data. **Run first** |
| `python topology.py` | Verify call-graph integrity and blast radii |
| `python run_rq1.py --dataset rcaeval --root ../data` | The pre-registered gate |
| `python compare.py` | Cross-corpus comparison, all sweeps |
| `python rebalance.py` | λ calibration + simplex sweep |
| `python verify_paper.py` | Recompute all 43 claimed numbers |
| `python figures.py` | Four vector PDFs → `figures/` |
| `python cloudops_probe.py --sample 48` | Cloud-OpsBench field verification |

`run_rq1.py` takes `--dataset {rcaeval,rca100}` and `--root`.
`cloudops_probe.py` takes `--sample` and `--workers`.

### Agent study

```bash
python agent.py --estimate --reps 3     # no API calls
```

| Flag | Default | Effect |
|---|---|---|
| `--corpus` | `rca100` | `rcaeval` or `rca100` |
| `--model` | `claude-sonnet-4-5` | any Claude model id |
| `--limit` | 0 | cap cases — use `5` for a smoke test |
| `--rep` | 1 | repetition index; separate output file |
| `--reps` | 1 | repetitions to price, `--estimate` only |
| `--estimate` | off | print tokens and cost, make no calls |

```bash
python summarise.py --corpus rca100 --limit 2   # inspect agent context
python summarise.py --build                     # cache all summaries
python agent_results.py --corpus rca100         # real (q,Y) → the pipeline
```

---

## 6. Module reference

### Core — the mathematics

**`policy.py`** — the only place the paper's mathematics lives. **Self-verifying.**

| Function | Purpose |
|---|---|
| `tau_act(rho, D, p)` | Eq. 7 — confidence above which acting beats escalating |
| `tau_assist(rho, p)` | Eq. 8 — same for assisting. No `D` term |
| `dtau_dstake_sign(D, p)` | Eq. 10 — sign of ∂τ/∂ρ. Independent of ρ |
| `straddles_boundary(D, p)` | RQ1's gate: fraction on each side |
| `derived_policy(q, rho, D, p)` | The three-way policy + diagnostics |
| `fixed_policy(q, tau, ...)` | The baseline: one constant for everything |
| `boundary_ratio`, `automation_asymmetry` | The two sides of Eq. 10 |

**`stakes.py`** — stake composition (Eq. 12–13) and `StakeParams`.
`infra_rate`, `failed_request_rate`, `burn_rate`, `compose_stake`,
`collateral_damage`.

**`topology.py`** — static call graphs. `downstream(system, service)` returns
transitively reachable services; `blast_radius` counts them. Online Boutique
and Sock Shop encoded; **Train Ticket deliberately raises.**

### Data loaders — independent by design

**`rcaeval_loader.py`** — wide format. `detect_schema(cols)` picks the
throughput and latency families **per file**. `load_case`, `build_dataset`.

**`rca100_loader.py`** — long format. Shares nothing with the above but the
stake equations, which is what makes the replication meaningful. Has its own
`blast_radius` using the measured in-window graph.

**`download.py`**, **`download_rca100.py`** — resumable acquisition.

**`probe_rca100.py`** — a one-off reachability probe, kept for provenance.
RCA100's GitLab API returns 404 so the repository tree cannot be enumerated;
this script established that raw file paths *do* resolve and that case data is
mirrored on Alibaba OSS, which is what `download_rca100.py` relies on. Not
part of the pipeline; run it only if the hosting changes.

**`cloudops_probe.py`** — field verification for the rejected third corpus.
Downloads a stratified sample, parses replica counts from `kubectl get pods`
output in the tool cache, and reports whether the infrastructure floor
appears. `--sample`, `--workers`.

### Evaluation

**`evaluate.py`** — `realised_cost` (Eq. 4–6), `oracle_cost`,
`regret`, `tune_fixed_threshold` (the hindsight baseline),
`all_baselines`, `coverage`, `expected_calibration_error`,
`risk_coverage_curve`, `stake_decile_masks`, `simulate_confidence`.

**`rebalance.py`** — `calibrate` (p90 equalisation), `compose`, `simplex`.

**`run_rq1.py`** — the pre-registered gate, with thresholds fixed in code.

**`compare.py`**, **`verify_paper.py`**, **`figures.py`**, **`run_all.py`**.

### Agent study

**`summarise.py`** — deterministic telemetry → agent context. No model
involved, so context is reproducible from data alone and cacheable.
**`agent.py`** — structured tool-call runner, resumable, with cost estimator.
**`agent_results.py`** — bridges real `(q, Y)` into the verified pipeline.

---

## 7. The mathematics

### Notation

| Symbol | Meaning | Unit |
|---|---|---|
| `q` | agent confidence | [0,1] |
| `Y` | was the hypothesis right | {0,1} |
| `ρ` | **stake** — cost per second unresolved | USD/s |
| `D` | collateral damage of a wrong autonomous action | USD |
| `w` | engineer cost rate | USD/s |
| `Hₑ` | engineer-seconds under escalate | s |
| `Tₑ` | MTTR with evidence but no hypothesis | s |
| `Δ⁺` | seconds **saved** by a correct act | s |
| `Δ⁻` | seconds **lost** by a wrong act | s |
| `δ±` | the assist analogues | s |
| `η±` | engineer-second deltas for assist | s |

### Stake, Eq. 12

```
ρ = ρ_infra + λ_exp · r_fail + λ_slo · b
```

`ρ_infra` = replica-seconds × unit price (OpenCost model) · `r_fail` =
errors + latency-objective violations · `b` = error ratio ÷ (1 − SLO target).

### Collateral damage, Eq. 13

```
D = κ · |downstream(i)| · ρ̄
```

A **level**, not a rate — it does not scale with duration. That asymmetry
against ρ, which does, is what produces the sign flip.

### Proposition 1 — the thresholds

```
τ_act    = (ρΔ⁻ + D) / (ρ(Δ⁺ + Δ⁻) + wHₑ + D)

τ_assist = (ρδ⁻ + wη⁻) / (ρ(δ⁺ + δ⁻) + w(η⁺ + η⁻))
```

Both provably in [0,1]. **No `D` in `τ_assist`** — a human reviews the
hypothesis before anything changes, so assisting causes no collateral damage.

### Proposition 2 — the sign flip

```
∂τ_act/∂ρ > 0   ⟺   D/(w·Hₑ)  <  Δ⁻/Δ⁺
```

All ρ terms cancel. Left side: damage relative to the cost of paging a human.
Right side: the asymmetry of automation.

- Damage cheap → higher stakes demand **more** confidence
- Damage expensive → higher stakes demand **less**; waiting costs more than a
  bad guess

**A single constant is therefore wrong in both directions at once.**

### Proposition 3 — rank invariance

Incident ordering by ρ is invariant to a common scaling of all λ. The absolute
price level is immaterial; only relative weighting matters.

### The policy

```
q ≥ τ_act              → ACT
τ_assist ≤ q < τ_act   → ASSIST
q < τ_assist           → ESCALATE
```

`τ_assist ≤ τ_act` is **not guaranteed**. Where it fails, assist is dominated.
Reported, never suppressed.

---

## 8. Every parameter

### `CostParams` — `policy.py`

| Parameter | Default | Meaning |
|---|---|---|
| `delta_plus_act` | 300 s | seconds saved by a correct automated fix |
| `delta_minus_act` | 1800 s | seconds lost by a wrong one |
| `delta_plus_assist` | 240 s | saved by a correct hypothesis given to a human |
| `delta_minus_assist` | 420 s | lost to anchoring on a wrong one |
| `H_e` | 2700 s | engineer time under escalate (45 min) |
| `eta_plus` | 900 s | engineer-seconds saved when the hypothesis is right |
| `eta_minus` | 600 s | wasted when it is wrong |
| `w` | 0.0167 USD/s | engineer cost rate (≈$60/hr) |

**None of these is measured.** No benchmark records how long a human took.
They are anchored to published incident-management figures and swept. The
`delta_minus_act/delta_plus_act` ratio of 6× is anchored on the finding that
mis-triage causes up to 10× delay.

### `StakeParams` — `stakes.py`

| Parameter | Default | Meaning |
|---|---|---|
| `lambda_exp` | 0.01 USD/req | value of a failed request |
| `lambda_slo` | 1000 USD | value of a unit of error budget |
| `kappa` | 60 s | extra outage seconds per downstream service |
| `slo_availability` | 0.999 | **uniform across every service** |
| `slo_latency_ms` | 500 | the latency objective |
| `node_usd_per_hour` | 0.192 | published on-demand rate |
| `pods_per_node` | 16 | for the OpenCost division |

> **The uniform SLO is the neutrality defence.** Choosing per-service targets
> would let the analyst manufacture the variance the hypothesis needs. Fixing
> them identically means all variance comes from the data. **Do not change
> this to a per-service value.**

### Sweep ranges

| Parameter | Range |
|---|---|
| `lambda_exp`, `lambda_slo` | 4 decades each |
| `kappa` | 3 decades |
| `Δ⁻/Δ⁺` | 1× – 20× |
| `δ⁻/δ⁺` | 0.5× – 10× |
| `H_e`, `η±` | ±1 decade |

---

## 9. Output reference

### `run_rq1.py`

```
stake spread     1.51 decades   (need >= 1.0)
tau_act spread   0.257          (need >= 0.10)
rises / falls    100% / 0%      (need >= 5% minority)
VERDICT: REFUTED
```

Thresholds were fixed in code **before the loader worked**. **REFUTED is the
expected, correct result.**

### `verify_paper.py`

```
VERIFIED 43   MISMATCHED 0
```

Anything else means code and paper diverged. Investigate — do not edit the
paper to match.

### The headline numbers

| | RCAEval | RCA100 |
|---|---|---|
| Cases | 249 | 103 |
| Stake spread | 1.51 dec | 0.56 dec |
| τ_act IQR | 0.056 | 0.016 |
| Rises with stake | 100% | 100% |
| Always act | 0.0727 | 0.0250 |
| Always escalate | 1.5350 | 1.7077 |
| **Hindsight-tuned** | **0.0727** (τ\*=0.000) | **0.0172** (τ\*=0.333) |
| **Derived (ours)** | 0.1015 | 0.0250 |
| **Δ vs tuned** | **+39.6%** | **+45.0%** |
| ECE | 0.070 | 0.097 |
| Ordering violated | 100% | 100% |

**τ\* = 0.000 on RCAEval means the best fixed policy is no gate at all.** Not
"our gate loses to a better gate" — *any* gate loses to no gate.

### ρ\* — when the third action earns its place

```
ρ* ≈ 0.031 USD/s  =  $111.30 / hour
```

| | Median stake | Per hour | Shortfall |
|---|---|---|---|
| RCAEval | 9.0e-4 | **$3.24** | 34× |
| RCA100 | 3.8e-4 | **$1.38** | 80× |

### Trivial baselines — read these first

| Corpus | rank-1 (no model) |
|---|---|
| RCAEval | **75.8%** |
| RCA100 | **41.7%** |

RCAEval is three-quarters solved by picking the largest anomaly. **An agent
that cannot beat this has not earned its place.**

### Agent study cost

```
claude-haiku-4-5     $  2.22
claude-sonnet-4-5    $  6.66     1,053 calls, both corpora, 3 reps
claude-opus-4-5      $ 11.10
```

---

## 10. Extending this work

### Add a fourth dataset

1. **Field-verify first.** Confirm it has: per-service metrics, replica or pod
   counts, a call graph, ground-truth labels. Cloud-OpsBench failed this check
   and saved a 3.8 GB download.
2. Write a **separate loader**. Do not reuse an existing one — shared parsing
   shares bugs, and independence is what makes replication meaningful.
3. Return `(rho, D, T_e, df)` with columns `rho_infra, r_fail, burn, blast,
   T_faulty`.
4. Add it to `compare.py` and `verify_paper.py`.

### Change the cost model

Edit `CostParams` in `policy.py`. **Then re-run `python policy.py`** — the
propositions are verified against your parameters, not the defaults. If
Proposition 2 fails, your parameters are outside the model's valid range.

### Use a different agent

`agent.py`'s `TOOL` schema and `SYSTEM` prompt are the interface. Any model
with structured output works — produce the same JSONL and `agent_results.py`
consumes it unchanged.

### Add a system to the topology

Add a dict to `topology.py` mapping service → direct dependencies, register it
in `GRAPHS`, add it to `SUPPORTED`. `_selftest()` asserts every edge target is
a declared node. **Do not guess a topology** — Train Ticket is unsupported for
exactly this reason.

---

## 11. Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `MISMATCHED > 0` in `verify_paper.py` | Code and paper diverged. Investigate; don't edit the paper to match |
| `no cases loaded` | Data not downloaded. Run the `download*.py` steps |
| `zero throughput ... schema grammar may have changed` | **Deliberate hard failure.** RCAEval changed its columns; fix `detect_schema` |
| `ANTHROPIC_API_KEY is not set` | Only `agent.py` needs it. Everything else runs without |
| RCA100 download stalls | `aiops.cn` GitLab is slow for answer keys. Resumable — re-run |
| `NotImplementedError` in `topology.py` | You asked for Train Ticket. Unsupported by design |
| Numbers change after editing a module | **Stale bytecode.** `rm -rf code/__pycache__` and re-run. This once produced a wrong cross-check |
| `249` vs `248` RCAEval cases | Both correct — different window requirements. See §4.1 |
| Figures look wrong after edits | `python figures.py` regenerates all four |
| Proposition 2 fails after parameter change | Your parameters are outside the model's valid range |
| Unicode errors on Windows | `PYTHONIOENCODING=utf-8` before the command |

---

## 12. Glossary

| Term | Meaning |
|---|---|
| **Abstention** | A model declining to answer rather than guessing |
| **Selective prediction** | Prediction with a reject option. Trades coverage for accuracy |
| **Learning to defer** | Selective prediction where a human handles what the model declines |
| **Stake (ρ)** | What one second of unresolved incident costs |
| **Blast radius** | Services a bad fix could break downstream |
| **SLO** | Service Level Objective — a promise like "99.9% of requests succeed" |
| **Error budget** | The failure the SLO allows. At 99.9%, the budget is 0.1% |
| **Burn rate** | How fast an incident drains that budget |
| **Regret** | How much worse than a perfect-knowledge policy. Zero = oracle |
| **Oracle** | A policy that knows the outcome. Upper bound, never achievable |
| **Coverage** | Fraction of incidents handled without paging a human |
| **ECE** | Expected Calibration Error. Say 70%, be right 70% of the time |
| **Dominated action** | Never the best choice, so it may as well not exist |
| **Replica-seconds** | Pods × seconds running. The unit cloud cost is billed in |
| **Chaos injection** | Deliberately breaking a running system to produce labelled incidents |
| **Pre-registration** | Fixing the hypothesis and decision rule before seeing data |
| **Hindsight-tuned baseline** | The best constant, chosen by looking at the answers. Deliberately unfair |

---

## 13. FAQ

**Is the paper here?**
No. It is unsubmitted, and an unsubmitted paper on a public remote can count
as prior publication at some venues. All the code that produces its numbers is
here, and `verify_paper.py` checks all 43.

**Why is the result negative?**
Because that is what the data said. The hypothesis was pre-registered with its
falsification condition fixed in code before the loader worked. It returned
REFUTED and we reported it. The journal in [`docs/`](docs/) records the
reversal as it happened.

**Did you try to rescue it?**
There is a parameter window where the method wins by up to 34%. We report it
and also report that **the window does not transfer** — RCAEval wins at
10–300× error-budget dominance, RCA100 at 300–1000×. No single value works for
both. Adopting the one that rescues one corpus would have been the dishonest
move available, which is why the sweep was built before the result was known.

**Does the mathematics still hold?**
Yes. Propositions 1–3 are proved and verified numerically, and CI re-checks
them on every push. What was refuted is their *practical reach on public
benchmarks*, not their correctness.

**Why does the title not say "LLM-Assisted"?**
Because no LLM is run in the reported results. The confidence signal is
simulated at literature calibration levels; the stake side is measured. The
harness for a real agent ships in `agent.py` but has not been run.

**Can I use this in production?**
The stake estimator, yes — it runs on telemetry any instrumented cluster
emits. The threshold derivation, only above ρ\* ≈ $111/hour, and check your
own numbers first. Below that, the evidence here says a gate subtracts value.

**What would change the conclusion?**
A corpus with both cluster dynamics and traffic telemetry. None of the three
examined has both. That is the open problem this work hands forward.

---

## 14. Complete file manifest

Every file in the repository, 44 in total. Nothing here is undocumented.

### Repository root

| File | Purpose |
|---|---|
| `README.md` | Orientation — what this is, what was found, how to run it |
| `GUIDE.md` | This file. The complete reference |
| `LICENSE` | MIT. The datasets carry their own licences |
| `requirements.txt` | Six core packages; `anthropic` optional, agent study only |
| `CITATION.cff` | Machine-readable citation metadata. Drives GitHub's "Cite this repository" button |
| `.gitignore` | Excludes `data/` (~1 GB, downloadable), `figures/` (generated), `paper/` (unsubmitted manuscript), credentials, and the Obsidian working copies of the journal |
| `.gitattributes` | `* text=auto eol=lf` so the repo is byte-identical across Windows, macOS and Linux; PDFs and parquet marked binary |

### `.github/`

| File | Purpose |
|---|---|
| `workflows/ci.yml` | Runs Propositions 1 and 2 against a finite difference, checks topology integrity, and imports all modules, on Python 3.11 and 3.12. Deliberately does **not** run `verify_paper.py`, which needs the corpora |

### `code/` — 20 files

| File | Purpose |
|---|---|
| `README.txt` | A short orientation for the code directory alone, including the ordering-violation finding that needs a decision |
| `policy.py` | **The mathematics.** Both thresholds, the sign flip, the three-way policy. Self-verifying — run first |
| `stakes.py` | Stake composition (Eq. 12–13) and `StakeParams` |
| `topology.py` | Static call graphs; blast radius. Train Ticket deliberately unsupported |
| `rcaeval_loader.py` | RCAEval, wide format. Schema detected **per file** |
| `rca100_loader.py` | RCA100, long format. Shares nothing with the above but the equations |
| `rebalance.py` | p90 calibration and the simplex sweep |
| `evaluate.py` | Realised cost, oracle, five baselines, regret, ECE, risk–coverage |
| `run_rq1.py` | The pre-registered gate |
| `compare.py` | Cross-corpus comparison and the burn-dominance sweep |
| `verify_paper.py` | Recomputes all 43 claimed numbers and fails loudly on divergence |
| `figures.py` | The four figures → `figures/` |
| `run_all.py` | Everything, in order, stopping at the first failure |
| `download.py` | RCAEval acquisition, resumable |
| `download_rca100.py` | RCA100 acquisition, lean by default |
| `probe_rca100.py` | One-off reachability probe, kept for provenance |
| `cloudops_probe.py` | Field verification for the rejected third corpus |
| `summarise.py` | Deterministic telemetry → agent context |
| `agent.py` | The agent study. Needs an API key |
| `agent_results.py` | Real `(q, Y)` → the verified pipeline |

### `docs/` — 16 files

`README.md` indexes all 14 journal entries plus the project brief. The entries
are the working notes kept while the study ran, published because the
provenance is the point: the hypothesis was pre-registered and then refuted by
its own authors.

| File | What it records |
|---|---|
| `README.md` | Index of the journal, with the three entries worth reading first |
| `PROJECT-BRIEF.txt` | The plan written **before** any data existed. One personal observation redacted, visibly marked |
| `2026-09-20_problem-statement-market-validation.md` | The novelty scan that cut two thirds of the original brief |
| `2026-09-20_problem-statement-final.md` | The problem statement in three lengths |
| `2026-09-21_loss-function-page.md` | Every cost term with a unit and a source; where the sign flip was found |
| `2026-09-21_rcaeval-day1-field-verification.md` | What the first dataset actually contains |
| `2026-09-21_first-results-and-the-one-term-problem.md` | A flat sensitivity sweep read as a defect, not a triumph |
| `2026-09-21_rq1-refuted-and-why-that-is-the-result.md` | **The reversal.** A parser bug and a degenerate cost model |
| `2026-09-21_rca100-replicates-the-refutation.md` | The second corpus, and the salvage that does not transfer |
| `2026-09-21_four-figures-and-one-replaced.md` | Three figure defects found by looking |
| `2026-09-21_clearing-the-markers.md` | What filling in the placeholders revealed |
| `2026-09-21_compiling-and-the-heredoc-corruption.md` | A shell-escaping bug that reached the source |
| `2026-09-21_verifying-every-citation.md` | Three citations that were wrong |
| `2026-09-21_pre-submission-rescan.md` | The first pre-submission novelty scan |
| `2026-09-21_owning-the-three-action-contradiction.md` | Deriving where a collapsed contribution stops being collapsed |
| `2026-10-29_market-recheck-and-honest-positioning.md` | The October re-scan; three adjacent papers, none a scoop |

### Not in the repository

| | Why |
|---|---|
| `data/` | ~1 GB. Reproducible via `download.py` and `download_rca100.py`, both resumable |
| `figures/` | Generated. `python figures.py` recreates all four |
| `paper/` | Unsubmitted manuscript. On a public remote it can count as prior publication at some venues. Held in a separate private repository |
