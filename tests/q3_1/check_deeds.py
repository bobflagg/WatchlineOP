"""Check Deed nodes and HAS_DEED relationships against the frozen source. Read-only on both databases.

1. Each fixture lot is re-derived from the source with SQL, so a stale fixture fails.
2. Each fixture lot is looked up in the graph with tests/q3_1/lookup.cypher and compared.
3. Graph totals must equal the totals computed from the source, and every Deed must be linked to a Lot.
Any failure or error is a failure. Run: uv run python tests/q3_1/check_deeds.py
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

SOURCE_LOT = """
WITH cur AS (
  SELECT DISTINCT ON (m.documentid) m.documentid, m.doctype, m.docdate, m.recordedfiled, m.docamount
  FROM real_property_master m
  WHERE m.documentid IN (SELECT documentid FROM real_property_legals WHERE bbl = %(bbl)s)
  ORDER BY m.documentid, m.modifieddate DESC NULLS LAST, m.goodthroughdate DESC NULLS LAST)
SELECT c.documentid, c.doctype, to_char(c.docdate, 'YYYY-MM-DD'), to_char(c.recordedfiled, 'YYYY-MM-DD'), c.docamount,
       (SELECT count(DISTINCT l2.bbl) - 1 FROM real_property_legals l2 WHERE l2.documentid = c.documentid
          AND (l2.bbl IN (SELECT bbl FROM hpd_registrations)
               OR l2.bbl IN (SELECT p.bbl FROM pluto_latest p WHERE p.unitsres >= 3)))
FROM cur c WHERE c.doctype = ANY(%(types)s)
"""
SCOPE = """
scope AS (SELECT bbl FROM hpd_registrations
          UNION SELECT p.bbl FROM pluto_latest p WHERE p.unitsres >= 3
                AND NOT EXISTS (SELECT 1 FROM hpd_registrations r WHERE r.bbl = p.bbl))
"""
SOURCE_TOTALS = f"""
WITH {SCOPE},
pairs AS (SELECT DISTINCT l.bbl::text AS bbl, l.documentid FROM real_property_legals l JOIN scope s ON s.bbl = l.bbl),
cur AS (SELECT DISTINCT ON (m.documentid) m.documentid, m.doctype, m.docdate, m.recordedfiled
        FROM real_property_master m WHERE m.documentid IN (SELECT documentid FROM pairs)
        ORDER BY m.documentid, m.modifieddate DESC NULLS LAST, m.goodthroughdate DESC NULLS LAST),
deeds AS (SELECT * FROM cur WHERE doctype = ANY(%(types)s)),
dp AS (SELECT p.bbl, p.documentid, d.recordedfiled FROM pairs p JOIN deeds d USING (documentid)),
top AS (SELECT bbl, max(recordedfiled) AS mx FROM dp GROUP BY bbl),
tied AS (SELECT dp.bbl FROM dp JOIN top t ON t.bbl = dp.bbl AND t.mx = dp.recordedfiled GROUP BY dp.bbl HAVING count(*) > 1)
SELECT (SELECT count(*) FROM deeds), (SELECT count(*) FROM dp), (SELECT count(*) FROM deeds WHERE docdate IS NOT NULL),
       (SELECT count(DISTINCT bbl) FROM dp), (SELECT count(*) FROM tied)
"""
GRAPH_TOTALS = """
CALL () { MATCH (d:Deed) RETURN count(d) AS deeds, count(d.docDate) AS with_docdate }
CALL () { MATCH (:Lot)-[h:HAS_DEED]->(:Deed) RETURN count(h) AS pairs }
CALL () { MATCH (l:Lot)-[:HAS_DEED]->(:Deed) RETURN count(DISTINCT l) AS lots }
CALL () { MATCH (l:Lot)-[:HAS_DEED]->(d:Deed) WITH l, max(d.recordedDate) AS mx
          MATCH (l)-[:HAS_DEED]->(d2:Deed {recordedDate: mx}) WITH l, count(d2) AS c WHERE c > 1 RETURN count(l) AS tied }
CALL () { MATCH (d:Deed) WHERE NOT (:Lot)-[:HAS_DEED]->(d) RETURN count(d) AS orphans }
CALL () { MATCH (d:Deed) WHERE NOT d.docType IN $types RETURN count(d) AS badtype }
RETURN deeds, with_docdate, pairs, lots, tied, orphans, badtype
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
                for f in fx["lots"]:
                    bbl = f["bbl"]
                    cur.execute(SOURCE_LOT, {"bbl": bbl, "types": TYPES})
                    src = {d: [t, dd, r, a, o] for d, t, dd, r, a, o in cur.fetchall()}
                    rec = session.run(lookup, bbl=bbl).single()
                    got = {x["documentId"]: [x["docType"], x["docDate"], x["recordedDate"], x["amount"], x["otherLots"]]
                           for x in rec["deeds"]} if rec else None
                    for name, deeds in (("source", src), ("graph", got)):
                        if deeds is None:
                            check(f"{bbl} is in the {name}", False)
                            continue
                        newest = max((v[2] for v in deeds.values()), default=None)
                        latest = {k: v for k, v in deeds.items() if v[2] == newest}
                        ok = True
                        if "latest" in f:
                            ok = latest == {k: list(v) for k, v in f["latest"].items()}
                        if "includes" in f:
                            ok = ok and all(deeds.get(k) == list(v) for k, v in f["includes"].items())
                        if "excludes" in f:
                            ok = ok and not any(k in deeds for k in f["excludes"])
                        if "deed_count" in f:
                            ok = ok and len(deeds) == f["deed_count"] and newest == f.get("latest_recorded")
                        check(f"{bbl} {name} matches fixture", ok, f"{name} gives latest {latest}, {len(deeds)} deeds")
                for bbl in fx["absent_lots"]:
                    check(f"{bbl} has no Lot in the graph, so no deeds", session.run(lookup, bbl=bbl).peek() is None)
                cur.execute(SOURCE_TOTALS, {"types": TYPES})
                src = cur.fetchone()
            t = fx.get("totals") or {}
            if t:
                check("source totals match fixture", src == (t["deeds"], t["pairs"], t["with_docdate"], t["lots"], t["tied"]), f"source gives {src}")
            else:
                check("fixture totals are filled in", False, f"source gives deeds, pairs, with_docdate, lots, tied = {src}")
            g = session.run(GRAPH_TOTALS, types=TYPES).single()
            check("graph totals match source", (g["deeds"], g["pairs"], g["with_docdate"], g["lots"], g["tied"]) == src,
                  f"graph {(g['deeds'], g['pairs'], g['with_docdate'], g['lots'], g['tied'])} vs source {src}")
            check("every Deed is linked to a Lot", g["orphans"] == 0, f"{g['orphans']} unlinked")
            check("only deed types are loaded", g["badtype"] == 0, f"{g['badtype']} other types")
    failed = results.count(False)
    print(f"{len(results) - failed}/{len(results)} checks passed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
