"""Check OwnerContact nodes and HAS_OWNER_CONTACT against the frozen source. Read-only on both databases.

1. Each fixture is re-derived from the source with SQL, so a stale fixture fails.
2. Each fixture is looked up in the graph with tests/q2_2/lookup.cypher.
3. Graph totals must equal the totals computed from the source, and every OwnerContact must be linked.
Person names are never printed or stored in fixtures: a named person is compared as "<person>".
Run: uv run python tests/q2_2/check_owners.py
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
NAME = """CASE WHEN c.type = 'CorporateOwner' THEN nullif(btrim(c.corporationname), '')
            ELSE nullif(btrim(concat_ws(' ', nullif(btrim(c.firstname), ''), nullif(btrim(c.middleinitial), ''),
                                         nullif(btrim(c.lastname), ''))), '') END"""
SOURCE_OWNERS = f"SELECT DISTINCT c.type, {NAME} FROM hpd_contacts c WHERE c.registrationid = %(rid)s AND c.type IN ('CorporateOwner','IndividualOwner','JointOwner')"
SOURCE_ON_BIN = f"SELECT count(*) FROM hpd_registrations WHERE registrationid = %(rid)s AND bin = %(bin)s AND {VALID}"
SOURCE_TOTALS = f"""
SELECT count(*), count(name) FROM (SELECT DISTINCT c.registrationid, c.type, {NAME} AS name FROM hpd_contacts c
 WHERE c.type IN ('CorporateOwner','IndividualOwner','JointOwner')
   AND c.registrationid IN (SELECT registrationid FROM hpd_registrations WHERE bbl IS NOT NULL AND {VALID})) x
"""
GRAPH_TOTALS = """
CALL () { MATCH (c:OwnerContact) RETURN count(c) AS contacts, count(c.name) AS named }
CALL () { MATCH (c:OwnerContact) WHERE NOT (:Registration)-[:HAS_OWNER_CONTACT]->(c) RETURN count(c) AS orphans }
CALL () { MATCH (c:OwnerContact) WHERE NOT c.contactType IN ['CorporateOwner','IndividualOwner','JointOwner'] RETURN count(c) AS badtype }
RETURN contacts, named, orphans, badtype
"""
results = []


def check(name, ok, detail=""):
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  ({detail})" if detail and not ok else ""))


def mask(t, n):
    """Corporate names are shown; personal names become a marker."""
    return (t, n if t == "CorporateOwner" or n is None else "<person>")


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
                    exp = sorted(tuple(o) for o in f["owners"])
                    cur.execute(SOURCE_ON_BIN, {"rid": rid, "bin": b})
                    on_bin = cur.fetchone()[0] > 0
                    cur.execute(SOURCE_OWNERS, {"rid": rid})
                    derived = sorted(mask(t, n) for t, n in cur.fetchall())
                    check(f"{rid} fixture matches source", on_bin and derived == sorted(exp), f"on building {on_bin}, source gives {derived}")
                    rows = {r["registrationId"]: r["owners"] for r in session.run(lookup, bin=b)}
                    got = sorted(mask(o["contactType"], o["name"]) for o in rows.get(rid, [None])) if rid in rows else None
                    check(f"{rid} graph matches fixture", got == sorted(exp), f"graph has {got}")
                cur.execute(SOURCE_TOTALS)
                src = cur.fetchone()
            check("source totals match fixture", src == (fx["totals"]["contacts"], fx["totals"]["named"]), f"source gives {src}")
            g = session.run(GRAPH_TOTALS).single()
            check("graph contact totals match source", (g["contacts"], g["named"]) == src, f"graph {(g['contacts'], g['named'])} vs source {src}")
            check("every OwnerContact is linked to a Registration", g["orphans"] == 0, f"{g['orphans']} unlinked")
            check("only owner contact types are loaded", g["badtype"] == 0, f"{g['badtype']} other types")
    failed = results.count(False)
    print(f"{len(results) - failed}/{len(results)} checks passed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
