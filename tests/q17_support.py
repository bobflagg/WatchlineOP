"""Shared helpers for the Q17 checks: derive the missing, lapsed, older-than-deed and threshold answers from the frozen source, independent of the graph."""

import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from q14_support import DEED_TYPES, check, connect, finish  # noqa: E402,F401

ROOT = HERE.parent
AS_OF = "2026-05-29"
THRESHOLD = 3


def sql(sub: str) -> str:
    return (HERE / sub / "expected.sql").read_text()


def source_missing(cur, bbl: str) -> dict:
    cur.execute(sql("q17_1"), {"bbl": bbl})
    hpd_row, regs, bldgs, pluto = cur.fetchone()
    return {"missing": "does-not-hold" if hpd_row else "holds", "hpdRegistered": bool(hpd_row), "registrations": int(regs),
            "registeredBuildings": int(bldgs), "noUsable": bool(hpd_row) and int(regs) == 0, "plutoNumBuildings": pluto}


def source_registrations(cur, bbl: str) -> dict:
    cur.execute(sql("q17_2"), {"bbl": bbl})
    return {(b, int(rid)): {"lastRegistered": str(lr) if lr else None, "registrationEnd": str(re) if re else None} for b, rid, lr, re in cur.fetchall()}


def lapsed(regs: dict, as_of: str = AS_OF) -> str:
    ends = [r["registrationEnd"] for r in regs.values()]
    if not regs:
        return "cannot-tell"
    if any(e is not None and e >= as_of for e in ends):
        return "does-not-hold"
    if all(e is not None and e < as_of for e in ends):
        return "holds"
    return "cannot-tell"


def source_latest(cur, bbl: str) -> dict:
    cur.execute(sql("q17_3"), {"bbl": bbl, "types": DEED_TYPES})
    rows = cur.fetchall()
    deeds = {r[0]: {"type": r[1], "recorded": str(r[3]), "amount": int(r[4])} for r in rows if r[0]}
    latest = str(rows[0][5]) if rows and rows[0][5] else None
    return {"deeds": deeds, "latestRegistered": latest}


def older_than_deed(latest: dict) -> str:
    if not latest["deeds"] or latest["latestRegistered"] is None:
        return "cannot-tell"
    recorded = next(iter(latest["deeds"].values()))["recorded"]
    return "holds" if latest["latestRegistered"] < recorded else "does-not-hold"


def source_units(cur, bbl: str) -> dict | None:
    cur.execute(sql("q17_4"), {"bbl": bbl})
    row = cur.fetchone()
    return None if row is None else {"units": row[0], "yearBuilt": row[1]}


def threshold_outcome(units) -> str:
    if units is None or units == 0:
        return "units-not-recorded"
    return "meets-threshold" if units >= THRESHOLD else "below-threshold"


def graph_session(driver):
    return driver.session(database=os.environ["NEO4J_DATABASE"], default_access_mode="READ")
