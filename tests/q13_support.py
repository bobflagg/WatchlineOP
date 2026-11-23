"""Shared helpers for the Q13 checks: derive financing documents from the frozen source (tests/q13_1 and q13_2 expected.sql), independent of the graph."""

import os
import sys
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from neo4j import GraphDatabase

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

REQUIRED_ENV = ("JUSTFIX_DATABASE_URL", "NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD", "NEO4J_DATABASE")
FINANCING_TYPES = ["MTGE", "ASST", "SAT", "AGMT", "AL&R", "TL&R", "SAGE"]
# Answer contract (Q13.3): kind and description by document type. The descriptions are the project's wording for the codes
# (acris_document_codes is unusable locally); they are not official ACRIS text.
KINDS = {"MTGE": ("mortgage", "mortgage"), "ASST": ("assignment", "assignment of mortgage"), "AL&R": ("assignment", "assignment of leases and rents"),
         "SAT": ("satisfaction", "satisfaction of mortgage"), "TL&R": ("termination", "termination of assignment of leases and rents"),
         "AGMT": ("agreement", "agreement"), "SAGE": ("agreement", "sundry agreement")}
DOCS_SQL = (ROOT / "tests" / "q13_1" / "expected.sql").read_text()
PARTIES_SQL = (ROOT / "tests" / "q13_2" / "expected.sql").read_text()
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


def source_documents(cur, bbl: str) -> dict:
    """{documentId: {type, docdate, recorded, amount, lots}} for the financing documents of one lot, from the frozen source."""
    cur.execute(DOCS_SQL, {"bbls": [bbl], "types": FINANCING_TYPES})
    return {doc: {"type": t, "docdate": str(dd) if dd else None, "recorded": str(rec) if rec else None, "amount": int(a), "lots": list(lots)}
            for doc, t, dd, rec, a, lots in cur.fetchall()}


def source_parties(cur, docs) -> dict:
    """{documentId: sorted [(partyType, name, address1, address2, zip)]} of distinct party rows, blank as None."""
    cur.execute(PARTIES_SQL, {"docs": list(docs)})
    out: dict = {d: [] for d in docs}
    for doc, pt, name, a1, a2, zip_ in cur.fetchall():
        out[doc].append((int(pt), name, a1, a2, zip_))
    return {d: sorted(v, key=lambda r: tuple("" if x is None else str(x) for x in r)) for d, v in out.items()}


def party_rows(parties) -> list:
    rows = [(int(p["partyType"]), p["name"], p["mailingAddress"], p["addressLine2"], p["zip"]) for p in parties if p is not None]
    return sorted(rows, key=lambda r: tuple("" if x is None else str(x) for x in r))
