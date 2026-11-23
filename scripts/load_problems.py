"""Load Q27 complaint problems: every HPD complaint problem received on or after 2021-01-01 on an HPD-registered lot whose BIN is a Building already
in the graph, as Problem nodes and Building-[:HAS_PROBLEM]->Problem.

Run after scripts/load_buildings.py. Rules (tests/q27_1/expected.sql):
  - Scope (decision 2026-11-19, user choice): problems received since 2021-01-01 whose BBL has a row in hpd_registrations and whose BIN is a Building
    in the graph. Earlier problems and problems with no usable or unregistered BIN are not loaded; the latter are excluded and counted.
  - Problem {problemId (unique), complaintId, problemType (as HPD records: EMERGENCY, NON EMERGENCY, IMMEDIATE EMERGENCY, HAZARDOUS, REFERRAL),
    majorCategory, minorCategory and problemCode (as HPD records them, text; Q27.3 pest extension), status ('OPEN' or 'CLOSE', the problem's own status at
    the snapshot), receivedDate, duplicate (HPD's duplicate flag, kept as recorded)}. Apartment, unit type, space type, anonymity and coordinates are not loaded.
Safe to rerun (MERGE). Reads the source read-only and writes only to the POC database. About 4.0M problems; takes several minutes.
Run: uv run python scripts/load_problems.py
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
SELECT c.problemid, c.complaintid, c.type, c.majorcategory, c.minorcategory, c.problemcode, c.problemstatus, c.receiveddate, c.problemduplicateflag, c.bin
FROM hpd_complaints_and_problems c JOIN (SELECT DISTINCT bbl FROM hpd_registrations WHERE bbl IS NOT NULL) rb ON rb.bbl = c.bbl
WHERE c.receiveddate >= DATE '2021-01-01'
ORDER BY c.problemid
"""
CONSTRAINT = "CREATE CONSTRAINT problem_id_unique IF NOT EXISTS FOR (p:Problem) REQUIRE p.problemId IS UNIQUE"
LOAD = """
UNWIND $rows AS row
MATCH (b:Building {bin: row.bin})
MERGE (p:Problem {problemId: row.id})
SET p.complaintId = row.complaint, p.problemType = row.type, p.majorCategory = row.major, p.minorCategory = row.minor, p.problemCode = row.code, p.status = row.status,
    p.receivedDate = date(row.received), p.duplicate = row.dup
MERGE (b)-[:HAS_PROBLEM]->(p)
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
            with pg.cursor(name="problems") as cur:
                cur.itersize = 20000
                cur.execute(SOURCE_SQL)
                for pid, cid, type_, major, minor, code, status, received, dup, bin_ in cur:
                    if bin_ not in bins:
                        excluded += 1
                        continue
                    batch.append({"id": int(pid), "complaint": int(cid), "type": type_, "major": major, "minor": minor, "code": code, "status": status,
                                  "received": received.isoformat(), "dup": bool(dup), "bin": bin_})
                    if len(batch) >= BATCH:
                        staged += len(batch)
                        linked += session.execute_write(lambda tx, b=batch: tx.run(LOAD, rows=b).single()["linked"])
                        batch = []
                        if (staged // BATCH) % 40 == 0:
                            print(f"  problems {staged:,} ({time.time() - started:.0f}s)", flush=True)
                if batch:
                    staged += len(batch)
                    linked += session.execute_write(lambda tx, b=batch: tx.run(LOAD, rows=b).single()["linked"])
        g = session.run("MATCH (b:Building)-[r:HAS_PROBLEM]->(p:Problem) RETURN count(r) AS links, count(DISTINCT p) AS problems").single()
    print(f"staged: problems {staged:,}, excluded (no registered building) {excluded:,}")
    print(f"graph:  problems {g['problems']:,}, HAS_PROBLEM {g['links']:,}")
    ok = linked == staged and (staged, staged) == (g["problems"], g["links"])
    print("reconciled" if ok else "MISMATCH between staged and graph counts", file=sys.stdout if ok else sys.stderr)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
