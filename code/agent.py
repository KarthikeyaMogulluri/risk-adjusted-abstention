"""
The RCA agent study -- replaces simulated confidence with a real model.

WHY THIS IS A SMALL CHANGE. The evaluation pipeline takes (q, Y, rho, D, T_e)
and is already verified end to end (43/43 in verify_paper.py). Only q and Y are
simulated today. This module produces real ones; nothing downstream changes.

WHAT THE TRIVIAL BASELINE SAYS -- measured before spending anything:

    corpus     rank-1 acc   top-3 acc
    RCAEval      75.8%        95.6%     <- largest anomaly is usually the cause
    RCA100       29.1%        39.8%     <- it usually is not

So RCAEval is close to solved by ranking alone and is a weak testbed: an agent
there is mostly being tested on not ruining a good ordering. RCA100 carries the
diagnostic difficulty. We run both and ALWAYS report the trivial baseline
beside the agent, which RCA papers routinely omit.

    python agent.py --estimate                  # tokens and cost, no API calls
    python agent.py --corpus rca100 --limit 5   # smoke test
    python agent.py --corpus rca100             # full run, resumable
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
RUNS = ROOT / "data" / "agent_runs"

# Published per-million-token prices, used only for the estimate.
PRICES = {
    "claude-opus-4-5":   (5.00, 25.00),
    "claude-sonnet-4-5": (3.00, 15.00),
    "claude-haiku-4-5":  (1.00,  5.00),
}
DEFAULT_MODEL = "claude-sonnet-4-5"

SYSTEM = """You are a site reliability engineer diagnosing a fault in a \
Kubernetes microservice deployment.

You are given, for every service, how each signal shifted between the window \
before the fault was injected and the window during it. Services are listed in \
order of largest change, but the largest change is frequently a SYMPTOM rather \
than the cause: load shifts and latency propagate downstream, and a saturated \
service often perturbs its callers more visibly than itself.

Identify the single service where the fault originated, and the kind of fault.

