"""Shared helpers for tests/q23_*: the footprint of a managing agent name, derived from the frozen source, and layer membership from the pinned BOR release.

Read-only on the source database, the release and the graph. Independent of the loaders. Counting units are named in each check:
registrations (distinct registration ids), buildings (distinct BIN) and lots (distinct BBL), never links.
"""

import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[0] / "src"))
from bor_support import group_layer, network_layer  # noqa: E402,F401
from q19_support import NET, PORT  # noqa: E402,F401
from watchline.compare import n3  # noqa: E402

SQL = "\n".join(ln for ln in (HERE / "q23_1" / "expected.sql").read_text().splitlines() if not ln.startswith("--")).strip().rstrip(";")


def agent_rows(pg, name_key: str) -> list[tuple]:
    """(registrationid, contact type, corporation name as recorded, bbl, bin) of Agent contacts whose corporation name has the N3 key, on registrations the graph holds."""
    prefix = name_key.split(" ")[0] + "%"
    with pg.cursor() as cur:
        cur.execute(SQL, {"prefix": prefix})
        return [r for r in cur.fetchall() if n3(r[2]) == name_key]


def lots_of_bins(pg, bins: set) -> set:
    """Lots of buildings: every lot on which HPD records one of these BINs (a building on two lots counts toward both), as Q21 does."""
    with pg.cursor() as cur:
        cur.execute("SELECT DISTINCT bbl::text FROM hpd_registrations WHERE bin = ANY(%s) AND bbl IS NOT NULL AND registrationid > 0", (sorted(bins),))
        return {r[0] for r in cur.fetchall()}


def footprint(pg, rows: list[tuple]) -> dict:
    return {"registrations": len({r[0] for r in rows}), "buildings": len({r[4] for r in rows}), "lots": len(lots_of_bins(pg, {r[4] for r in rows})),
            "spellings": dict(Counter({s: len({r[0] for r in rows if r[2].strip() == s}) for s in {r[2].strip() for r in rows}}))}


def layer_state(lots: set, ref_lots: set, group_of: dict) -> dict:
    """Of the footprint lots: in the group(s) of the reference lots, in another group, in none. One reference lot expected; with several, 'same' means any of them."""
    ref = {group_of[b] for b in ref_lots if b in group_of}
    same = {b for b in lots if group_of.get(b) in ref}
    none = {b for b in lots if b not in group_of}
    return {"group": sorted(ref)[0] if len(ref) == 1 else None, "lots": len(lots), "same": len(same), "other": len(lots) - len(same) - len(none), "none": len(none)}
