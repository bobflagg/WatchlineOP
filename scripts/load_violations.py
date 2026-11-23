"""Load Q15 violations: every HPD violation on an HPD-registered lot whose BIN is a Building already in the graph, as Violation nodes and
Building-[:HAS_VIOLATION]->Violation.

Run after scripts/load_buildings.py. Rules (tests/q15_1/expected.sql):
  - Scope (decision 2026-11-18, user choice): violations whose BBL has a row in hpd_registrations and whose BIN is a Building in the graph
    (valid BIN, registered). Other violations on registered lots (no usable BIN, or a BIN that is not a registered building) are excluded and counted.
  - Violation {violationId (unique), violationClass (A, B, C, I), status ('Open' or 'Close', as HPD records), inspectionDate, orderNumber}. The status is
    as of the snapshot (data through 2026-07-02). orderNumber is HPD's order code as recorded (text, present on every loaded row; Q15.3 pest
    extension, data/hpd_pest_orders.yaml). The apartment column, the description and the other source columns are not loaded.
Safe to rerun (MERGE). Reads the source read-only and writes only to the POC database. About 1.9M violations; takes a couple of minutes.
Run: uv run python scripts/load_violations.py
"""

import os
import sys
import time
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from neo4j import GraphDatabase

ROOT = Path(__file__).resolve().parent.parent
POC_DATABASE = "watchline"
REQUIRED_ENV = ("JUSTFIX_DATABASE_URL", "NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD", "NEO4J_DATABASE")
BATCH = 5000

SOURCE_SQL = """
SELECT v.violationid, v.class, v.violationstatus, v.inspectiondate::date, v.bin, v.ordernumber
FROM hpd_violations v JOIN (SELECT DISTINCT bbl FROM hpd_registrations WHERE bbl IS NOT NULL) rb ON rb.bbl = v.bbl
ORDER BY v.violationid
"""
CONSTRAINT = "CREATE CONSTRAINT violation_id_unique IF NOT EXISTS FOR (v:Violation) REQUIRE v.violationId IS UNIQUE"
LOAD = """
UNWIND $rows AS row
MATCH (b:Building {bin: row.bin})
MERGE (v:Violation {violationId: row.id})
SET v.violationClass = row.cls, v.status = row.status, v.inspectionDate = date(row.inspected), v.orderNumber = row.orderNumber
MERGE (b)-[:HAS_VIOLATION]->(v)
RETURN count(*) AS linked
"""


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
    staged = linked = excluded = 0
    with driver, driver.session(database=POC_DATABASE) as session:
        session.run(CONSTRAINT).consume()
        bins = {r["bin"] for r in session.run("MATCH (b:Building) RETURN b.bin AS bin")}
        if not bins:
            print("no Building nodes: run scripts/load_buildings.py first", file=sys.stderr)
            return 1
        batch: list[dict] = []
        with psycopg.connect(os.environ["JUSTFIX_DATABASE_URL"]) as pg:
            pg.read_only = True
            with pg.cursor(name="violations") as cur:
                cur.itersize = 20000
                cur.execute(SOURCE_SQL)
                for vid, cls, status, inspected, bin_, order_ in cur:
                    if bin_ not in bins:
                        excluded += 1
                        continue
                    batch.append({"id": int(vid), "cls": cls, "status": status, "inspected": inspected.isoformat(), "bin": bin_, "orderNumber": order_})
                    if len(batch) >= BATCH:
                        staged += len(batch)
                        linked += session.execute_write(lambda tx, b=batch: tx.run(LOAD, rows=b).single()["linked"])
                        batch = []
                        if (staged // BATCH) % 40 == 0:
                            print(f"  violations {staged:,} ({time.time() - started:.0f}s)", flush=True)
                if batch:
                    staged += len(batch)
                    linked += session.execute_write(lambda tx, b=batch: tx.run(LOAD, rows=b).single()["linked"])
        g = session.run("MATCH (b:Building)-[r:HAS_VIOLATION]->(v:Violation) RETURN count(r) AS links, count(DISTINCT v) AS violations").single()
    print(f"staged: violations {staged:,}, excluded (no registered building) {excluded:,}")
    print(f"graph:  violations {g['violations']:,}, HAS_VIOLATION {g['links']:,}")
    ok = linked == staged and (staged, staged) == (g["violations"], g["links"])
    print("reconciled" if ok else "MISMATCH between staged and graph counts", file=sys.stdout if ok else sys.stderr)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
