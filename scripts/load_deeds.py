"""Load Deed nodes, Lot-[:HAS_DEED]->Deed relationships and Grantee nodes (Q3.1, Q3.2).

Run after scripts/load_lots.py. Rules (see tests/q3_1/expected.sql and tests/q3_2/expected.sql):
  - Scope: every ACRIS document of a deed type recorded against a Lot already in the graph.
  - Deed types (decision 2026-11-12): DEED, DEED TS, DEED LE, DEED RC, DEEDO, DEEDP, CORRD, CONDEED.
    DEED COR is an index-correction code, not a deed, and is excluded.
  - real_property_master repeats a documentid (14,957 documents). The row with the latest modifieddate (then
    goodthroughdate) is the document's current version; the type test is applied to that version. No ties occur.
  - Deed: documentId, docType, docDate (absent when null), recordedDate, amount (0 kept as recorded; it does not
    mean a free sale).
  - HAS_DEED: one per distinct (BBL, documentid) in real_property_legals. A deed can sit on several lots.
  - Grantee: one per distinct party row of partytype 2 on a loaded deed (same document, name and address are one).
    name, mailingAddress (address1), addressLine2 (address2) and zip are as recorded, blank is absent.
    Grantors are not loaded (decision 2026-11-12).

Safe to rerun (MERGE). Reads the source read-only and writes only to the POC database.
Run: uv run python scripts/load_deeds.py
"""

import os
import sys
import time
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from neo4j import GraphDatabase

POC_DATABASE = "watchline"
REQUIRED_ENV = ("JUSTFIX_DATABASE_URL", "NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD", "NEO4J_DATABASE")
LOT_CHUNK = 2000
PARTY_CHUNK = 5000
DEED_TYPES = ("DEED", "DEED, TS", "DEED, LE", "DEED, RC", "DEEDO", "DEEDP", "CORRD", "CONDEED")

DEEDS_SQL = """
WITH docs AS (SELECT DISTINCT documentid FROM real_property_legals WHERE bbl = ANY(%(bbls)s)),
cur AS (
    SELECT DISTINCT ON (m.documentid) m.documentid, m.doctype, m.docdate, m.recordedfiled, m.docamount
    FROM real_property_master m JOIN docs d ON d.documentid = m.documentid
    ORDER BY m.documentid, m.modifieddate DESC NULLS LAST, m.goodthroughdate DESC NULLS LAST
)
SELECT documentid, doctype, docdate, recordedfiled, docamount FROM cur WHERE doctype = ANY(%(types)s)
"""
PAIRS_SQL = """
SELECT DISTINCT l.bbl::text, l.documentid FROM real_property_legals l
WHERE l.bbl = ANY(%(bbls)s) AND l.documentid = ANY(%(docs)s)
"""
GRANTEES_SQL = """
SELECT DISTINCT documentid, nullif(btrim(name), ''), nullif(btrim(address1), ''), nullif(btrim(address2), ''), nullif(btrim(zip), '')
FROM real_property_parties WHERE partytype = 2 AND documentid = ANY(%(docs)s)
"""
CONSTRAINTS = [
    "CREATE CONSTRAINT deed_document_id_unique IF NOT EXISTS FOR (d:Deed) REQUIRE d.documentId IS UNIQUE",
    "CREATE CONSTRAINT grantee_key_unique IF NOT EXISTS FOR (g:Grantee) REQUIRE g.partyKey IS UNIQUE",
]
LOAD_DEEDS = """
UNWIND $rows AS row
MERGE (d:Deed {documentId: row.id})
SET d.docType = row.type, d.docDate = CASE WHEN row.docdate IS NULL THEN null ELSE date(row.docdate) END,
    d.recordedDate = date(row.recorded), d.amount = row.amount
"""
LOAD_PAIRS = """
UNWIND $rows AS row
MATCH (l:Lot {bbl: row.bbl})
MATCH (d:Deed {documentId: row.id})
MERGE (l)-[:HAS_DEED]->(d)
RETURN count(*) AS linked
"""
LOAD_GRANTEES = """
UNWIND $rows AS row
MATCH (d:Deed {documentId: row.id})
MERGE (g:Grantee {partyKey: row.key})
SET g.name = row.name, g.mailingAddress = row.addr, g.addressLine2 = row.line2, g.zip = row.zip
MERGE (d)-[:HAS_GRANTEE]->(g)
RETURN count(*) AS linked
"""
COUNTS = """
CALL () { MATCH (d:Deed) RETURN count(d) AS deeds, count(d.docDate) AS with_docdate }
CALL () { MATCH (:Lot)-[h:HAS_DEED]->(:Deed) RETURN count(h) AS pairs }
CALL () { MATCH (g:Grantee) RETURN count(g) AS grantees, count(g.name) AS named, count(g.mailingAddress) AS with_addr }
RETURN deeds, with_docdate, pairs, grantees, named, with_addr
"""


