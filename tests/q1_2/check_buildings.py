"""Check Building nodes and HAS_BUILDING relationships against the frozen source. Read-only on both databases.

1. Each fixture is re-derived from the source with SQL, so a stale fixture fails.
2. Each fixture lot is looked up in the graph with tests/q1_2/lookup.cypher.
3. Graph totals must equal the totals computed from the source, and every graph Building must be linked.

Any failure or error is a failure; nothing is skipped. Exit code 0 only if every check passes.
Run: uv run python tests/q1_2/check_buildings.py
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
VALID = "bin ~ '^[1-5][0-9]{6}$' AND bin !~ '000000$'"

SOURCE_BUILDINGS = f"""
SELECT btrim(b.bin),
       (SELECT CASE WHEN count(DISTINCT a) = 1 THEN min(a) END
        FROM (SELECT nullif(btrim(concat_ws(' ', r2.housenumber, r2.streetname)), '') AS a,
                     rank() OVER (ORDER BY r2.lastregistrationdate DESC NULLS LAST, r2.registrationid DESC) AS rk
              FROM hpd_registrations r2 WHERE r2.bin = b.bin AND r2.bbl IS NOT NULL) x
        WHERE rk = 1)
FROM (SELECT DISTINCT bin FROM hpd_registrations WHERE bbl = %(bbl)s AND {VALID}) b
"""
SOURCE_NUMBLDGS = "SELECT numbldgs FROM pluto_latest WHERE bbl = %(bbl)s"
SOURCE_TOTALS = f"""
SELECT (SELECT count(DISTINCT bin) FROM hpd_registrations WHERE bbl IS NOT NULL AND {VALID}),
       (SELECT count(*) FROM (SELECT DISTINCT bbl, bin FROM hpd_registrations WHERE bbl IS NOT NULL AND {VALID}) x),
       (SELECT count(*) FROM hpd_registrations WHERE bbl IS NOT NULL AND NOT ({VALID}))
"""
GRAPH_TOTALS = """
CALL () { MATCH (b:Building) RETURN count(b) AS buildings }
CALL () { MATCH (:Lot)-[r:HAS_BUILDING]->(:Building) RETURN count(r) AS pairs }
CALL () { MATCH (b:Building) WHERE NOT (:Lot)-[:HAS_BUILDING]->(b) RETURN count(b) AS orphans }
RETURN buildings, pairs, orphans
"""

results = []


def check(name: str, ok: bool, detail: str = "") -> None:
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  ({detail})" if detail and not ok else ""))


def matches(expected: dict, got: dict, mode: str) -> bool:
    return expected.items() <= got.items() if mode == "includes" else expected == got


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
                for f in fixtures["lots"]:
                    bbl, mode = f["bbl"], f["mode"]
                    expected = {str(k): v for k, v in f["buildings"].items()}
                    cur.execute(SOURCE_BUILDINGS, {"bbl": bbl})
                    derived = {b: a for b, a in cur.fetchall()}
                    cur.execute(SOURCE_NUMBLDGS, {"bbl": bbl})
                    row = cur.fetchone()
                    derived_num = row[0] if row else None
                    check(f"{bbl} fixture matches source", matches(expected, derived, mode) and derived_num == f["plutoNumBuildings"],
                          f"source says plutoNumBuildings {derived_num}, buildings {derived}")
                    rec = session.run(lookup, bbl=bbl).single()
                    got = {b["bin"]: b["address"] for b in rec["buildings"]} if rec else None
                    ok = rec is not None and matches(expected, got, mode) and rec["plutoNumBuildings"] == f["plutoNumBuildings"]
                    check(f"{bbl} graph matches fixture", ok, f"graph has plutoNumBuildings {rec and rec['plutoNumBuildings']}, buildings {got}")
                cur.execute(SOURCE_TOTALS)
                buildings, pairs, excluded = cur.fetchone()
            t = fixtures["totals"]
            check("source totals match fixture", (buildings, pairs, excluded) == (t["buildings"], t["pairs"], t["excluded_rows"]),
                  f"source gives {(buildings, pairs, excluded)}")
            g = session.run(GRAPH_TOTALS).single()
            check("graph Building count matches source", g["buildings"] == buildings, f"graph {g['buildings']} vs source {buildings}")
            check("graph HAS_BUILDING count matches source", g["pairs"] == pairs, f"graph {g['pairs']} vs source {pairs}")
            check("every Building is linked to a Lot", g["orphans"] == 0, f"{g['orphans']} unlinked")

    failed = results.count(False)
    print(f"{len(results) - failed}/{len(results)} checks passed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
