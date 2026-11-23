"""Load Q28 litigation: every HPD Housing Court case on a registered building, as Litigation nodes and Building-[:HAS_LITIGATION]->Litigation.

Run after scripts/load_buildings.py. Rules (tests/q28_1/expected.sql):
  - Scope: cases whose BIN is a Building in the graph (valid BIN, HPD-registered). Cases on registered lots with no usable BIN or a BIN that is not a
    registered building are excluded and counted.
  - Litigation {litigationId (unique), caseType, caseOpenDate, caseStatus, openJudgement, harassmentFinding, findingDate, penalty, respondent,
    respondentKeys}. Values are as HPD records them; a blank or null is absent. A date the source holds that cannot be right (before 1990 or after the
    snapshot) is kept as recorded and counted by the check, never corrected. respondent is the recorded string; respondentKeys are the N3 keys of its
    comma-separated parts (a derived lead for matching, never a finding of identity); absent, not an empty list, when there are none.
  - penalty is whole dollars (integer) as recorded. Case addresses, coordinates and the other source columns are not loaded.
Safe to rerun (MERGE). Reads the source read-only and writes only to the POC database. About 210,000 cases.
Run: uv run python scripts/load_litigations.py
"""

import os
import sys
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from neo4j import GraphDatabase

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from watchline.compare import n3  # noqa: E402

POC_DATABASE = "watchline"
REQUIRED_ENV = ("JUSTFIX_DATABASE_URL", "NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD", "NEO4J_DATABASE")
BATCH = 5000

SOURCE_SQL = """
SELECT l.litigationid, l.bin, nullif(btrim(l.casetype), ''), l.caseopendate::date, nullif(btrim(l.casestatus), ''), nullif(btrim(l.openjudgement), ''),
       nullif(btrim(l.findingofharassment), ''), l.findingdate::date, nullif(btrim(l.penalty), ''), nullif(btrim(l.respondent), '')
FROM hpd_litigations l JOIN (SELECT DISTINCT bbl FROM hpd_registrations WHERE bbl IS NOT NULL) rb ON rb.bbl = l.bbl
ORDER BY l.litigationid
"""
CONSTRAINT = "CREATE CONSTRAINT litigation_id_unique IF NOT EXISTS FOR (c:Litigation) REQUIRE c.litigationId IS UNIQUE"
LOAD = """
UNWIND $rows AS row
MATCH (b:Building {bin: row.bin})
MERGE (c:Litigation {litigationId: row.id})
SET c.caseType = row.caseType, c.caseOpenDate = CASE WHEN row.opened IS NULL THEN null ELSE date(row.opened) END, c.caseStatus = row.status,
    c.openJudgement = row.judgement, c.harassmentFinding = row.finding,
    c.findingDate = CASE WHEN row.found IS NULL THEN null ELSE date(row.found) END, c.penalty = row.penalty,
    c.respondent = row.respondent, c.respondentKeys = row.keys
MERGE (b)-[:HAS_LITIGATION]->(c)
RETURN count(*) AS linked
"""


def keys(respondent: str | None) -> list[str]:
    if not respondent:
        return []
    return sorted({k for p in respondent.split(",") if (k := n3(p))})


def main() -> int:
    load_dotenv(ROOT / ".env")
    missing = [k for k in REQUIRED_ENV if not os.environ.get(k)]
    if missing:
        print(f"missing in .env: {', '.join(missing)}", file=sys.stderr)
        return 1
    if os.environ["NEO4J_DATABASE"] != POC_DATABASE:
        print(f"refusing: NEO4J_DATABASE is not the POC database '{POC_DATABASE}'", file=sys.stderr)
        return 1
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
            with pg.cursor(name="litigations") as cur:
                cur.itersize = 20000
                cur.execute(SOURCE_SQL)
                for lid, bin_, ctype, opened, status, judgement, finding, found, penalty, respondent in cur:
                    if bin_ not in bins:
                        excluded += 1
                        continue
                    batch.append({"id": int(lid), "bin": bin_, "caseType": ctype, "opened": opened.isoformat() if opened else None, "status": status,
                                  "judgement": judgement, "finding": finding, "found": found.isoformat() if found else None,
                                  "penalty": int(penalty) if penalty and penalty.isdigit() else None, "respondent": respondent, "keys": keys(respondent) or None})
                    if len(batch) >= BATCH:
                        staged += len(batch)
                        linked += session.execute_write(lambda tx, b=batch: tx.run(LOAD, rows=b).single()["linked"])
                        batch = []
                if batch:
                    staged += len(batch)
                    linked += session.execute_write(lambda tx, b=batch: tx.run(LOAD, rows=b).single()["linked"])
        g = session.run("MATCH (b:Building)-[r:HAS_LITIGATION]->(c:Litigation) RETURN count(r) AS links, count(DISTINCT c) AS cases").single()
    print(f"staged: cases {staged:,}, excluded (no registered building) {excluded:,}")
    print(f"graph:  cases {g['cases']:,}, HAS_LITIGATION {g['links']:,}")
    ok = linked == staged and (staged, staged) == (g["cases"], g["links"])
    print("reconciled" if ok else "MISMATCH between staged and graph counts", file=sys.stdout if ok else sys.stderr)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
