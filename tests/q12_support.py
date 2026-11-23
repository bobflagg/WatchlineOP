"""Shared helpers for the Q12 checks: derive deeds from the frozen source (tests/q12_1/expected.sql) independent of the graph."""

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
NOT_SALE_TYPES = {"CORRD", "CONDEED"}
EXPECTED = (ROOT / "tests" / "q12_1" / "expected.sql").read_text()
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


def source_deeds(cur, bbls, start=None, end=None) -> dict:
    """{documentId: {type, docdate, recorded, amount, lots, grantors, grantees, notSale}} from the frozen source."""
    cur.execute(EXPECTED, {"bbls": list(bbls), "types": DEED_TYPES, "start": start, "end": end})
    out: dict = {}
    for doc, typ, docdate, rec, amt, lots, ptype, name, a1, a2, zip_ in cur.fetchall():
        d = out.setdefault(doc, {"type": typ, "docdate": str(docdate) if docdate else None, "recorded": str(rec), "amount": int(amt),
                                 "lots": list(lots), "grantors": [], "grantees": [],
                                 "notSale": int(amt) == 0 or typ in NOT_SALE_TYPES})
        if ptype == 1:
            d["grantors"].append((name, a1, a2, zip_))
        elif ptype == 2:
            d["grantees"].append((name, a1, a2, zip_))
    for d in out.values():
        d["grantors"].sort(key=lambda r: tuple("" if x is None else x for x in r))
        d["grantees"].sort(key=lambda r: tuple("" if x is None else x for x in r))
    return out


def party_tuples(parties) -> list:
    rows = [(p["name"], p["mailingAddress"], p["addressLine2"], p["zip"]) for p in parties if p is not None]
    return sorted(rows, key=lambda r: tuple("" if x is None else x for x in r))
