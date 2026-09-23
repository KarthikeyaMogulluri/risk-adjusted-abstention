"""
Download RCA100 v1.1 -- the second, independent population.

ROUTING, established by probe on 2026-09-21:
  - The aiops.cn GitLab API returns 404 (project not exposed over API), so the
    repository tree cannot be enumerated. Raw file paths DO resolve.
  - Case data is mirrored on Alibaba OSS and is much faster from there.
  - answer_key/ is NOT on OSS (404). It comes from GitLab raw.

LEAN BY DESIGN. A full case is ~35 MB, dominated by traces (26 MB) and logs
(8.5 MB). The stake model needs neither: metrics carry the signal and
topology.json carries the call graph. Pulling only what is used takes the
corpus from ~3.6 GB to ~65 MB and costs nothing the analysis needs.

WHY THIS DATASET MATTERS BEYOND BEING A SECOND POPULATION
  - `deployment_available_replicas` is present, so rho_infra can use the real
    OpenCost replica-seconds formula instead of the CPU+memory proxy RCAEval
    forced. Substitution 1 is testable here rather than merely declared.
  - topology.json ships 277 entities and 353 edges per case, so blast radius
    is measured rather than taken from a published static graph.
    Substitution 3 is likewise testable.

    python download_rca100.py            # lean, 103 tasks
    python download_rca100.py --full     # adds traces + logs (~3.6 GB)
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import pathlib

import requests

OSS = "https://aiops-benchmark.oss-cn-hongkong.aliyuncs.com/rca/rca100/v1.1"
GITLAB = ("https://www.aiops.cn/gitlab/aiops-live-benchmark/"
          "agenticopseval/-/raw/main/RCA100")
HEADERS = {"User-Agent": "Mozilla/5.0 (research data fetch)"}
DATA = pathlib.Path(__file__).resolve().parent.parent / "data" / "rca100"

LEAN = ["task.json", "topology.json", "metrics.parquet", "alerts.parquet",
        "events.parquet"]
HEAVY = ["traces.parquet", "logs.parquet"]


def fetch(base: str, remote: str, local: str, force: bool = False):
    out = DATA / local
    if out.exists() and not force and out.stat().st_size > 0:
        return local, -1
    try:
        r = requests.get(f"{base}/{remote}", timeout=(20, 300), headers=HEADERS)
    except Exception as e:                                     # noqa: BLE001
        return local, -999
    if r.status_code != 200:
        return local, -r.status_code
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(r.content)
    return local, len(r.content)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()

    DATA.mkdir(parents=True, exist_ok=True)
    fetch(OSS, "manifest.txt", "manifest.txt")
    tasks = [t.strip() for t in (DATA / "manifest.txt").read_text().split()
             if t.strip()]
    print(f"manifest: {len(tasks)} tasks ({tasks[0]}..{tasks[-1]})")

    files = LEAN + (HEAVY if args.full else [])
    jobs = [(OSS, f"cases/{t}/{f}", f"cases/{t}/{f}")
            for t in tasks for f in files]
    # ground truth + taxonomy come from GitLab, which is slower -- keep it small
    jobs += [(GITLAB, f"answer_key/{t}.gt.json", f"answer_key/{t}.gt.json")
             for t in tasks]
    jobs += [(GITLAB, "answer_key/mapping.json", "answer_key/mapping.json"),
             (GITLAB, "answer_key/taxonomy.json", "answer_key/taxonomy.json"),
             (OSS, "summary.json", "summary.json")]

    got = cached = missing = 0
    total = 0
    with cf.ThreadPoolExecutor(args.workers) as ex:
        futs = [ex.submit(fetch, b, r, l) for b, r, l in jobs]
        for i, fut in enumerate(cf.as_completed(futs), 1):
            local, n = fut.result()
            if n == -1:
                cached += 1
            elif n < 0:
                missing += 1
                if missing <= 5:
                    print(f"  MISS {local} ({n})")
            else:
                got += 1
                total += n
            if i % 100 == 0 or i == len(futs):
                print(f"  {i}/{len(futs)}  got={got} cached={cached} "
                      f"miss={missing}  {total/1e6:.0f} MB", flush=True)

    print(f"\ndone. {got} downloaded, {cached} cached, {missing} missing, "
          f"{total/1e6:.1f} MB")


if __name__ == "__main__":
    main()
