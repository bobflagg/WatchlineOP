"""Load Building nodes and Lot-[:HAS_BUILDING]->Building relationships (Q1.2).

Run after scripts/load_lots.py. Rules (see tests/q1_2/expected.sql):
  - Building per distinct valid BIN in hpd_registrations. A valid BIN matches ^[1-5][0-9]{6}$ and does not
    end in 000000. Registration rows with any other BIN (0, blank, borough-level placeholders such as
    3000000, short values) are excluded and counted, never turned into buildings.
  - address: house number and street name from the BIN's most recent registrations (lastregistrationdate, then
    registrationid, descending), as HPD spells them. registrationid repeats, so those registrations can tie;
    if they name more than one address the address is left absent, never picked.
  - HAS_BUILDING: one relationship per distinct (BBL, BIN) pair. A BIN can sit on several lots and a lot can
    have many BINs, so the relationship is many-to-many.
  - Both endpoints must already exist. A missing Lot is an error; endpoints are never created here.

Safe to rerun (MERGE). Reads the source read-only and writes only to the POC database.
Run: uv run python scripts/load_buildings.py
"""

import os
import re
import sys
import time
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from neo4j import GraphDatabase

POC_DATABASE = "watchline"
BATCH = 5000
BIN_PATTERN = re.compile(r"^[1-5][0-9]{6}$")
BBL_PATTERN = re.compile(r"^[1-5][0-9]{9}$")
REQUIRED_ENV = ("JUSTFIX_DATABASE_URL", "NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD", "NEO4J_DATABASE")

VALID_BIN = "bin ~ '^[1-5][0-9]{6}$' AND bin !~ '000000$'"

BUILDINGS_SQL = f"""
SELECT bin::text AS bin, CASE WHEN count(DISTINCT a) = 1 THEN min(a) END AS address
FROM (
    SELECT bin, nullif(btrim(concat_ws(' ', housenumber, streetname)), '') AS a,
           rank() OVER (PARTITION BY bin
                        ORDER BY lastregistrationdate DESC NULLS LAST, registrationid DESC) AS rk
    FROM hpd_registrations
    WHERE bbl IS NOT NULL AND {VALID_BIN}
) ranked
WHERE rk = 1
GROUP BY bin
ORDER BY bin
"""
PAIRS_SQL = f"""
SELECT DISTINCT bbl::text AS bbl, bin::text AS bin
FROM hpd_registrations
WHERE bbl IS NOT NULL AND {VALID_BIN}
ORDER BY bbl, bin
"""
EXCLUDED_SQL = f"SELECT count(*) FROM hpd_registrations WHERE bbl IS NOT NULL AND NOT ({VALID_BIN})"

CONSTRAINT = "CREATE CONSTRAINT building_bin_unique IF NOT EXISTS FOR (b:Building) REQUIRE b.bin IS UNIQUE"
LOAD_BUILDINGS = """
UNWIND $rows AS row
MERGE (b:Building {bin: row.bin})
SET b.address = row.address
"""
LOAD_PAIRS = """
UNWIND $rows AS row
MATCH (l:Lot {bbl: row.bbl})
MATCH (b:Building {bin: row.bin})
MERGE (l)-[:HAS_BUILDING]->(b)
RETURN count(*) AS linked
"""
COUNTS = """
CALL () { MATCH (b:Building) RETURN count(b) AS buildings, count(CASE WHEN b.address IS NULL THEN 1 END) AS no_address }
CALL () { MATCH (:Lot)-[r:HAS_BUILDING]->(:Building) RETURN count(r) AS pairs }
RETURN buildings, no_address, pairs
"""


def stream(pg, name, sql, validate):
    with pg.cursor(name=name) as cur:
        cur.itersize = BATCH
        cur.execute(sql)
        while True:
            rows = cur.fetchmany(BATCH)
            if not rows:
                return
            for row in rows:
                validate(row)
            yield rows


def main() -> int:
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    missing = [k for k in REQUIRED_ENV if not os.environ.get(k)]
    if missing:
        print(f"missing in .env: {', '.join(missing)}", file=sys.stderr)
        return 1
    if os.environ["NEO4J_DATABASE"] != POC_DATABASE:
        print(f"refusing: NEO4J_DATABASE is not the POC database '{POC_DATABASE}'", file=sys.stderr)
        return 1

    def check_building(row):
        if not BIN_PATTERN.match(row[0]):
            raise ValueError(f"invalid BIN from source: {row[0]!r}")

    def check_pair(row):
        if not BBL_PATTERN.match(row[0]) or not BIN_PATTERN.match(row[1]):
            raise ValueError(f"invalid pair from source: {row!r}")

    staged_buildings = staged_no_address = staged_pairs = linked = 0
    started = time.time()

    driver = GraphDatabase.driver(
        os.environ["NEO4J_URI"], auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"])
    )
    try:
        driver.verify_connectivity()
    except Exception as exc:  # start the DBMS in Neo4j Desktop first
        print(f"cannot reach Neo4j ({type(exc).__name__}). Is the DBMS started in Neo4j Desktop?", file=sys.stderr)
        return 1

    with driver, driver.session(database=POC_DATABASE) as session:
        session.run(CONSTRAINT).consume()
        with psycopg.connect(os.environ["JUSTFIX_DATABASE_URL"]) as pg:
            pg.read_only = True
            for rows in stream(pg, "buildings", BUILDINGS_SQL, check_building):
                batch = [{"bin": b, "address": a} for b, a in rows]
                session.execute_write(lambda tx, b=batch: tx.run(LOAD_BUILDINGS, rows=b).consume())
                staged_buildings += len(batch)
                staged_no_address += sum(1 for _, a in rows if a is None)
            print(f"  buildings loaded: {staged_buildings:,} ({time.time() - started:.0f}s)", flush=True)
            for rows in stream(pg, "pairs", PAIRS_SQL, check_pair):
                batch = [{"bbl": l, "bin": b} for l, b in rows]
                n = session.execute_write(lambda tx, b=batch: tx.run(LOAD_PAIRS, rows=b).single()["linked"])
                staged_pairs += len(batch)
                linked += n
            with pg.cursor() as cur:
                cur.execute(EXCLUDED_SQL)
                excluded = cur.fetchone()[0]
        graph = session.run(COUNTS).single()

    print(f"excluded registration rows (invalid or placeholder BIN): {excluded:,}")
    print(f"staged:  buildings {staged_buildings:,} (no address {staged_no_address:,}), lot-building pairs {staged_pairs:,}")
    print(f"graph:   buildings {graph['buildings']:,} (no address {graph['no_address']:,}), HAS_BUILDING {graph['pairs']:,}")
    ok = (
        linked == staged_pairs  # every pair found both endpoints
        and (staged_buildings, staged_no_address, staged_pairs)
        == (graph["buildings"], graph["no_address"], graph["pairs"])
    )
    if linked != staged_pairs:
        print(f"{staged_pairs - linked:,} pairs had a missing Lot or Building endpoint", file=sys.stderr)
    print("reconciled" if ok else "MISMATCH between staged and graph counts", file=sys.stdout if ok else sys.stderr)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
