"""Check Registration nodes and HAS_REGISTRATION against the frozen source. Read-only on both databases.

1. Each fixture is re-derived from the source with SQL, so a stale fixture fails.
2. Each fixture building is looked up in the graph with tests/q2_1/lookup.cypher.
3. Graph totals must equal the totals computed from the source.
Any failure or error is a failure. Run: uv run python tests/q2_1/check_registrations.py
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
VALID = "bin ~ '^[1-5][0-9]{6}$' AND bin !~ '000000$' AND registrationid > 0"

SOURCE_PAIRS = f"""
SELECT registrationid,
       CASE WHEN count(DISTINCT lastregistrationdate) = 1 AND count(lastregistrationdate) = count(*)
            THEN to_char(min(lastregistrationdate), 'YYYY-MM-DD') END,
       CASE WHEN count(DISTINCT registrationenddate) = 1 AND count(registrationenddate) = count(*)
            THEN to_char(min(registrationenddate), 'YYYY-MM-DD') END
FROM hpd_registrations WHERE bin = %(bin)s AND {VALID} GROUP BY registrationid
"""
SOURCE_TOTALS = f"""
SELECT (SELECT count(DISTINCT registrationid) FROM hpd_registrations WHERE bbl IS NOT NULL AND {VALID}),
       count(*), count(*) FILTER (WHERE has_last), count(*) FILTER (WHERE has_end),
       (SELECT count(*) FROM (SELECT bin FROM hpd_registrations WHERE bbl IS NOT NULL AND {VALID}
                              GROUP BY bin HAVING count(DISTINCT registrationid) > 1) m)
FROM (SELECT count(DISTINCT lastregistrationdate) = 1 AND count(lastregistrationdate) = count(*) AS has_last,
             count(DISTINCT registrationenddate) = 1 AND count(registrationenddate) = count(*) AS has_end
      FROM hpd_registrations WHERE bbl IS NOT NULL AND {VALID} GROUP BY registrationid, bin) p
"""
GRAPH_TOTALS = """
CALL () { MATCH (r:Registration) RETURN count(r) AS regs }
CALL () { MATCH (:Building)-[h:HAS_REGISTRATION]->(:Registration) RETURN count(h) AS pairs, count(h.lastRegistered) AS lasts, count(h.registrationEnd) AS ends }
CALL () { MATCH (b:Building)-[:HAS_REGISTRATION]->(:Registration) WITH b, count(*) AS c WHERE c > 1 RETURN count(b) AS multi }
CALL () { MATCH (r:Registration) WHERE NOT (:Building)-[:HAS_REGISTRATION]->(r) RETURN count(r) AS orphans }
RETURN regs, pairs, lasts, ends, multi, orphans
"""
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
    lookup = (HERE / "lookup.cypher").read_text()
    driver = GraphDatabase.driver(os.environ["NEO4J_URI"], auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]))
    with driver, driver.session(database=os.environ["NEO4J_DATABASE"], default_access_mode="READ") as session:
        with psycopg.connect(os.environ["JUSTFIX_DATABASE_URL"]) as pg:
            pg.read_only = True
            with pg.cursor() as cur:
                for f in fx["buildings"]:
                    b = f["bin"]
                    cur.execute(SOURCE_PAIRS, {"bin": b})
                    derived = {int(r): [l, e] for r, l, e in cur.fetchall()}
                    rec = session.run(lookup, bin=b).single()
                    got = {r["registrationId"]: [r["lastRegistered"], r["registrationEnd"]] for r in rec["registrations"]} if rec else None
                    if f["mode"] == "exact":
                        exp = {int(k): v for k, v in f["registrations"].items()}
                        check(f"{b} fixture matches source", exp == derived, f"source gives {derived}")
                        check(f"{b} graph matches fixture", got == exp, f"graph has {got}")
                    else:
                        check(f"{b} fixture matches source", len(derived) == f["count"], f"source gives {len(derived)}")
                        check(f"{b} graph matches fixture", got is not None and len(got) == f["count"] and got == derived,
                              f"graph has {None if got is None else len(got)}")
                for b in fx["absent_bins"]:
                    check(f"{b} is absent from the graph", session.run(lookup, bin=b).single() is None)
                cur.execute(SOURCE_TOTALS)
                src = cur.fetchone()
            t = fx["totals"]
            exp = (t["registrations"], t["pairs"], t["with_last"], t["with_end"], t["bins_multi"])
            check("source totals match fixture", src == exp, f"source gives {src}")
            g = session.run(GRAPH_TOTALS).single()
            check("graph totals match source", (g["regs"], g["pairs"], g["lasts"], g["ends"], g["multi"]) == src,
                  f"graph {(g['regs'], g['pairs'], g['lasts'], g['ends'], g['multi'])} vs source {src}")
            check("every Registration is linked to a Building", g["orphans"] == 0, f"{g['orphans']} unlinked")
    failed = results.count(False)
    print(f"{len(results) - failed}/{len(results)} checks passed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
