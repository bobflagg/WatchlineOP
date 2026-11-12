"""Load Lot nodes (Q1.1) from the frozen JustFix/WoW snapshot into the POC Neo4j graph.

Lot rules (see tests/q1_1/expected.sql):
  - one Lot per BBL in hpd_registrations, plus every unregistered pluto_latest lot with unitsres >= 3
  - bbl: 10-digit string, unique
  - address: PLUTO address; for a registered BBL missing from PLUTO, the address of its most recent
    registrations (lastregistrationdate, then registrationid, descending). If those registrations name more
    than one address (registrationid repeats, so ties happen), the address is left absent, never picked.
  - hpdRegistered: true if the BBL has a row in hpd_registrations
  - plutoNumBuildings: PLUTO numbldgs as recorded (0 is kept; absent when PLUTO has none or the lot is not in PLUTO).
    It is PLUTO's count, not the number of buildings in the graph.
  - Q1.4 characteristics, all from PLUTO 26v1 and absent when PLUTO has no value or the lot is not in PLUTO:
    yearBuilt (PLUTO 0 means unknown, so it is stored as absent), buildingClass (blank is absent),
    unitsRes and assessedTotal (0 is kept: PLUTO records none; it is not "no housing" or "no tenants").
    unitsRes is lot-wide.

Safe to rerun: MERGE on bbl, so a replay creates no duplicates. Reads the source read-only, writes only
to the POC database. Credentials come from .env and are never printed.

Run: uv run python scripts/load_lots.py
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
BBL_PATTERN = re.compile(r"^[1-5][0-9]{9}$")
REQUIRED_ENV = ("JUSTFIX_DATABASE_URL", "NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD", "NEO4J_DATABASE")

SOURCE_SQL = """
WITH reg AS (
    SELECT bbl, CASE WHEN count(DISTINCT a) = 1 THEN min(a) END AS reg_address
    FROM (
        SELECT bbl, nullif(btrim(concat_ws(' ', housenumber, streetname)), '') AS a,
               rank() OVER (PARTITION BY bbl
                            ORDER BY lastregistrationdate DESC NULLS LAST, registrationid DESC) AS rk
        FROM hpd_registrations
        WHERE bbl IS NOT NULL
    ) ranked
    WHERE rk = 1
    GROUP BY bbl
),
lots AS (
    SELECT p.bbl::text AS bbl, p.address AS address, (r.bbl IS NOT NULL) AS hpd_registered, p.numbldgs AS num_buildings,
           nullif(p.yearbuilt, 0) AS year_built, nullif(btrim(p.bldgclass), '') AS building_class,
           p.unitsres AS units_res, p.assesstot AS assessed_total
    FROM pluto_latest p
    LEFT JOIN reg r ON r.bbl = p.bbl
    WHERE r.bbl IS NOT NULL OR p.unitsres >= 3
    UNION ALL
    SELECT r.bbl::text, r.reg_address, TRUE, NULL::integer,
           NULL::smallint, NULL::text, NULL::integer, NULL::bigint
    FROM reg r
    WHERE NOT EXISTS (SELECT 1 FROM pluto_latest p WHERE p.bbl = r.bbl)
)
SELECT bbl, nullif(btrim(address), '') AS address, hpd_registered, num_buildings,
       year_built, building_class, units_res, assessed_total
FROM lots
ORDER BY bbl
"""

CONSTRAINT = "CREATE CONSTRAINT lot_bbl_unique IF NOT EXISTS FOR (l:Lot) REQUIRE l.bbl IS UNIQUE"

# Setting a null property removes it, so a lot with no known address has no address property.
LOAD = """
UNWIND $rows AS row
MERGE (l:Lot {bbl: row.bbl})
SET l.address = row.address, l.hpdRegistered = row.hpdRegistered, l.plutoNumBuildings = row.plutoNumBuildings,
    l.yearBuilt = row.yearBuilt, l.buildingClass = row.buildingClass,
    l.unitsRes = row.unitsRes, l.assessedTotal = row.assessedTotal
"""

COUNTS = """
MATCH (l:Lot)
RETURN count(l) AS total,
       count(CASE WHEN l.hpdRegistered THEN 1 END) AS registered,
       count(CASE WHEN l.address IS NULL THEN 1 END) AS no_address,
       count(CASE WHEN l.plutoNumBuildings IS NULL THEN 1 END) AS no_num_buildings,
       count(l.yearBuilt) AS year_built, count(l.buildingClass) AS building_class,
       count(l.unitsRes) AS units_res, count(l.assessedTotal) AS assessed_total
"""


def main() -> int:
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    missing = [k for k in REQUIRED_ENV if not os.environ.get(k)]
    if missing:
        print(f"missing in .env: {', '.join(missing)}", file=sys.stderr)
        return 1
    if os.environ["NEO4J_DATABASE"] != POC_DATABASE:
        print(f"refusing: NEO4J_DATABASE is not the POC database '{POC_DATABASE}'", file=sys.stderr)
        return 1

    staged = staged_registered = staged_no_address = staged_no_num = 0
    staged_chars = [0, 0, 0, 0]  # non-null yearBuilt, buildingClass, unitsRes, assessedTotal
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
            with pg.cursor(name="lots") as cur:
                cur.itersize = BATCH
                cur.execute(SOURCE_SQL)
                while True:
                    rows = cur.fetchmany(BATCH)
                    if not rows:
                        break
                    batch = []
                    for bbl, address, registered, num_buildings, year_built, building_class, units_res, assessed_total in rows:
                        if not BBL_PATTERN.match(bbl):
                            raise ValueError(f"invalid BBL from source: {bbl!r}")
                        batch.append({"bbl": bbl, "address": address, "hpdRegistered": bool(registered), "plutoNumBuildings": num_buildings,
                                      "yearBuilt": year_built, "buildingClass": building_class,
                                      "unitsRes": units_res, "assessedTotal": assessed_total})
                        staged_registered += bool(registered)
                        staged_no_address += address is None
                        staged_no_num += num_buildings is None
                        for i, v in enumerate((year_built, building_class, units_res, assessed_total)):
                            staged_chars[i] += v is not None
                    session.execute_write(lambda tx, b=batch: tx.run(LOAD, rows=b).consume())
                    staged += len(batch)
                    if (staged // BATCH) % 10 == 0:
                        print(f"  loaded {staged:,} lots ({time.time() - started:.0f}s)", flush=True)

        graph = session.run(COUNTS).single()

    print(f"staged:  total {staged:,}, registered {staged_registered:,}, no address {staged_no_address:,}, no plutoNumBuildings {staged_no_num:,}")
    print(f"graph:   total {graph['total']:,}, registered {graph['registered']:,}, no address {graph['no_address']:,}, no plutoNumBuildings {graph['no_num_buildings']:,}")
    graph_chars = [graph["year_built"], graph["building_class"], graph["units_res"], graph["assessed_total"]]
    print(f"with yearBuilt/buildingClass/unitsRes/assessedTotal: staged {staged_chars}, graph {graph_chars}")
    ok = (staged, staged_registered, staged_no_address, staged_no_num, staged_chars) == (
        graph["total"], graph["registered"], graph["no_address"], graph["no_num_buildings"], graph_chars)
    print("reconciled" if ok else "MISMATCH between staged and graph counts", file=sys.stdout if ok else sys.stderr)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
