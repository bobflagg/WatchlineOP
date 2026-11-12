"""Check Lot characteristics (Q1.4) against the frozen source. Read-only on both databases.

1. Each fixture is re-derived from the source with tests/q1_4/expected.sql, so a stale fixture fails.
2. Each fixture lot is looked up in the graph with tests/q1_4/lookup.cypher.
3. Counts of lots with each characteristic must match between the source, the fixtures and the graph.

Any failure or error is a failure; nothing is skipped. Exit code 0 only if every check passes.
Run: uv run python tests/q1_4/check_characteristics.py
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
FIELDS = ("yearBuilt", "buildingClass", "unitsRes", "assessedTotal")

SOURCE_TOTALS = """
WITH scope AS (SELECT bbl FROM hpd_registrations WHERE bbl IS NOT NULL
               UNION SELECT bbl FROM pluto_latest WHERE unitsres >= 3)
SELECT count(*), count(nullif(p.yearbuilt, 0)), count(nullif(btrim(p.bldgclass), '')), count(p.unitsres), count(p.assesstot)
FROM scope s LEFT JOIN pluto_latest p ON p.bbl = s.bbl
"""
GRAPH_TOTALS = """
MATCH (l:Lot) RETURN count(l) AS total, count(l.yearBuilt) AS yearBuilt, count(l.buildingClass) AS buildingClass,
       count(l.unitsRes) AS unitsRes, count(l.assessedTotal) AS assessedTotal
"""

results = []


def check(name: str, ok: bool, detail: str = "") -> None:
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  ({detail})" if detail and not ok else ""))


def main() -> int:
    load_dotenv(ROOT / ".env")
    missing = [k for k in REQUIRED_ENV if not os.environ.get(k)]
    if missing:
        print(f"missing in .env: {', '.join(missing)}", file=sys.stderr)
        return 1
    fixtures = yaml.safe_load((HERE / "fixtures.yaml").read_text())
    expected_sql = (HERE / "expected.sql").read_text()
    lookup = (HERE / "lookup.cypher").read_text()

    driver = GraphDatabase.driver(os.environ["NEO4J_URI"], auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]))
    with driver, driver.session(database=os.environ["NEO4J_DATABASE"], default_access_mode="READ") as session:
        with psycopg.connect(os.environ["JUSTFIX_DATABASE_URL"]) as pg:
            pg.read_only = True
            with pg.cursor() as cur:
                for f in fixtures["lots"]:
                    bbl = f["bbl"]
                    expected = {k: f[k] for k in FIELDS}
                    cur.execute(expected_sql, {"bbl": bbl})
                    row = cur.fetchone()
                    derived = dict(zip(FIELDS, row)) if row else {k: None for k in FIELDS}
                    check(f"{bbl} fixture matches source", derived == expected, f"source says {derived}")
                    rec = session.run(lookup, bbl=bbl).single()
                    got = {k: rec[k] for k in FIELDS} if rec else None
                    check(f"{bbl} graph matches fixture", got == expected, f"graph has {got}")
                cur.execute(SOURCE_TOTALS)
                src = cur.fetchone()
        g = session.run(GRAPH_TOTALS).single()
        t = fixtures["totals"]
        for i, k in enumerate(FIELDS, start=1):
            check(f"{k}: source count matches fixture", src[i] == t[k], f"source {src[i]} vs fixture {t[k]}")
            check(f"{k}: graph count matches source", g[k] == src[i], f"graph {g[k]} vs source {src[i]}")
        check("graph lot total matches source", g["total"] == src[0], f"graph {g['total']} vs source {src[0]}")

    failed = results.count(False)
    print(f"{len(results) - failed}/{len(results)} checks passed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
