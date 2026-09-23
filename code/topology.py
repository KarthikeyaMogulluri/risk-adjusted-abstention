"""
Static service dependency graphs -- the blast-radius term in Eq. (13).

WHY STATIC RATHER THAN TRACE-DERIVED
------------------------------------
Verified against the RCAEval index on 2026-09-21:

    suite   has_traces
    RE1     0%          <- all 375 cases
    RE2     66.7%
    RE3     66.7%

Only 240 of 735 cases carry traces. A trace-derived call graph would therefore
cover a third of the corpus and vary with sampling rate and load.

These three systems are published, open-source, fixed architectures. Their
dependency graphs are documented properties of the software, not measurements.
Using them gives 100% coverage, exact reproducibility, and no dependence on
trace sampling. This is a strength, not a compromise -- but it MUST be stated
in Section 5.2 as a declared topology, never implied to be trace-derived.

VERIFY BEFORE SUBMISSION: check each graph against the upstream architecture
diagram. Encoded from the documented designs; a transcription error here
silently biases every blast-radius number.
"""

from __future__ import annotations


# --- Online Boutique (GoogleCloudPlatform/microservices-demo) ----------------
# Service names match the metric column prefixes in the RCAEval data exactly.
ONLINE_BOUTIQUE = {
    "frontend": ["adservice", "cartservice", "checkoutservice",
                 "currencyservice", "productcatalogservice",
                 "recommendationservice", "shippingservice"],
    "checkoutservice": ["cartservice", "currencyservice", "emailservice",
                        "paymentservice", "productcatalogservice",
                        "shippingservice"],
    "recommendationservice": ["productcatalogservice"],
    "cartservice": ["redis"],
    "adservice": [],
    "currencyservice": [],
    "emailservice": [],
    "paymentservice": [],
    "productcatalogservice": [],
    "shippingservice": [],
    "redis": [],
}

# --- Sock Shop (microservices-demo / weaveworks) -----------------------------
SOCK_SHOP = {
    "front-end": ["catalogue", "carts", "orders", "user"],
    "orders": ["carts", "payment", "shipping", "user", "orders-db"],
    "catalogue": ["catalogue-db"],
    "carts": ["carts-db"],
    "user": ["user-db"],
    "shipping": ["rabbitmq"],
    "rabbitmq": ["queue-master"],
    "payment": [],
    "queue-master": [],
    "catalogue-db": [],
    "carts-db": [],
    "user-db": [],
    "orders-db": [],
    "session-db": [],
    "rabbitmq-exporter": [],
}

# --- Train Ticket ------------------------------------------------------------
# 64 services. NOT ENCODED. Transcribing a 64-node graph from memory is exactly
# the kind of plausible-looking guess that silently corrupts results, so the
# loader refuses Train Ticket rather than inventing its topology.
#
# TODO: transcribe from the FudanSELab/train-ticket architecture documentation,
# or derive it from RE2's traces (66% coverage) and report the coverage gap.
# Until then RQ1 runs on Online Boutique + Sock Shop = 250 RE1 cases, which is
# two independent systems and sufficient for the gating test.
TRAIN_TICKET: dict[str, list[str]] = {}

GRAPHS = {"ob": ONLINE_BOUTIQUE, "ss": SOCK_SHOP, "tt": TRAIN_TICKET}
SUPPORTED = ("ob", "ss")


def downstream(system: str, service: str) -> set[str]:
    """Services transitively reachable from `service`. Excludes itself.

    This is the blast radius: what a wrong remediation on `service` can break.
    """
    g = GRAPHS.get(system)
    if not g:
        raise NotImplementedError(
            f"No topology for system '{system}'. Supported: {SUPPORTED}. "
            "See the Train Ticket note in topology.py."
        )
    seen: set[str] = set()
    stack = list(g.get(service, []))
    while stack:
        n = stack.pop()
        if n in seen:
            continue
        seen.add(n)
        stack.extend(g.get(n, []))
    seen.discard(service)
    return seen


def blast_radius(system: str, service: str) -> int:
    return len(downstream(system, service))


def _selftest() -> None:
    for sysid in SUPPORTED:
        g = GRAPHS[sysid]
        print(f"{sysid}: {len(g)} services")
        radii = {s: blast_radius(sysid, s) for s in g}
        for s, r in sorted(radii.items(), key=lambda kv: -kv[1])[:4]:
            print(f"    {s:<26} blast radius {r}")
        lo, hi = min(radii.values()), max(radii.values())
        print(f"    range {lo}-{hi}")
        # Every declared edge target must be a declared node, or the graph has
        # a typo and reachability is silently wrong.
        for src, dsts in g.items():
            for d in dsts:
                assert d in g, f"{sysid}: edge {src}->{d} but '{d}' not a node"
        print(f"    edge targets all resolve: OK")


if __name__ == "__main__":
    _selftest()
