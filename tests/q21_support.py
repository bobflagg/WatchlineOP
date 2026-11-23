"""Shared helpers for tests/q21_*: expected open-violation figures per lot, derived from the pinned BOR release (members) and the source database (violations, units).

Read-only on the release, the source database and the graph. Independent of the loaders.
"""

from pathlib import Path

from bor_support import group_layer, network_layer  # noqa: F401
from q19_support import NET, PORT  # noqa: F401

HERE = Path(__file__).resolve().parent
SQL = "\n".join(ln for ln in (HERE / "q21_1" / "expected.sql").read_text().splitlines() if not ln.startswith("--")).strip().rstrip(";")
TOP = 3


def members(release, layer: str, group_id: str) -> list[str]:
    """Member lots of a group from the release: all network lots, or the rental portfolio lots."""
    if layer in ("network", NET):
        return sorted(network_layer(release)[1].get(group_id, []))
    return sorted(group_layer(release, PORT)[1].get(group_id, []))


def lot_figures(pg, bbls: list[str]) -> dict:
    """{bbl: {open, A, B, C, I, units, rate}} from the source for the given lots (members absent from the graph's scope get zeros)."""
    out = {b: {"open": 0, "A": 0, "B": 0, "C": 0, "I": 0, "units": None, "rate": None} for b in bbls}
    with pg.cursor() as cur:
        cur.execute(SQL, {"bbls": bbls})
        for bbl, cls, n in cur.fetchall():
            out[bbl][cls] = int(n)
        cur.execute("SELECT bbl::text, unitsres FROM pluto_latest WHERE bbl::text = ANY(%s)", (bbls,))
        for bbl, u in cur.fetchall():
            out[bbl]["units"] = u
    for f in out.values():
        f["open"] = f["A"] + f["B"] + f["C"] + f["I"]
        f["rate"] = None if not f["units"] else f["open"] / f["units"]
    return out


def ranked(figs: dict) -> list[str]:
    """Rank rule: rate available first (descending), then open count (descending), then bbl."""
    return sorted(figs, key=lambda b: (-(figs[b]["rate"] if figs[b]["rate"] is not None else -1.0), -figs[b]["open"], b))


def concentration(figs: dict, top: int = TOP) -> dict:
    counts = sorted((f["open"] for f in figs.values()), reverse=True)
    total = sum(counts)
    return {"memberLots": len(figs), "lotsWithOpen": sum(1 for c in counts if c), "sumOpen": total, "topOpen": sum(counts[:top]),
            "topShare": None if total == 0 else sum(counts[:top]) / total}
