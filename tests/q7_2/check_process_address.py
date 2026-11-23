"""Check Q7.2 (do two DOS records share a process address, and how many active entities list it) against the frozen source.

1. Each fixture pair is re-derived from the source with tests/q7_2/expected.sql (entity count over the whole table).
2. Each pair is looked up in the graph with tests/q7_2/lookup.cypher: ids, filing dates, shared flag and the stored hub count.
3. Every DosEntity with a process street line carries a hub count that equals the source for a sample of addresses.
Any failure or error is a failure. Run: uv run python tests/q7_2/check_process_address.py
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
sys.path.insert(0, str(ROOT / "src"))
from watchline.compare import n3  # noqa: E402

REQUIRED_ENV = ("JUSTFIX_DATABASE_URL", "NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD", "NEO4J_DATABASE")
SOURCE_RECORD = """
SELECT nullif(btrim(dosprocessaddress1), ''), nullif(btrim(dosprocesszip), ''), initialdosfilingdate::date
FROM dos_active_corporations WHERE dosid = %(id)s
"""
SAMPLE = """
MATCH (e:DosEntity) WHERE e.processAddress IS NOT NULL
RETURN DISTINCT toUpper(e.processAddress) AS street, left(coalesce(e.processZip, ''), 5) AS zip5, e.processAddressEntities AS n
ORDER BY street, zip5
"""
GRAPH_TOTALS = "MATCH (e:DosEntity) RETURN count(e) AS entities, count(e.processAddress) AS addressed, count(e.processAddressEntities) AS counted"
results = []


def check(name, ok, detail=""):
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  ({detail})" if detail and not ok else ""))


def main() -> int:
    load_dotenv(ROOT / ".env")
    missing = [k for k in REQUIRED_ENV if not os.environ.get(k)]
    if missing:
        print(f"missing in .env: {', '.join(missing)}", file=sys.stderr)
        return 1
    fx = yaml.safe_load((HERE / "fixtures.yaml").read_text())
    expected = (HERE / "expected.sql").read_text()
    lookup = (HERE / "lookup.cypher").read_text()
    driver = GraphDatabase.driver(os.environ["NEO4J_URI"], auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]))
    with driver, driver.session(database=os.environ["NEO4J_DATABASE"], default_access_mode="READ") as session:
        g = session.run(GRAPH_TOTALS).single()
        check("every DosEntity with a process street line has a hub count", g["addressed"] == g["counted"], f"{g['addressed']} addressed, {g['counted']} counted")
        with psycopg.connect(os.environ["JUSTFIX_DATABASE_URL"]) as pg:
            pg.read_only = True
            with pg.cursor() as cur:
                for f in fx["pairs"]:
                    label = f"{f['a']} and {f['b']}"
                    cur.execute(expected, {"street": f["street"], "zip5": f["zip5"]})
                    n = cur.fetchone()[0]
                    check(f"{label}: fixture count matches source", n == f["entities"], f"source {n}")
                    id_a, id_b = int(f["dosIdA"]), int(f["dosIdB"])
                    for side, dos_id in (("a", id_a), ("b", id_b)):
                        cur.execute(SOURCE_RECORD, {"id": dos_id})
                        row = cur.fetchone()
                        check(f"{label}: {side} record is at the fixture address",
                              row is not None and (row[0] or "").upper() == f["street"] and (row[1] or "")[:5] == f["zip5"]
                              and row[2].isoformat() == f["filedA" if side == "a" else "filedB"])
                    rec = session.run(lookup, nameKeyA=n3(f["a"]), nameKeyB=n3(f["b"])).single()
                    ra = [r for r in rec["recordsA"] if r["dosId"] == id_a]
                    rb = [r for r in rec["recordsB"] if r["dosId"] == id_b]
                    check(f"{label}: both records are found by name", len(ra) == 1 and len(rb) == 1)
                    if ra and rb:
                        check(f"{label}: filing dates and hub count match fixture",
                              str(ra[0]["filingDate"]) == f["filedA"] and str(rb[0]["filingDate"]) == f["filedB"]
                              and ra[0]["entities"] == f["entities"] == rb[0]["entities"])
                    shared = any([id_a, id_b] in pairs for pairs in rec["sharedPairs"])
                    check(f"{label}: shared process address is {f['shared']}", shared == f["shared"])
                for s in session.run(SAMPLE).data()[::2000]:
                    cur.execute(expected, {"street": s["street"], "zip5": s["zip5"]})
                    n = cur.fetchone()[0]
                    check(f"hub {s['street']} {s['zip5']} equals source", n == s["n"], f"source {n}, graph {s['n']}")
    failed = results.count(False)
    print(f"{len(results) - failed}/{len(results)} checks passed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