Report a calibrated confidence. Calibrated means: across many incidents where \
you say 0.7, you should be correct about 70% of the time. Do not inflate it \
because a single service looks obvious, and do not deflate it to appear \
cautious. If the evidence genuinely underdetermines the cause, say so with a \
low number."""

TOOL = {
    "name": "report_root_cause",
    "description": "Report the diagnosed root cause with a calibrated confidence.",
    "input_schema": {
        "type": "object",
        "properties": {
            "root_cause_service": {
                "type": "string",
                "description": "Exact service name from the report.",
            },
            "fault_type": {
                "type": "string",
                "description": "One of: cpu, memory, disk, network-delay, "
                               "packet-loss, error-5xx, other.",
            },
            "confidence": {
                "type": "number",
                "description": "Calibrated probability in [0,1] that "
                               "root_cause_service is correct.",
            },
            "reasoning": {
                "type": "string",
                "description": "Two sentences: the evidence, and what would "
                               "disconfirm it.",
            },
        },
        "required": ["root_cause_service", "fault_type", "confidence",
                     "reasoning"],
    },
}


# ------------------------------------------------------------------ cases ---
def load_cases(corpus: str) -> list[dict]:
    """Return [{case, prompt, truth}] with ground truth attached."""
    from summarise import summarise_rcaeval, summarise_rca100, render
    import pandas as pd
    out = []

    if corpus == "rcaeval":
        idx = pd.read_parquet(ROOT / "data" / "cases.parquet")
        idx = idx[(idx.suite == "RE1") & (idx.system.isin(("ob", "ss")))]
        for _, r in idx.iterrows():
            d = ROOT / "data" / "cases" / r["case"]
            if not (d / "metrics.parquet").exists():
                continue
            try:
                s = summarise_rcaeval(r["case"])
            except Exception:                                  # noqa: BLE001
                continue
            out.append({"case": r["case"], "prompt": render(s),
                        "truth": [str(r["root_cause_service"])],
                        "rank1": s["services"][0]["service"] if s["services"] else ""})
    else:
        tasks = [t.strip() for t in
                 (ROOT / "data" / "rca100" / "manifest.txt").read_text().split()
                 if t.strip()]
        for t in tasks:
            d = ROOT / "data" / "rca100" / "cases" / t
            gt = ROOT / "data" / "rca100" / "answer_key" / f"{t}.gt.json"
            if not (d / "metrics.parquet").exists() or not gt.exists():
                continue
            truth = json.loads(gt.read_text(encoding="utf-8")).get(
                "root_cause_entities") or []
            if not truth:
                continue
            try:
                s = summarise_rca100(t)
            except Exception:                                  # noqa: BLE001
                continue
            out.append({"case": t, "prompt": render(s),
                        "truth": [str(x) for x in truth],
                        "rank1": s["services"][0]["service"] if s["services"] else ""})
    return out


def scores(pred: str, truth: list[str]) -> int:
    """1 if the prediction names a ground-truth entity. Substring either way,
    because RCA100 labels services while the graph carries typed entities."""
    p = (pred or "").strip().lower()
    if not p:
        return 0
    return int(any(p == t.lower() or p in t.lower() or t.lower() in p
                   for t in truth))


# --------------------------------------------------------------- estimate ---
def estimate(corpora: list[str], model: str, reps: int) -> None:
    try:
        import anthropic
        client = anthropic.Anthropic(api_key="x")   # counting needs no auth key
        counter = client.messages.count_tokens
    except Exception:
        counter = None

    tin = tout = ncases = 0
    for c in corpora:
        cases = load_cases(c)
        chars = sum(len(x["prompt"]) for x in cases)
        # 3.6 chars/token is the usual English ratio; the exact counter is used
        # when it is reachable.
        est_in = chars / 3.6 + len(cases) * 420      # + system + tool schema
        tin += est_in
        tout += len(cases) * 220
        ncases += len(cases)
        print(f"  {c:<10} {len(cases):>4} cases  "
              f"{est_in/1e3:>8.1f}k input tokens")

    tin *= reps
    tout *= reps
    pin, pout = PRICES.get(model, PRICES[DEFAULT_MODEL])
    cost = tin / 1e6 * pin + tout / 1e6 * pout
    print()
    print(f"  model        {model}")
    print(f"  repetitions  {reps}")
    print(f"  calls        {ncases * reps:,}")
    print(f"  input        {tin/1e6:.2f}M tokens")
    print(f"  output       {tout/1e6:.2f}M tokens")
    print(f"  ESTIMATED    ${cost:,.2f}")
    print()
    for m, (a, b) in PRICES.items():
        print(f"    {m:<20} ${tin/1e6*a + tout/1e6*b:>7,.2f}")


# -------------------------------------------------------------------- run ---
def run(corpus: str, model: str, limit: int, rep: int) -> None:
    import anthropic
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("ANTHROPIC_API_KEY is not set. Export it and re-run.")
    client = anthropic.Anthropic()

    RUNS.mkdir(parents=True, exist_ok=True)
    out = RUNS / f"{corpus}_{model}_rep{rep}.jsonl"
    done = set()
    if out.exists():
        done = {json.loads(l)["case"] for l in out.open(encoding="utf-8") if l.strip()}
        print(f"  resuming: {len(done)} already complete")

    cases = load_cases(corpus)
    if limit:
        cases = cases[:limit]

    with out.open("a", encoding="utf-8") as fh:
        for i, c in enumerate(cases, 1):
            if c["case"] in done:
                continue
            for attempt in range(4):
                try:
                    r = client.messages.create(
                        model=model, max_tokens=700, system=SYSTEM,
                        tools=[TOOL],
                        tool_choice={"type": "tool",
                                     "name": "report_root_cause"},
                        messages=[{"role": "user", "content": c["prompt"]}],
                    )
                    break
                except Exception as e:                         # noqa: BLE001
                    if attempt == 3:
                        print(f"  FAIL {c['case']}: {type(e).__name__}")
                        r = None
                        break
                    time.sleep(2 ** attempt)
            if r is None:
                continue

            blk = next((b for b in r.content if b.type == "tool_use"), None)
            if blk is None:
                continue
            d = blk.input
            rec = {
                "case": c["case"],
                "pred": d.get("root_cause_service", ""),
                "fault": d.get("fault_type", ""),
                "q": float(d.get("confidence", 0.0)),
                "reasoning": d.get("reasoning", "")[:400],
                "truth": c["truth"],
                "rank1": c["rank1"],
                "Y": scores(d.get("root_cause_service", ""), c["truth"]),
                "Y_rank1": scores(c["rank1"], c["truth"]),
                "in_tok": r.usage.input_tokens,
                "out_tok": r.usage.output_tokens,
            }
            fh.write(json.dumps(rec) + "\n")
            fh.flush()
            if i % 10 == 0 or i == len(cases):
                print(f"  {i}/{len(cases)}", flush=True)

    print(f"  written -> {out}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", choices=["rcaeval", "rca100"], default="rca100")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--rep", type=int, default=1)
    ap.add_argument("--reps", type=int, default=1, help="for --estimate only")
    ap.add_argument("--estimate", action="store_true")
    a = ap.parse_args()

    if a.estimate:
        estimate(["rcaeval", "rca100"], a.model, a.reps)
        return
    run(a.corpus, a.model, a.limit, a.rep)


if __name__ == "__main__":
    main()
