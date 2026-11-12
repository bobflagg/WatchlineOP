"""Check the Lot nodes against the frozen source. Read-only on both databases.

1. Each fixture is re-derived from the source with SQL, so a stale fixture fails.
2. Each fixture lot is looked up in the graph with tests/q1_1/lookup.cypher.
3. Lots outside the rental scope must be absent from the graph.
4. Graph totals must equal the totals computed from the source.

Any failure or error is a failure; nothing is skipped. Exit code 0 only if every check passes.
Run: uv run python tests/q1_1/check_lots.py
"""

import os
import sys
from pathlib import Path

import psycopg
import yaml
from dotenv import load_dotenv
from neo4j import GraphDatabase

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
REQUIRED_ENV = ("JUSTFIX_DATABASE_URL", "NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD", "NEO4J_DATABASE")

SOURCE_LOT = """
SELECT p.address,
       EXISTS (SELECT 1 FROM hpd_registrations r WHERE r.bbl = p.bbl) AS hpd_registered
FROM pluto_latest p WHERE p.bbl = %(bbl)s
"""
SOURCE_REGISTRATION_ADDRESS = """
SELECT (SELECT count(*) FROM hpd_registrations WHERE bbl = %(bbl)s) AS registrations,
       (SELECT CASE WHEN count(DISTINCT a) = 1 THEN min(a) END
        FROM (SELECT nullif(btrim(concat_ws(' ', housenumber, streetname)), '') AS a,
                     rank() OVER (ORDER BY lastregistrationdate DESC NULLS LAST, registrationid DESC) AS rk
              FROM hpd_registrations WHERE bbl = %(bbl)s) x
        WHERE rk = 1) AS address
"""
SOURCE_IN_SCOPE = """
SELECT EXISTS (SELECT 1 FROM hpd_registrations WHERE bbl = %(bbl)s)
    OR EXISTS (SELECT 1 FROM pluto_latest WHERE bbl = %(bbl)s AND unitsres >= 3)
"""
SOURCE_TOTALS = """
SELECT (SELECT count(DISTINCT bbl) FROM hpd_registrations WHERE bbl IS NOT NULL),
       (SELECT count(*) FROM (SELECT bbl FROM pluto_latest WHERE unitsres >= 3
                              EXCEPT SELECT bbl FROM hpd_registrations) x),
       (SELECT count(*) FROM (SELECT bbl FROM pluto_latest WHERE unitsres >= 3
                              UNION SELECT bbl FROM hpd_registrations WHERE bbl IS NOT NULL) y)
"""
GRAPH_TOTALS = """
MATCH (l:Lot) RETURN count(l) AS total, count(CASE WHEN l.hpdRegistered THEN 1 END) AS registered
"""

results = []


def check(name: str, ok: bool, detail: str = "") -> None:
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  ({detail})" if detail and not ok else ""))


def source_lot(cur, bbl):
    cur.execute(SOURCE_LOT, {"bbl": bbl})
    row = cur.fetchone()
    if row:
        return {"address": row[0], "hpdRegistered": bool(row[1])}
    cur.execute(SOURCE_REGISTRATION_ADDRESS, {"bbl": bbl})
    registrations, address = cur.fetchone()
    return {"address": address, "hpdRegistered": True} if registrations else None


def main() -> int:
    load_dotenv(ROOT / ".env")
    missing = [k for k in REQUIRED_ENV if not os.environ.get(k)]
    if missing:
        print(f"missing in .env: {', '.join(missing)}", file=sys.stderr)
        return 1
    fixtures = yaml.safe_load((HERE / "fixtures.yaml").read_text())
    lookup = (HERE / "lookup.cypher").read_text()

    driver = GraphDatabase.driver(
        os.environ["NEO4J_URI"], auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"])
    )
    with driver, driver.session(database=os.environ["NEO4J_DATABASE"], default_access_mode="READ") as session:
        with psycopg.connect(os.environ["JUSTFIX_DATABASE_URL"]) as pg:
            pg.read_only = True
            with pg.cursor() as cur:
                for f in fixtures["in_graph"]:
                    bbl = f["bbl"]
                    expected = {"address": f["address"], "hpdRegistered": f["hpdRegistered"]}
                    derived = source_lot(cur, bbl)
                    check(f"{bbl} fixture matches source", derived == expected, f"source says {derived}")
                    rec = session.run(lookup, bbl=bbl).single()
                    got = {"address": rec["address"], "hpdRegistered": rec["hpdRegistered"]} if rec else None
                    check(f"{bbl} graph matches fixture", got == expected, f"graph has {got}")

                for f in fixtures["not_in_graph"]:
                    bbl = f["bbl"]
                    cur.execute(SOURCE_IN_SCOPE, {"bbl": bbl})
                    check(f"{bbl} is outside the rental scope in the source", cur.fetchone()[0] is False)
                    check(f"{bbl} is absent from the graph", session.run(lookup, bbl=bbl).single() is None)

                cur.execute(SOURCE_TOTALS)
                reg, unreg, total = cur.fetchone()
            t = fixtures["totals"]
            check("source totals match fixture", (reg, unreg, total) == (
                t["registered_bbl"], t["unregistered_3plus"], t["total_lots"]), f"source gives {(reg, unreg, total)}")
            g = session.run(GRAPH_TOTALS).single()
            check("graph total matches source", g["total"] == total, f"graph {g['total']} vs source {total}")
            check("graph registered matches source", g["registered"] == reg, f"graph {g['registered']} vs source {reg}")

    failed = results.count(False)
    print(f"{len(results) - failed}/{len(results)} checks passed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
