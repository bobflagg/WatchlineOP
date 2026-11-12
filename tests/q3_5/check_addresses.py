"""Check Q3.5 address agreement. Read-only on both databases.

1. Each pair is computed in SQL (tests/q3_5/expected.sql rules) and by src/watchline/compare.py; both must equal the fixture.
2. Each fixture lot is read from the source (newest deeds' grantees, the lot's registered owners), compared in SQL, then read
   from the graph with lookup.cypher and compared with compare.py; outcomes must equal the fixture.
3. The second line is returned apart and does not change the outcome.
Run: uv run python tests/q3_5/check_addresses.py
"""

import os
import sys
from pathlib import Path

import psycopg
import yaml
from dotenv import load_dotenv
from neo4j import GraphDatabase

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from watchline.compare import address_agreement  # noqa: E402

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
REQUIRED_ENV = ("JUSTFIX_DATABASE_URL", "NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD", "NEO4J_DATABASE")
TYPES = ["DEED", "DEED, TS", "DEED, LE", "DEED, RC", "DEEDO", "DEEDP", "CORRD", "CONDEED"]
OUTCOME_SQL = """
SELECT CASE WHEN nullif(btrim(%(la)s), '') IS NULL OR nullif(btrim(%(lb)s), '') IS NULL
              OR substring(%(za)s from '^\\s*(\\d{5})') IS NULL OR substring(%(zb)s from '^\\s*(\\d{5})') IS NULL THEN 'absent'
            WHEN upper(btrim(regexp_replace(%(la)s, '\\s+', ' ', 'g'))) = upper(btrim(regexp_replace(%(lb)s, '\\s+', ' ', 'g')))
             AND substring(%(za)s from '^\\s*(\\d{5})') = substring(%(zb)s from '^\\s*(\\d{5})') THEN 'same'
            ELSE 'differs' END
"""
SOURCE_GRANTEES = """
WITH cur AS (SELECT DISTINCT ON (m.documentid) m.documentid, m.doctype, m.recordedfiled FROM real_property_master m
             WHERE m.documentid IN (SELECT documentid FROM real_property_legals WHERE bbl = %(bbl)s)
             ORDER BY m.documentid, m.modifieddate DESC NULLS LAST, m.goodthroughdate DESC NULLS LAST),
deeds AS (SELECT * FROM cur WHERE doctype = ANY(%(types)s)),
newest AS (SELECT documentid FROM deeds WHERE recordedfiled = (SELECT max(recordedfiled) FROM deeds))
SELECT DISTINCT p.documentid, nullif(btrim(p.name), ''), nullif(btrim(p.address1), ''), nullif(btrim(p.zip), '')
FROM real_property_parties p JOIN newest USING (documentid) WHERE p.partytype = 2
"""
SOURCE_OWNERS = """
SELECT DISTINCT r.registrationid,
       CASE WHEN c.type = 'CorporateOwner' THEN nullif(btrim(c.corporationname), '')
            ELSE nullif(btrim(concat_ws(' ', nullif(btrim(c.firstname), ''), nullif(btrim(c.middleinitial), ''), nullif(btrim(c.lastname), ''))), '') END,
       nullif(btrim(concat_ws(' ', nullif(btrim(c.businesshousenumber), ''), nullif(btrim(c.businessstreetname), ''))), ''),
       nullif(btrim(c.businesszip), '')
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
                def sql_outcome(la, za, lb, zb):
                    cur.execute(OUTCOME_SQL, {"la": la, "za": za, "lb": lb, "zb": zb})
                    return cur.fetchone()[0]

                for la, za, lb, zb, outcome in fx["pairs"]:
                    got = address_agreement(la, za, lb, zb)["outcome"]
                    check(f"pair {outcome} ({la!r} / {lb!r}): compare.py equals the fixture", got == outcome, f"got {got}")
                    check(f"pair {outcome} ({la!r} / {lb!r}): SQL equals the fixture", sql_outcome(la, za, lb, zb) == outcome)
                for ua, ub, expect in fx["units"]:
                    got = address_agreement("1 MAIN ST", "11220", "1 MAIN ST", "11220", ua, ub)
                    check(f"units {ua!r}/{ub!r} are reported apart and the outcome stays same",
                          got["units"] == expect and got["outcome"] == "same", f"got {got}")
                for f in fx["lots"]:
                    bbl = f["bbl"]
                    cur.execute(SOURCE_GRANTEES, {"bbl": bbl, "types": TYPES})
                    sg = [(a, z) for _, _, a, z in cur.fetchall()]
                    cur.execute(SOURCE_OWNERS, {"bbl": bbl})
                    so = [(a, z) for _, _, a, z in cur.fetchall()]
                    src = sorted(sql_outcome(ga, gz, oa, oz) for ga, gz in sg for oa, oz in so)
                    rec = session.run(lookup, bbl=bbl).single()
                    got = sorted(address_agreement(g["mailingAddress"], g["zip"], o["mailingAddress"], o["zip"])["outcome"]
                                 for g in rec["grantees"] for o in rec["owners"]) if rec else None
                    exp = sorted(f["expect"]) if "expect" in f else [f["all"]] * f["pairs"]
                    check(f"{bbl} source pairs match the fixture", src == exp, f"source gives {sorted(set(src))} x{len(src)}")
                    check(f"{bbl} graph outcomes match the fixture", got == exp, f"graph gives {sorted(set(got or []))} x{len(got or [])}")
    failed = results.count(False)
    print(f"{len(results) - failed}/{len(results)} checks passed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
