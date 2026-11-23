"""Load Q13 financing documents: every ACRIS document of a financing type recorded against a Lot already in the graph, with all its
party rows, as Document, DocumentParty, HAS_PARTY (the Q7.3 elements) and Lot-[:HAS_FINANCING_DOCUMENT]->Document.

Run after scripts/load_lots.py. Rules (tests/q13_1/expected.sql, tests/q13_2/expected.sql):
  - Scope F (decision 2026-11-17, user choice): financing types MTGE, ASST, SAT, AGMT, AL&R, TL&R, SAGE, tested on the document's current
    version (latest modifieddate, then goodthroughdate); a document is linked to every graph lot it names (distinct (BBL, documentid)).
  - Document and DocumentParty fields and keys are exactly those of scripts/load_documents.py. Party hub counts (addressNames,
    addressDocuments) are NOT set here and existing ones are never overwritten: they exist only on parties of scopes C and M.
  - Both scopes use the same nodes, so a document that is also in scope C or M loads once.
Safe to rerun (MERGE). Reads the source read-only and writes only to the POC database. Allow an hour or more (about 2.9M documents).
Run: uv run python scripts/load_financing.py
"""

import os
import sys
import time
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from neo4j import GraphDatabase

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from watchline.compare import n3  # noqa: E402

POC_DATABASE = "watchline"
REQUIRED_ENV = ("JUSTFIX_DATABASE_URL", "NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD", "NEO4J_DATABASE")
LOT_CHUNK = 1000
PARTY_CHUNK = 5000
FINANCING_TYPES = ("MTGE", "ASST", "SAT", "AGMT", "AL&R", "TL&R", "SAGE")

DOCS_SQL = """
WITH docs AS (SELECT DISTINCT documentid FROM real_property_legals WHERE bbl = ANY(%(bbls)s)),
cur AS (
    SELECT DISTINCT ON (m.documentid) m.documentid, m.doctype, m.docdate, m.recordedfiled, m.docamount
    FROM real_property_master m JOIN docs d ON d.documentid = m.documentid
    ORDER BY m.documentid, m.modifieddate DESC NULLS LAST, m.goodthroughdate DESC NULLS LAST
)
SELECT documentid, doctype, docdate, recordedfiled, docamount FROM cur WHERE doctype = ANY(%(types)s)
"""
PAIRS_SQL = """
SELECT DISTINCT l.bbl::text, l.documentid FROM real_property_legals l WHERE l.bbl = ANY(%(bbls)s) AND l.documentid = ANY(%(docs)s)
"""
PARTIES_SQL = """
SELECT DISTINCT documentid, partytype, nullif(btrim(name), ''), nullif(btrim(address1), ''), nullif(btrim(address2), ''),
       nullif(btrim(zip), '')
FROM real_property_parties WHERE documentid = ANY(%(docs)s)
"""
CONSTRAINTS = [
    "CREATE CONSTRAINT document_id_unique IF NOT EXISTS FOR (d:Document) REQUIRE d.documentId IS UNIQUE",
    "CREATE CONSTRAINT document_party_key_unique IF NOT EXISTS FOR (p:DocumentParty) REQUIRE p.partyKey IS UNIQUE",
    "CREATE INDEX document_party_name_key IF NOT EXISTS FOR (p:DocumentParty) ON (p.nameKey)",
]
LOAD_DOCS = """
UNWIND $rows AS row
MERGE (d:Document {documentId: row.id})
SET d.docType = row.type, d.docDate = CASE WHEN row.docdate IS NULL THEN null ELSE date(row.docdate) END,
    d.recordedDate = CASE WHEN row.recorded IS NULL THEN null ELSE date(row.recorded) END, d.amount = row.amount
"""
LOAD_PAIRS = """
UNWIND $rows AS row
MATCH (l:Lot {bbl: row.bbl})
MATCH (d:Document {documentId: row.id})
MERGE (l)-[:HAS_FINANCING_DOCUMENT]->(d)
RETURN count(*) AS linked
"""
LOAD_PARTIES = """
UNWIND $rows AS row
MATCH (d:Document {documentId: row.id})
MERGE (p:DocumentParty {partyKey: row.key})
SET p.name = row.name, p.nameKey = row.nameKey, p.mailingAddress = row.addr, p.addressLine2 = row.line2, p.zip = row.zip
MERGE (d)-[:HAS_PARTY {partyType: row.ptype}]->(p)
RETURN count(*) AS linked
"""
COUNTS = """
CALL () { MATCH (:Lot)-[h:HAS_FINANCING_DOCUMENT]->(d:Document) RETURN count(h) AS pairs, count(DISTINCT d) AS documents }
CALL () { MATCH (d:Document)<-[:HAS_FINANCING_DOCUMENT]-() WITH DISTINCT d MATCH (d)-[r:HAS_PARTY]->() RETURN count(r) AS links }
RETURN pairs, documents, links
"""


