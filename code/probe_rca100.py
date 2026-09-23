"""Probe every plausible route to the RCA100 / AIOps2025 archives.

The project page at www.aiops.cn serves HTML fine but its GitLab API timed out
at 60s. This tries the API again with a long timeout, the HTML tree pages, and
the raw/archive endpoints, and reports which routes work and what sizes they
advertise -- before committing to a 3.4 GB download.
"""
from __future__ import annotations

import requests

BASE = "https://www.aiops.cn/gitlab"
PROJ = "aiops-live-benchmark/agenticopseval"
ENC = PROJ.replace("/", "%2F")
H = {"User-Agent": "Mozilla/5.0 (research data fetch)"}
T = (30, 300)          # connect, read


def probe(label: str, url: str, head: bool = False) -> None:
    try:
        fn = requests.head if head else requests.get
        r = fn(url, timeout=T, headers=H, allow_redirects=True,
               stream=not head)
        size = r.headers.get("Content-Length", "?")
        ctype = r.headers.get("Content-Type", "?")[:40]
        print(f"  {r.status_code}  {size:>12}  {ctype:<40} {label}")
        if not head and r.status_code == 200 and "json" in ctype:
            j = r.json()
            if isinstance(j, list):
                for e in j[:30]:
                    print(f"        {e.get('type','?'):9} {e.get('path','?')}")
            else:
                print("       ", {k: j[k] for k in list(j)[:8]})
        r.close()
    except Exception as e:                                   # noqa: BLE001
        print(f"  FAIL {type(e).__name__:24} {label}")


def main() -> None:
    print("API routes")
    probe("project meta", f"{BASE}/api/v4/projects/{ENC}")
    probe("tree root", f"{BASE}/api/v4/projects/{ENC}/repository/tree?per_page=100")
    for p in ("RCA100", "AIOps2025"):
        probe(f"tree {p}",
              f"{BASE}/api/v4/projects/{ENC}/repository/tree?per_page=100&path={p}")

    print("\nHTML tree routes")
    for p in ("", "RCA100", "AIOps2025"):
        probe(f"html tree /{p}", f"{BASE}/{PROJ}/-/tree/main/{p}")

    print("\nArchive / raw routes (HEAD only -- size check, no download)")
    probe("repo archive .tar.gz", f"{BASE}/{PROJ}/-/archive/main/agenticopseval-main.tar.gz", head=True)
    probe("raw README", f"{BASE}/{PROJ}/-/raw/main/README.md", head=True)


if __name__ == "__main__":
    main()
