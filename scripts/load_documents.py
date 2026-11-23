"""Load Document nodes, DocumentParty nodes and HAS_PARTY relationships (Q7.3).

Run after scripts/load_registrations.py (CorporateOwner Contacts). Rules (see tests/q7_3/expected.sql):
  - Scope C (decision 2026-11-16): an ACRIS document is loaded when two or more distinct party names, normalized by rule N3
    (src/watchline/compare.py), equal the N3 name of a CorporateOwner Contact's corporation name. Every document type is loaded.
  - Document: documentId, docType, docDate, recordedDate, amount, from the current version (latest modifieddate, then
    goodthroughdate); absent when null.
  - DocumentParty: one per distinct party row (any partytype) of a loaded document (document, name, address1, address2, zip);
    values trimmed, blank is absent; nameKey = rule N3 of the name.
  - HAS_PARTY: one per (Document, DocumentParty, partytype), property partyType.
  - addressNames / addressDocuments: distinct N3 names and distinct documents over ALL ACRIS party rows at the same
    upper-cased street line and first five ZIP characters.

Q11.1 adds a second scope (scripts/load_mortgages.py, which calls main() here with MORTGAGE_SQL): current-version MTGE documents naming
at least one CorporateOwner name (rule N3). Both scopes use the same nodes, so a document in both loads once.

Safe to rerun (MERGE). Reads the source read-only and writes only to the POC database.
The scope and hub scans read all of real_property_parties (about 47M rows); allow several minutes.
Run: uv run python scripts/load_documents.py
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
CHUNK = 5000

OWNER_NAMES = "MATCH (c:Contact {contactType: 'CorporateOwner'}) WHERE c.corporationName IS NOT NULL RETURN DISTINCT c.corporationName AS n"
SQL_N3 = ("btrim(regexp_replace(replace(replace(replace(replace(upper(btrim({c})), '.', ''), ',', ' '), '''', ''), "
          "E'\\t', ' '), '\\s+', ' ', 'g'))")
SCOPE_SQL = f"""
WITH g AS (SELECT unnest(%(keys)s::text[]) AS k),
hits AS (SELECT p.documentid, {SQL_N3.format(c='p.name')} AS k FROM real_property_parties p WHERE p.name ~ '[A-Za-z]')
SELECT h.documentid FROM hits h JOIN g ON g.k = h.k GROUP BY h.documentid HAVING count(DISTINCT h.k) >= 2
"""
MASTER_SQL = """
SELECT DISTINCT ON (documentid) documentid, doctype, docdate, recordedfiled, docamount
FROM real_property_master WHERE documentid = ANY(%(docs)s)
ORDER BY documentid, modifieddate DESC NULLS LAST, goodthroughdate DESC NULLS LAST
"""
PARTIES_SQL = """
SELECT DISTINCT documentid, partytype, nullif(btrim(name), ''), nullif(btrim(address1), ''), nullif(btrim(address2), ''),
       nullif(btrim(zip), '')
FROM real_property_parties WHERE documentid = ANY(%(docs)s)
"""
HUB_SQL = f"""
WITH a AS (SELECT unnest(%(streets)s::text[]) AS s, unnest(%(zips)s::text[]) AS z)
SELECT upper(btrim(p.address1)), left(btrim(coalesce(p.zip, '')), 5),
       count(DISTINCT {SQL_N3.format(c='p.name')}) FILTER (WHERE p.name ~ '[A-Za-z]'), count(DISTINCT p.documentid)
FROM real_property_parties p JOIN a ON a.s = upper(btrim(p.address1)) AND a.z = left(btrim(coalesce(p.zip, '')), 5)
GROUP BY 1, 2
"""
# Q11.1 scope M (decision 2026-11-16): mortgages (current document type MTGE) naming at least one HPD corporate owner.
MORTGAGE_SQL = f"""
WITH g AS (SELECT unnest(%(keys)s::text[]) AS k),
cur AS (SELECT DISTINCT ON (documentid) documentid, doctype FROM real_property_master
        ORDER BY documentid, modifieddate DESC NULLS LAST, goodthroughdate DESC NULLS LAST),
hits AS (SELECT DISTINCT p.documentid FROM real_property_parties p JOIN g ON g.k = {SQL_N3.format(c='p.name')}
         WHERE p.name ~ '[A-Za-z]')
