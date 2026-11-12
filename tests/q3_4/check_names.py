"""Check Q3.4 name agreement. Read-only on both databases.

1. Each pair is computed in SQL (tests/q3_4/expected.sql rules) and by src/watchline/compare.py; both must equal the fixture.
2. Each fixture lot is read from the source (newest deeds, their grantees, the lot's registered owners), compared in SQL,
   then read from the graph with lookup.cypher and compared with compare.py; the outcomes must equal the fixture.
Person names are never printed. Run: uv run python tests/q3_4/check_names.py
"""

import os
import sys
from pathlib import Path

import psycopg
import yaml
from dotenv import load_dotenv
from neo4j import GraphDatabase

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from watchline.compare import name_agreement  # noqa: E402

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
REQUIRED_ENV = ("JUSTFIX_DATABASE_URL", "NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD", "NEO4J_DATABASE")
TYPES = ["DEED", "DEED, TS", "DEED, LE", "DEED, RC", "DEEDO", "DEEDP", "CORRD", "CONDEED"]
OUTCOME_SQL = """
SELECT CASE WHEN nullif(btrim(%(a)s), '') IS NULL OR nullif(btrim(%(b)s), '') IS NULL THEN 'not-comparable'
       WHEN upper(btrim(regexp_replace(%(a)s, '\\s+', ' ', 'g'))) = upper(btrim(regexp_replace(%(b)s, '\\s+', ' ', 'g'))) THEN 'exact-normalized'
       WHEN upper(btrim(regexp_replace(replace(replace(%(a)s, '.', ''), ',', ' '), '\\s+', ' ', 'g')))
          = upper(btrim(regexp_replace(replace(replace(%(b)s, '.', ''), ',', ' '), '\\s+', ' ', 'g'))) THEN 'normalization-match'
       ELSE 'different' END
"""
SOURCE_GRANTEES = """
WITH cur AS (SELECT DISTINCT ON (m.documentid) m.documentid, m.doctype, m.recordedfiled FROM real_property_master m
             WHERE m.documentid IN (SELECT documentid FROM real_property_legals WHERE bbl = %(bbl)s)
             ORDER BY m.documentid, m.modifieddate DESC NULLS LAST, m.goodthroughdate DESC NULLS LAST),
deeds AS (SELECT * FROM cur WHERE doctype = ANY(%(types)s)),
newest AS (SELECT documentid FROM deeds WHERE recordedfiled = (SELECT max(recordedfiled) FROM deeds))
SELECT DISTINCT p.documentid, nullif(btrim(p.name), '') FROM real_property_parties p JOIN newest USING (documentid) WHERE p.partytype = 2
"""
SOURCE_OWNERS = """
SELECT DISTINCT r.registrationid,
       CASE WHEN c.type = 'CorporateOwner' THEN nullif(btrim(c.corporationname), '')
            ELSE nullif(btrim(concat_ws(' ', nullif(btrim(c.firstname), ''), nullif(btrim(c.middleinitial), ''), nullif(btrim(c.lastname), ''))), '') END
FROM hpd_registrations r JOIN hpd_contacts c ON c.registrationid = r.registrationid
WHERE r.bbl = %(bbl)s AND r.bin ~ '^[1-5][0-9]{6}$' AND r.bin !~ '000000$' AND r.registrationid > 0
  AND c.type IN ('CorporateOwner', 'IndividualOwner', 'JointOwner')
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
                def sql_outcome(a, b):
                    cur.execute(OUTCOME_SQL, {"a": a, "b": b})
                    return cur.fetchone()[0]

                for a, b, outcome, rule in fx["pairs"]:
                    label = f"pair {outcome} ({'<null>' if b is None else 'strings'})"
                    got = name_agreement(a, b)
                    check(f"{label}: compare.py equals the fixture", (got["outcome"], got["rule"]) == (outcome, rule), f"got {got}")
                    check(f"{label}: SQL equals the fixture", sql_outcome(a, b) == outcome)
                for f in fx["lots"]:
                    bbl = f["bbl"]
                    cur.execute(SOURCE_GRANTEES, {"bbl": bbl, "types": TYPES})
                    sg = [n for _, n in cur.fetchall()]
                    cur.execute(SOURCE_OWNERS, {"bbl": bbl})
                    so = [n for _, n in cur.fetchall()]
                    src = sorted((sql_outcome(g, o) for g in sg for o in so))
                    rec = session.run(lookup, bbl=bbl).single()
                    got = sorted(name_agreement(g["name"], o["name"])["outcome"] for g in rec["grantees"] for o in rec["owners"]) if rec else None
                    if "expect" in f:
                        exp = sorted(o for _, _, o, _ in f["expect"])
                        check(f"{bbl} source pairs match the fixture", src == exp, f"source gives {src}")
                        check(f"{bbl} graph outcomes match the fixture", got == exp, f"graph gives {got}")
                    else:
                        exp = [f["all"]] * f["pairs"]
                        check(f"{bbl} source pairs match the fixture", src == exp, f"source gives {len(src)} pairs, outcomes {sorted(set(src))}")
                        check(f"{bbl} graph outcomes match the fixture", got == exp, f"graph gives {None if got is None else len(got)} pairs, outcomes {sorted(set(got or []))}")
    failed = results.count(False)
    print(f"{len(results) - failed}/{len(results)} checks passed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
