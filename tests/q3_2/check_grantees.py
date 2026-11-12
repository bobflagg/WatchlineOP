"""Check Grantee nodes and HAS_GRANTEE against the frozen source. Read-only on both databases.

1. Each fixture deed is re-derived from the source with SQL, so a stale fixture fails.
2. Each fixture deed is looked up in the graph with tests/q3_2/lookup.cypher and compared.
3. Graph totals must equal the totals computed from the source, and every Grantee must be linked to a Deed.
Person names are never printed. Any failure or error is a failure. Run: uv run python tests/q3_2/check_grantees.py
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
TYPES = ["DEED", "DEED, TS", "DEED, LE", "DEED, RC", "DEEDO", "DEEDP", "CORRD", "CONDEED"]

SOURCE_DEED = """
SELECT DISTINCT nullif(btrim(name), ''), nullif(btrim(address1), ''), nullif(btrim(address2), ''), nullif(btrim(zip), '')
FROM real_property_parties WHERE documentid = %(doc)s AND partytype = 2
"""
SOURCE_TOTALS = """
WITH scope AS (SELECT bbl FROM hpd_registrations
               UNION SELECT p.bbl FROM pluto_latest p WHERE p.unitsres >= 3
                     AND NOT EXISTS (SELECT 1 FROM hpd_registrations r WHERE r.bbl = p.bbl)),
pairs AS (SELECT DISTINCT l.documentid FROM real_property_legals l JOIN scope s ON s.bbl = l.bbl),
cur AS (SELECT DISTINCT ON (m.documentid) m.documentid, m.doctype FROM real_property_master m
        WHERE m.documentid IN (SELECT documentid FROM pairs)
        ORDER BY m.documentid, m.modifieddate DESC NULLS LAST, m.goodthroughdate DESC NULLS LAST),
deeds AS (SELECT documentid FROM cur WHERE doctype = ANY(%(types)s)),
g AS (SELECT DISTINCT p.documentid, nullif(btrim(p.name), '') AS n, nullif(btrim(p.address1), '') AS a,
             nullif(btrim(p.address2), '') AS l, nullif(btrim(p.zip), '') AS z
      FROM real_property_parties p JOIN deeds d USING (documentid) WHERE p.partytype = 2)
SELECT count(*), count(n), count(a), count(DISTINCT documentid) FROM g
"""
GRAPH_TOTALS = """
CALL () { MATCH (g:Grantee) RETURN count(g) AS grantees, count(g.name) AS named, count(g.mailingAddress) AS with_addr }
CALL () { MATCH (:Deed)-[:HAS_GRANTEE]->(g:Grantee) RETURN count(DISTINCT g) AS linked }
CALL () { MATCH (d:Deed)-[:HAS_GRANTEE]->(:Grantee) RETURN count(DISTINCT d) AS deeds }
CALL () { MATCH (g:Grantee) WHERE size([(d:Deed)-[:HAS_GRANTEE]->(g) | d]) <> 1 RETURN count(g) AS notone }
RETURN grantees, named, with_addr, linked, deeds, notone
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
                for f in fx["deeds"]:
                    doc = f["documentId"]
                    cur.execute(SOURCE_DEED, {"doc": doc})
                    src = sorted(cur.fetchall(), key=lambda r: tuple(x or "" for x in r))
                    rec = session.run(lookup, documentId=doc).single()
                    got = sorted(((g["name"], g["mailingAddress"], g["addressLine2"], g["zip"]) for g in rec["grantees"]),
                                 key=lambda r: tuple(x or "" for x in r)) if rec else None

                    def ok_for(rows):
                        if rows is None:
                            return False
                        if "grantees" in f:
                            return sorted(tuple(r) for r in rows) == sorted((tuple(g) for g in f["grantees"]), key=lambda r: tuple(x or "" for x in r))
                        if "grantee_count" in f:
                            return len(rows) == f["grantee_count"]
                        if "blank_names" in f:
                            return sum(1 for r in rows if r[0] is None) == f["blank_names"]
                        if "blank_addresses" in f:
                            return sum(1 for r in rows if r[0] is not None and r[1] is None) >= f["blank_addresses"]
                        return False

                    check(f"{doc} fixture matches source", ok_for([tuple(r) for r in src]), f"source has {len(src)} grantees")
                    check(f"{doc} graph matches fixture", ok_for(got), f"graph has {None if got is None else len(got)} grantees")
                for doc in fx["absent_deeds"]:
                    check(f"{doc} is not in the graph", session.run(lookup, documentId=doc).peek() is None)
                cur.execute(SOURCE_TOTALS, {"types": TYPES})
                src = cur.fetchone()
            t = fx.get("totals") or {}
            if t:
                check("source totals match fixture", src == (t["grantees"], t["named"], t["with_addr"], t["deeds"]), f"source gives {src}")
            else:
                check("fixture totals are filled in", False, f"source gives grantees, named, with_addr, deeds = {src}")
            g = session.run(GRAPH_TOTALS).single()
            check("graph totals match source", (g["grantees"], g["named"], g["with_addr"], g["deeds"]) == src,
                  f"graph {(g['grantees'], g['named'], g['with_addr'], g['deeds'])} vs source {src}")
            check("every Grantee is linked to exactly one Deed", g["notone"] == 0 and g["linked"] == g["grantees"], f"{g['notone']} not linked once")
    failed = results.count(False)
    print(f"{len(results) - failed}/{len(results)} checks passed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
