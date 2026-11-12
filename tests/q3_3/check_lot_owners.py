"""Check Q3.3: a lot's recorded owners through its buildings' registrations (the Q2 path). Read-only on both databases.
Each fixture is re-derived from the source, then compared with the graph lookup. Run: uv run python tests/q3_3/check_lot_owners.py
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
SOURCE = """
SELECT DISTINCT r.registrationid, c.type,
       CASE WHEN c.type = 'CorporateOwner' THEN nullif(btrim(c.corporationname), '')
            ELSE nullif(btrim(concat_ws(' ', nullif(btrim(c.firstname), ''), nullif(btrim(c.middleinitial), ''),
                                         nullif(btrim(c.lastname), ''))), '') END
FROM hpd_registrations r JOIN hpd_contacts c ON c.registrationid = r.registrationid
WHERE r.bbl = %(bbl)s AND r.bin ~ '^[1-5][0-9]{6}$' AND r.bin !~ '000000$' AND r.registrationid > 0
  AND c.type IN ('CorporateOwner', 'IndividualOwner', 'JointOwner')
"""
results = []


def check(name, ok, detail=""):
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  ({detail})" if detail and not ok else ""))


def mask(rid, t, n):
    return (rid, t, n if t == "CorporateOwner" or n is None else "<person>")


def main() -> int:
    load_dotenv(ROOT / ".env")
    missing = [k for k in REQUIRED_ENV if not os.environ.get(k)]
    if missing:
        print(f"missing in .env: {', '.join(missing)}", file=sys.stderr)
        return 1
    fx = yaml.safe_load((HERE / "fixtures.yaml").read_text())
    lookup = (HERE / "lookup.cypher").read_text()
    key = lambda r: (r[0], r[1], r[2] or "")
    driver = GraphDatabase.driver(os.environ["NEO4J_URI"], auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]))
    with driver, driver.session(database=os.environ["NEO4J_DATABASE"], default_access_mode="READ") as session:
        with psycopg.connect(os.environ["JUSTFIX_DATABASE_URL"]) as pg:
            pg.read_only = True
            with pg.cursor() as cur:
                for f in fx["lots"]:
                    exp = sorted((tuple(o) for o in f["owners"]), key=key)
                    cur.execute(SOURCE, {"bbl": f["bbl"]})
                    src = sorted((mask(*r) for r in cur.fetchall()), key=key)
                    check(f"{f['bbl']} fixture matches source", src == exp, f"source gives {src}")
                    rows = session.run(lookup, bbl=f["bbl"]).data()
                    got = sorted((mask(r["registrationId"], o["contactType"], o["name"]) for r in rows for o in r["owners"]), key=key)
                    check(f"{f['bbl']} graph matches fixture", got == exp, f"graph gives {got}")
    failed = results.count(False)
    print(f"{len(results) - failed}/{len(results)} checks passed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
