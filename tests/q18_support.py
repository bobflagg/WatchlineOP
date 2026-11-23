"""Shared helpers for the Q18 checks: classify deeds and derive restructuring signals from the frozen source, independent of the graph."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from q12_support import DEED_TYPES, check, connect, finish, n3, source_deeds  # noqa: E402,F401

OWNERS = (Path(__file__).resolve().parent / "q12_3" / "expected.sql").read_text()


def classify(d: dict, typ: str | None = None) -> str:
    """correction (CORRD, CONDEED), zero-transfer (amount 0), else priced. Computed, never stored."""
    if d["type"] in ("CORRD", "CONDEED"):
        return "correction"
    return "zero-transfer" if d["amount"] == 0 else "priced"


def lot_addresses(cur, bbls) -> dict:
    cur.execute("SELECT bbl::text, address FROM pluto_latest WHERE bbl = ANY(%(b)s)", {"b": list(bbls)})
    return {b: a for b, a in cur.fetchall()}


def signals(cur, bbls, start=None, end=None) -> dict:
    """{documentId: {lots, named, same, followOn: set(documentId), owner}} for each zero-transfer deed on bbls, from the source."""
    addr = lot_addresses(cur, bbls)
    window = source_deeds(cur, bbls, start, end)
    full = {b: source_deeds(cur, [b]) for b in bbls}      # every deed of the lot, for follow-on search
    cur.execute(OWNERS, {"bbls": list(bbls), "types": DEED_TYPES, "start": None, "end": None})
    owner_pairs = {(doc, bbl): (bool(g)) for doc, bbl, _o, g, _r in cur.fetchall()}
    out = {}
    for doc, d in window.items():
        if classify(d) != "zero-transfer":
            continue
        lots = [b for b in bbls if doc in full[b]]
        gkeys = {n3(p[0]) for p in d["grantees"] if n3(p[0])}
        rkeys = {n3(p[0]) for p in d["grantors"] if n3(p[0])}
        hn = lambda b: (addr.get(b) or "").split(" ")[0]
        named = any(k.startswith(hn(b) + " ") for b in lots if hn(b) for k in gkeys)
        follow = set()
        for b in lots:
            for odoc, o in full[b].items():
                if odoc != doc and o["recorded"] >= d["recorded"] and gkeys & {n3(p[0]) for p in o["grantors"]}:
                    follow.add(odoc)
        out[doc] = {"lots": sorted(lots), "named": named, "same": bool(gkeys & rkeys), "followOn": follow,
                    "owner": any(owner_pairs.get((doc, b), False) for b in lots)}
    return out
