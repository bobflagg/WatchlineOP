"""Check the business address of non-owner Contact nodes against the frozen source. Read-only on both databases.

1. Each fixture is re-derived from the source with SQL, so a stale fixture fails.
2. Each fixture is looked up in the graph with tests/q4_2/lookup.cypher (street line and ZIP compared).
3. Graph totals must equal the totals computed from the source.
Run: uv run python tests/q4_2/check_addresses.py
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
NOT_OWNER = "c.type NOT IN ('CorporateOwner','IndividualOwner','JointOwner')"
STREET = "nullif(btrim(concat_ws(' ', nullif(btrim(c.businesshousenumber), ''), nullif(btrim(c.businessstreetname), ''))), '')"
ZIP = "nullif(btrim(c.businesszip), '')"
PERSON = "nullif(btrim(concat_ws(' ', nullif(btrim(c.firstname), ''), nullif(btrim(c.middleinitial), ''), nullif(btrim(c.lastname), ''))), '')"
# one row per contact; a part is present only if every duplicate has the same value
SOURCE_ADDR = f"""
SELECT c.type, CASE WHEN count(DISTINCT {STREET}) = 1 AND count({STREET}) = count(*) THEN min({STREET}) END,
       CASE WHEN count(DISTINCT {ZIP}) = 1 AND count({ZIP}) = count(*) THEN min({ZIP}) END
FROM hpd_contacts c WHERE c.registrationid = %(rid)s AND {NOT_OWNER}
GROUP BY c.type, nullif(btrim(c.corporationname), ''), {PERSON}, nullif(btrim(c.title), '')
"""
SOURCE_TOTALS = f"""
SELECT count(*), count(*) FILTER (WHERE nn = n AND na = 1), count(*) FILTER (WHERE na > 1 OR (nn > 0 AND nn < n))
FROM (SELECT count(DISTINCT {STREET}) na, count({STREET}) nn, count(*) n FROM hpd_contacts c
      WHERE {NOT_OWNER} AND c.registrationid IN (SELECT registrationid FROM hpd_registrations WHERE bbl IS NOT NULL AND {VALID})
      GROUP BY c.registrationid, c.type, nullif(btrim(c.corporationname), ''), {PERSON}, nullif(btrim(c.title), '')) k
"""
GRAPH_TOTALS = "MATCH (c:Contact) WHERE NOT c.contactType IN ['CorporateOwner','IndividualOwner','JointOwner'] RETURN count(c) AS contacts, count(c.mailingAddress) AS with_addr"
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
                for f in fx["registrations"]:
                    rid, b = f["registrationId"], f["bin"]
                    cur.execute(SOURCE_ADDR, {"rid": rid})
                    derived = sorted(cur.fetchall(), key=str)
                    rows = {r["registrationId"]: r["contacts"] for r in session.run(lookup, bin=b)}
                    got = sorted(((c["contactType"], c["mailingAddress"], c["zip"]) for c in rows.get(rid, [])), key=str)
                    if "contacts" in f:
                        exp = sorted((tuple(c) for c in f["contacts"]), key=str)
                        check(f"{rid} fixture matches source", derived == exp, f"source gives {derived}")
                        check(f"{rid} graph matches fixture", got == exp, f"graph has {got}")
                    else:
                        src_missing = any(s is None for _, s, _ in derived)
                        check(f"{rid} a street line is absent in the source", src_missing, f"source gives {derived}")
                        check(f"{rid} graph agrees with source", got == derived, f"graph has {got}")
                cur.execute(SOURCE_TOTALS)
                src = cur.fetchone()
            t = fx["totals"]
            check("source totals match fixture", src == (t["contacts"], t["with_addr"], t["conflicting"]), f"source gives {src}")
            g = session.run(GRAPH_TOTALS).single()
            check("graph address totals match source", (g["contacts"], g["with_addr"]) == src[:2], f"graph {(g['contacts'], g['with_addr'])} vs source {src[:2]}")
    failed = results.count(False)
    print(f"{len(results) - failed}/{len(results)} checks passed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