def chunks(seq, n):
    for i in range(0, len(seq), n):
        yield seq[i:i + n]


def main() -> int:
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    missing = [k for k in REQUIRED_ENV if not os.environ.get(k)]
    if missing:
        print(f"missing in .env: {', '.join(missing)}", file=sys.stderr)
        return 1
    if os.environ["NEO4J_DATABASE"] != POC_DATABASE:
        print(f"refusing: NEO4J_DATABASE is not the POC database '{POC_DATABASE}'", file=sys.stderr)
        return 1

    started = time.time()
    driver = GraphDatabase.driver(os.environ["NEO4J_URI"], auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]))
    try:
        driver.verify_connectivity()
    except Exception as exc:
        print(f"cannot reach Neo4j ({type(exc).__name__}). Is the DBMS started in Neo4j Desktop?", file=sys.stderr)
        return 1

    deed_ids: set[str] = set()
    staged_pairs = linked_pairs = 0
    with driver, driver.session(database=POC_DATABASE) as session:
        for c in CONSTRAINTS:
            session.run(c).consume()
        bbls = [r["bbl"] for r in session.run("MATCH (l:Lot) RETURN l.bbl AS bbl ORDER BY bbl")]
        if not bbls:
            print("no Lot nodes: run scripts/load_lots.py first", file=sys.stderr)
            return 1
        with psycopg.connect(os.environ["JUSTFIX_DATABASE_URL"]) as pg:
            pg.read_only = True
            with pg.cursor() as cur:
                for n, part in enumerate(chunks(bbls, LOT_CHUNK), 1):
                    cur.execute(DEEDS_SQL, {"bbls": part, "types": list(DEED_TYPES)})
                    deeds = cur.fetchall()
                    rows = [{"id": i, "type": t, "docdate": d.isoformat() if d else None,
                             "recorded": r.isoformat(), "amount": a} for i, t, d, r, a in deeds]
                    session.execute_write(lambda tx, b=rows: tx.run(LOAD_DEEDS, rows=b).consume())
                    deed_ids |= {r["id"] for r in rows}
                    if rows:
                        cur.execute(PAIRS_SQL, {"bbls": part, "docs": [r["id"] for r in rows]})
                        pairs = [{"bbl": b, "id": i} for b, i in cur.fetchall()]
                        staged_pairs += len(pairs)
                        linked_pairs += session.execute_write(lambda tx, p=pairs: tx.run(LOAD_PAIRS, rows=p).single()["linked"])
                    if n % 10 == 0:
                        print(f"  lots {n * LOT_CHUNK:,}/{len(bbls):,}, deeds {len(deed_ids):,} ({time.time() - started:.0f}s)", flush=True)
                print(f"  deeds loaded: {len(deed_ids):,}, pairs {staged_pairs:,} ({time.time() - started:.0f}s)", flush=True)

                staged_grantees = staged_named = staged_addr = linked_grantees = 0
                for part in chunks(sorted(deed_ids), PARTY_CHUNK):
                    cur.execute(GRANTEES_SQL, {"docs": part})
                    batch = [{"id": i, "name": n, "addr": a, "line2": l, "zip": z,
                              "key": f"{i}|{n or ''}|{a or ''}|{l or ''}|{z or ''}"} for i, n, a, l, z in cur.fetchall()]
                    staged_grantees += len(batch)
                    staged_named += sum(1 for b in batch if b["name"])
                    staged_addr += sum(1 for b in batch if b["addr"])
                    linked_grantees += session.execute_write(lambda tx, b=batch: tx.run(LOAD_GRANTEES, rows=b).single()["linked"])
        g = session.run(COUNTS).single()

    print(f"staged: deeds {len(deed_ids):,}, lot-deed pairs {staged_pairs:,}, grantees {staged_grantees:,} "
          f"(named {staged_named:,}, with address {staged_addr:,})")
    print(f"graph:  deeds {g['deeds']:,} (document date {g['with_docdate']:,}), HAS_DEED {g['pairs']:,}, "
          f"grantees {g['grantees']:,} (named {g['named']:,}, with address {g['with_addr']:,})")
    ok = (linked_pairs == staged_pairs and linked_grantees == staged_grantees
          and (len(deed_ids), staged_pairs, staged_grantees, staged_named, staged_addr)
          == (g["deeds"], g["pairs"], g["grantees"], g["named"], g["with_addr"]))
    print("reconciled" if ok else "MISMATCH between staged and graph counts", file=sys.stdout if ok else sys.stderr)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