SELECT h.documentid FROM hits h JOIN cur c USING (documentid) WHERE c.doctype = 'MTGE'
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
LOAD_PARTIES = """
UNWIND $rows AS row
MATCH (d:Document {documentId: row.id})
MERGE (p:DocumentParty {partyKey: row.key})
SET p.name = row.name, p.nameKey = row.nameKey, p.mailingAddress = row.addr, p.addressLine2 = row.line2, p.zip = row.zip,
    p.addressNames = row.names, p.addressDocuments = row.docs
MERGE (d)-[r:HAS_PARTY {partyType: row.ptype}]->(p)
RETURN count(*) AS linked
"""
COUNTS = """
CALL () { MATCH (d:Document) RETURN count(d) AS documents }
CALL () { MATCH (p:DocumentParty) RETURN count(p) AS parties, count(p.name) AS named, count(p.mailingAddress) AS with_addr,
                 count(p.addressNames) AS with_hub }
CALL () { MATCH (:Document)-[r:HAS_PARTY]->(:DocumentParty) RETURN count(r) AS links }
RETURN documents, parties, named, with_addr, with_hub, links
"""


def chunks(seq, n):
    for i in range(0, len(seq), n):
        yield seq[i:i + n]


def main(scope_sql: str = SCOPE_SQL, label: str = "scope C") -> int:
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

    with driver, driver.session(database=POC_DATABASE) as session:
        for c in CONSTRAINTS:
            session.run(c).consume()
        keys = sorted({k for r in session.run(OWNER_NAMES) if (k := n3(r["n"]))})
        if not keys:
            print("no CorporateOwner contacts: run scripts/load_registrations.py first", file=sys.stderr)
            return 1
        print(f"owner name keys (N3): {len(keys):,}", flush=True)
        with psycopg.connect(os.environ["JUSTFIX_DATABASE_URL"]) as pg:
            pg.read_only = True
            with pg.cursor() as cur:
                cur.execute("SET statement_timeout = 0")
                cur.execute(scope_sql, {"keys": keys})
                docs = sorted(r[0] for r in cur.fetchall())
                print(f"{label} documents: {len(docs):,} ({time.time() - started:.0f}s)", flush=True)

                master = []
                for part in chunks(docs, CHUNK):
                    cur.execute(MASTER_SQL, {"docs": part})
                    master += [{"id": i, "type": t, "docdate": d.isoformat() if d else None,
                                "recorded": r.isoformat() if r else None, "amount": a} for i, t, d, r, a in cur.fetchall()]
                for part in chunks(master, CHUNK):
                    session.execute_write(lambda tx, b=part: tx.run(LOAD_DOCS, rows=b).consume())
                print(f"documents loaded: {len(master):,} ({time.time() - started:.0f}s)", flush=True)

                parties = []
                for part in chunks(docs, CHUNK):
                    cur.execute(PARTIES_SQL, {"docs": part})
                    parties += cur.fetchall()
                addrs = sorted({(a.upper(), (z or "")[:5]) for _, _, _, a, _, z in parties if a})
                hub = {}
                for part in chunks(addrs, 100000):
                    cur.execute(HUB_SQL, {"streets": [a for a, _ in part], "zips": [z for _, z in part]})
                    hub.update({(s, z): (n, d) for s, z, n, d in cur.fetchall()})
                print(f"party rows {len(parties):,}, addresses {len(addrs):,} hub-counted ({time.time() - started:.0f}s)", flush=True)

        rows, parties_keys, linked, with_hub = [], set(), 0, 0
        for doc, ptype, name, a1, a2, zip_ in parties:
            key = f"{doc}|{name or ''}|{a1 or ''}|{a2 or ''}|{zip_ or ''}"
            h = hub.get((a1.upper(), (zip_ or "")[:5])) if a1 else None
            parties_keys.add(key)
            with_hub += 1 if h else 0
            rows.append({"id": doc, "ptype": int(ptype), "key": key, "name": name, "nameKey": n3(name) if name else None,
                         "addr": a1, "line2": a2, "zip": zip_, "names": h[0] if h else None, "docs": h[1] if h else None})
        for part in chunks(rows, CHUNK):
            linked += session.execute_write(lambda tx, b=part: tx.run(LOAD_PARTIES, rows=b).single()["linked"])
        g = session.run(COUNTS).single()

    named = len({r["key"] for r in rows if r["name"]})
    print(f"staged ({label}): documents {len(master):,}, parties {len(parties_keys):,} (named {named:,}), party links {len(rows):,}")
    print(f"graph (all scopes): documents {g['documents']:,}, parties {g['parties']:,} (named {g['named']:,}, with address {g['with_addr']:,}, "
          f"with hub count {g['with_hub']:,}), HAS_PARTY {g['links']:,}")
    ok = linked == len(rows) and len(master) == len(docs) and g["documents"] >= len(master) and g["links"] >= len(rows)
    print("reconciled (the checks reconcile the graph totals per scope)" if ok else "MISMATCH between staged and loaded counts",
          file=sys.stdout if ok else sys.stderr)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
