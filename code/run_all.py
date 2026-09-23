"""
Run the whole study end to end, in order, and stop at the first failure.

Everything except the agent study, which costs money and needs a key.

    python run_all.py              # verify -> download -> gate -> compare -> figures
    python run_all.py --skip-download
    python run_all.py --quick      # maths + verification only, no data needed
"""

from __future__ import annotations

import argparse
import pathlib
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
DATA = HERE.parent / "data"


def step(n: int, total: int, title: str, args: list[str],
         needs_data: bool = False) -> float:
    print()
    print("=" * 74)
    print(f"[{n}/{total}]  {title}")
    print("=" * 74, flush=True)
    if needs_data and not (DATA / "cases.parquet").exists():
        print("  data not present -- run without --skip-download first")
        sys.exit(1)
    t0 = time.time()
    r = subprocess.run([sys.executable, "-u", *args], cwd=HERE)
    dt = time.time() - t0
    if r.returncode != 0:
        print(f"\n  FAILED after {dt:.0f}s: {' '.join(args)}")
        print("  Stopping. Fix this before continuing -- later steps build on it.")
        sys.exit(r.returncode)
    print(f"\n  ok ({dt:.0f}s)")
    return dt


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-download", action="store_true")
    ap.add_argument("--quick", action="store_true",
                    help="propositions + paper verification only")
    a = ap.parse_args()

    plan: list[tuple[str, list[str], bool]] = [
        ("Verify Propositions 1 and 2 (no data needed)", ["policy.py"], False),
    ]
    if not a.quick:
        if not a.skip_download:
            plan += [
                ("Download RCAEval RE1 (~120 MB)",
                 ["download.py", "--suite", "RE1"], False),
                ("Download RCA100 (~62 MB)", ["download_rca100.py"], False),
            ]
        plan += [
            ("Pre-registered gate on RCAEval",
             ["run_rq1.py", "--dataset", "rcaeval", "--root", "../data"], True),
            ("Cross-corpus comparison", ["compare.py"], True),
        ]
    plan.append(("Verify all 43 paper numbers", ["verify_paper.py"],
                 not a.quick))
    if not a.quick:
        plan.append(("Regenerate the four figures", ["figures.py"], True))

    total = len(plan)
    spent = 0.0
    for i, (title, args, nd) in enumerate(plan, 1):
        spent += step(i, total, title, args, nd)

    print()
    print("=" * 74)
    print(f"ALL STEPS PASSED  ({spent/60:.1f} min)")
    print("=" * 74)
    print()
    print("Next, if you want the agent study (costs money):")
    print("    python agent.py --estimate --reps 3")
    print("    export ANTHROPIC_API_KEY=sk-ant-...")
    print("    python agent.py --corpus rca100 --limit 5")
    print()
    print("To build the paper:")
    print("    cd ../paper && tectonic -X compile main.tex --outdir build")


if __name__ == "__main__":
    main()