def chunks(seq, n):
    for i in range(0, len(seq), n):
        yield seq[i:i + n]


def main() -> int:
    load_dotenv(ROOT / ".env")
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

    seen: set[str] = set()
    staged_pairs = linked_pairs = staged_links = linked_links = 0
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
                cur.execute("SET statement_timeout = 0")
                for n, part in enumerate(chunks(bbls, LOT_CHUNK), 1):
                    cur.execute(DOCS_SQL, {"bbls": part, "types": list(FINANCING_TYPES)})
                    rows = [{"id": i, "type": t, "docdate": d.isoformat() if d else None,
                             "recorded": r.isoformat() if r else None, "amount": a} for i, t, d, r, a in cur.fetchall()]
                    if rows:
                        session.execute_write(lambda tx, b=rows: tx.run(LOAD_DOCS, rows=b).consume())
                        ids = [r["id"] for r in rows]
                        cur.execute(PAIRS_SQL, {"bbls": part, "docs": ids})
                        pairs = [{"bbl": b, "id": i} for b, i in cur.fetchall()]
                        staged_pairs += len(pairs)
                        linked_pairs += session.execute_write(lambda tx, p=pairs: tx.run(LOAD_PAIRS, rows=p).single()["linked"])
                        new = [i for i in ids if i not in seen]
                        seen.update(new)
                        for sub in chunks(new, PARTY_CHUNK):
                            cur.execute(PARTIES_SQL, {"docs": sub})
                            batch = [{"id": i, "ptype": int(pt), "name": nm, "nameKey": n3(nm) if nm else None, "addr": a, "line2": l,
                                      "zip": z, "key": f"{i}|{nm or ''}|{a or ''}|{l or ''}|{z or ''}"}
                                     for i, pt, nm, a, l, z in cur.fetchall()]
                            staged_links += len(batch)
                            linked_links += session.execute_write(lambda tx, b=batch: tx.run(LOAD_PARTIES, rows=b).single()["linked"])
                    if n % 20 == 0:
                        print(f"  lots {min(n * LOT_CHUNK, len(bbls)):,}/{len(bbls):,}, documents {len(seen):,}, party links {staged_links:,} "
                              f"({time.time() - started:.0f}s)", flush=True)
        g = session.run(COUNTS).single()

    print(f"staged: documents {len(seen):,}, lot-document pairs {staged_pairs:,}, party links {staged_links:,}")
    print(f"graph:  financing documents {g['documents']:,}, HAS_FINANCING_DOCUMENT {g['pairs']:,}, their HAS_PARTY {g['links']:,}")
    ok = (linked_pairs == staged_pairs and linked_links == staged_links
          and (len(seen), staged_pairs, staged_links) == (g["documents"], g["pairs"], g["links"]))
    print("reconciled" if ok else "MISMATCH between staged and graph counts", file=sys.stdout if ok else sys.stderr)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
