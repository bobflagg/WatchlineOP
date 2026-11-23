"""Shared helpers for the Q14 checks: derive the title holder and registration status on a date from the frozen source, independent of the graph."""

import os
import sys
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from neo4j import GraphDatabase

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from watchline.compare import n3  # noqa: E402,F401

REQUIRED_ENV = ("JUSTFIX_DATABASE_URL", "NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD", "NEO4J_DATABASE")
DEED_TYPES = ["DEED", "DEED, TS", "DEED, LE", "DEED, RC", "DEEDO", "DEEDP", "CORRD", "CONDEED"]
TITLE_SQL = (ROOT / "tests" / "q14_1" / "expected.sql").read_text()
REG_SQL = (ROOT / "tests" / "q14_2" / "expected.sql").read_text()
results: list[bool] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  ({detail})" if detail and not ok else ""))


def finish() -> int:
    failed = results.count(False)
    print(f"{len(results) - failed}/{len(results)} checks passed")
    return 0 if failed == 0 else 1


def connect():
    load_dotenv(ROOT / ".env")
    missing = [k for k in REQUIRED_ENV if not os.environ.get(k)]
    if missing:
        print(f"missing in .env: {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)
    driver = GraphDatabase.driver(os.environ["NEO4J_URI"], auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]))
    pg = psycopg.connect(os.environ["JUSTFIX_DATABASE_URL"])
    pg.read_only = True
    return driver, pg


def source_title(cur, bbl: str, date: str, basis: str) -> dict:
    """{documentId: {type, docdate, recorded, amount, docDateAbsent, recordedAfterDate, confirmatory, grantees: set of names}}."""
    cur.execute(TITLE_SQL, {"bbls": [bbl], "date": date, "basis": basis, "types": DEED_TYPES})
    out: dict = {}
    for _bbl, doc, typ, docdate, rec, amt, _eff, absent, after, conf, grantee in cur.fetchall():
        d = out.setdefault(doc, {"type": typ, "docdate": str(docdate) if docdate else None, "recorded": str(rec), "amount": int(amt),
                                 "docDateAbsent": bool(absent), "recordedAfterDate": bool(after), "confirmatory": bool(conf), "grantees": set()})
        if grantee:
            d["grantees"].add(grantee)
    return out


def source_registrations(cur, bbl: str, date: str) -> dict:
    """{(bin, registrationId): {lastRegistered, registrationEnd, status, corporateKeys: set, hasIndividualOwner}}."""
    cur.execute(REG_SQL, {"bbls": [bbl], "date": date})
    return {(b, int(rid)): {"lastRegistered": str(lr) if lr else None, "registrationEnd": str(re) if re else None, "status": st,
                            "corporateKeys": set(keys or []), "hasIndividualOwner": bool(ind)}
            for _bbl, b, rid, lr, re, st, keys, ind in cur.fetchall()}


def relation(title: dict, regs: dict) -> str:
    """Q14.3: how the supporting deeds' grantees relate to the owners of the registrations in force (a computed name lead, rule N3)."""
    if not title:
        return "no-title-record"
    inforce = [r for r in regs.values() if r["status"] == "in-force"]
    if not inforce:
        return "no-registration-in-force"
    owners = set().union(*(r["corporateKeys"] for r in inforce))
    grantees = {k for d in title.values() for g in d["grantees"] if (k := n3(g))}
    if not owners or not grantees:
        return "not-comparable"
    return "coincide" if owners & grantees else "differ"
