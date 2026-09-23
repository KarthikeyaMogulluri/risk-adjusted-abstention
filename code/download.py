"""
Download RCAEval case data from HuggingFace.

Deliberately not using the RCAEval pip package: it pulls a heavy dependency
tree and we need only the parquet files. Plain HTTP against the HF resolve
endpoint is smaller, faster and has no version coupling.

    python download.py --suite RE1            # 375 cases, ~140 MB
    python download.py --suite RE2 --workers 8
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import pathlib
import sys

import pandas as pd
import requests

REPO = "https://huggingface.co/datasets/phamquiluan/RCAEval/resolve/main"
DATA = pathlib.Path(__file__).resolve().parent.parent / "data"

# Files present per case, by suite. Verified against the HF tree 2026-09-21:
# RE1 cases carry only inject_time.txt and metrics.parquet -- no traces, no logs.
PER_CASE = ["metrics.parquet", "inject_time.txt"]
OPTIONAL = ["traces.csv", "logs.csv", "simple_metrics.parquet"]


def fetch(case: str, fname: str, force: bool = False) -> tuple[str, str, int]:
    out = DATA / "cases" / case / fname
    if out.exists() and not force and out.stat().st_size > 0:
        return case, fname, -1                      # already have it
    out.parent.mkdir(parents=True, exist_ok=True)
    r = requests.get(f"{REPO}/{case}/{fname}", timeout=180)
    if r.status_code != 200:
        return case, fname, -r.status_code
    out.write_bytes(r.content)
    return case, fname, len(r.content)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--suite", default="RE1", choices=["RE1", "RE2", "RE3"])
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--optional", action="store_true",
                    help="also try traces.csv / logs.csv (RE2, RE3)")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    cases = pd.read_parquet(DATA / "cases.parquet")
    cases = cases[cases.suite == args.suite]
    if args.limit:
        cases = cases.head(args.limit)
    names = cases["case"].tolist()
    print(f"{args.suite}: {len(names)} cases")

    jobs = [(c, f) for c in names for f in PER_CASE]
    if args.optional:
        jobs += [(c, f) for c in names for f in OPTIONAL]

    got = skipped = failed = 0
    total_bytes = 0
    with cf.ThreadPoolExecutor(args.workers) as ex:
        futs = [ex.submit(fetch, c, f) for c, f in jobs]
        for i, fut in enumerate(cf.as_completed(futs), 1):
            case, fname, n = fut.result()
            if n == -1:
                skipped += 1
            elif n < 0:
                failed += 1
                if fname in PER_CASE:          # optional misses are expected
                    print(f"  FAIL {case}/{fname} HTTP {-n}")
            else:
                got += 1
                total_bytes += n
            if i % 100 == 0 or i == len(futs):
                print(f"  {i}/{len(futs)}  got={got} cached={skipped} "
                      f"missing={failed}  {total_bytes/1e6:.0f} MB",
                      flush=True)

    print(f"\ndone. {got} downloaded, {skipped} cached, {failed} missing, "
          f"{total_bytes/1e6:.1f} MB")
    if failed and not args.optional:
        print("NOTE: missing REQUIRED files -- investigate before loading.")
        sys.exit(1)


if __name__ == "__main__":
    main()
