"""Check RoleContact nodes and HAS_ROLE_CONTACT against the frozen source. Read-only on both databases.

1. Each fixture is re-derived from the source with SQL, so a stale fixture fails.
2. Each fixture is looked up in the graph with tests/q4_1/lookup.cypher.
3. Graph totals must equal the totals computed from the source, and every RoleContact must be linked.
Person names are never printed or stored: only whether a name is recorded is compared.
Run: uv run python tests/q4_1/check_roles.py
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
PERSON = "nullif(btrim(concat_ws(' ', nullif(btrim(c.firstname), ''), nullif(btrim(c.middleinitial), ''), nullif(btrim(c.lastname), ''))), '')"
SOURCE_ROLES = f"""SELECT DISTINCT c.type, nullif(btrim(c.title), ''), nullif(btrim(c.corporationname), '') IS NOT NULL, {PERSON} IS NOT NULL
FROM hpd_contacts c WHERE c.registrationid = %(rid)s AND {NOT_OWNER}"""
SOURCE_ON_BIN = f"SELECT count(*) FROM hpd_registrations WHERE registrationid = %(rid)s AND bin = %(bin)s AND {VALID}"
SOURCE_TOTALS = f"""
SELECT count(*), count(*) FILTER (WHERE corp IS NULL AND person IS NULL), count(*) FILTER (WHERE title IS NOT NULL), count(DISTINCT registrationid)
FROM (SELECT c.registrationid, c.type, nullif(btrim(c.corporationname), '') corp, {PERSON} person, nullif(btrim(c.title), '') title
      FROM hpd_contacts c WHERE {NOT_OWNER}
        AND c.registrationid IN (SELECT registrationid FROM hpd_registrations WHERE bbl IS NOT NULL AND {VALID})
      GROUP BY 1, 2, 3, 4, 5) k
"""
GRAPH_TOTALS = """
CALL () { MATCH (c:RoleContact) RETURN count(c) AS contacts, count(CASE WHEN c.corporationName IS NULL AND c.personName IS NULL THEN 1 END) AS unnamed, count(c.title) AS titled }
CALL () { MATCH (:Registration)-[:HAS_ROLE_CONTACT]->(c:RoleContact) RETURN count(DISTINCT c) AS linked }
CALL () { MATCH (r:Registration)-[:HAS_ROLE_CONTACT]->(:RoleContact) RETURN count(DISTINCT r) AS regs }
CALL () { MATCH (c:RoleContact) WHERE c.contactType IN ['CorporateOwner','IndividualOwner','JointOwner'] RETURN count(c) AS badtype }
RETURN contacts, unnamed, titled, linked, regs, badtype
"""
results = []


def check(name, ok, detail=""):
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  ({detail})" if detail and not ok else ""))


def shape(c):
    return (c["contactType"], c["title"], c["corporationName"] is not None, c["personName"] is not None)


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
                    exact = "contacts" in f
                    exp = sorted((tuple(c) for c in (f["contacts"] if exact else f["contacts_include"])), key=str)
                    cur.execute(SOURCE_ON_BIN, {"rid": rid, "bin": b})
                    on_bin = cur.fetchone()[0] > 0
                    cur.execute(SOURCE_ROLES, {"rid": rid})
                    derived = sorted(cur.fetchall(), key=str)

                    def fits(e, g):  # None in a fixture means "not asserted"
                        return all(x is None or x == y for x, y in zip(e, g))

                    def matches(got):
                        return all(any(fits(e, g) for g in got) for e in exp) and (not exact or len(got) == len(exp))

                    check(f"{rid} fixture matches source", on_bin and matches(derived), f"on building {on_bin}, source gives {derived}")
                    rows = {r["registrationId"]: r["contacts"] for r in session.run(lookup, bin=b)}
                    got = sorted((shape(c) for c in rows[rid]), key=str) if rid in rows else None
                    check(f"{rid} graph matches fixture", got is not None and matches(got), f"graph has {got}")
                cur.execute(SOURCE_TOTALS)
                src = cur.fetchone()
            t = fx["totals"]
            check("source totals match fixture", src == (t["contacts"], t["unnamed"], t["titled"], t["regs"]), f"source gives {src}")
            g = session.run(GRAPH_TOTALS).single()
            check("graph totals match source", (g["contacts"], g["unnamed"], g["titled"], g["regs"]) == src, f"graph {tuple(g[k] for k in ('contacts','unnamed','titled','regs'))} vs source {src}")
            check("every RoleContact is linked to a Registration", g["linked"] == g["contacts"], f"{g['contacts'] - g['linked']} unlinked")
            check("no owner contact type is a RoleContact", g["badtype"] == 0, f"{g['badtype']} owner types")
    failed = results.count(False)
    print(f"{len(results) - failed}/{len(results)} checks passed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
