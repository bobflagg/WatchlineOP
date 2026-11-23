"""Check Q7.1 (shared HPD business addresses and people between two entities) against the frozen source. Read-only on both databases.

1. Each fixture pair is re-derived from the source with tests/q7_1/expected.sql (registrations found by exact N3 corporation name,
   shared addresses by street line plus first five ZIP characters, hub registrations per address, shared people counted only).
2. Each pair is looked up in the graph with tests/q7_1/lookup.cypher and compared. Person names are never printed or stored in fixtures.
3. Graph Contact.nameKey must equal rule N3 of corporationName on every contact that has one.
Any failure or error is a failure. Run: uv run python tests/q7_1/check_shared_contacts.py
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
SQL_N3 = ("btrim(regexp_replace(replace(replace(replace(replace(upper(btrim(corporationname)), '.', ''), ',', ' '), '''', ''), "
          "E'\\t', ' '), '\\s+', ' ', 'g'))")
VALID = ("SELECT registrationid FROM hpd_registrations WHERE bbl IS NOT NULL AND bin ~ '^[1-5][0-9]{6}$' "
         "AND bin !~ '000000$' AND registrationid > 0")
SOURCE_REGS = f"SELECT DISTINCT registrationid FROM hpd_contacts WHERE registrationid IN ({VALID}) AND {SQL_N3} = %(key)s"
SOURCE_ADDR = f"""
WITH a AS (SELECT DISTINCT upper(btrim(coalesce(businesshousenumber,'')||' '||coalesce(businessstreetname,''))) street,
                  left(btrim(coalesce(businesszip,'')),5) zip5
           FROM hpd_contacts WHERE registrationid = ANY(%(regs)s) AND btrim(coalesce(businessstreetname,'')) <> '' AND btrim(coalesce(businesszip,'')) <> ''),
b AS (SELECT DISTINCT upper(btrim(coalesce(businesshousenumber,'')||' '||coalesce(businessstreetname,''))) street,
                  left(btrim(coalesce(businesszip,'')),5) zip5
           FROM hpd_contacts WHERE registrationid = ANY(%(regs_b)s) AND btrim(coalesce(businessstreetname,'')) <> '' AND btrim(coalesce(businesszip,'')) <> '')
SELECT a.street, a.zip5, (SELECT count(DISTINCT registrationid) FROM hpd_contacts h WHERE registrationid IN ({VALID})
        AND upper(btrim(coalesce(h.businesshousenumber,'')||' '||coalesce(h.businessstreetname,''))) = a.street
        AND left(btrim(coalesce(h.businesszip,'')),5) = a.zip5)
FROM a JOIN b USING (street, zip5) ORDER BY 1, 2
"""
SOURCE_PEOPLE = """
WITH p AS (SELECT upper(nullif(btrim(concat_ws(' ', nullif(btrim(firstname), ''), nullif(btrim(middleinitial), ''),
                                                  nullif(btrim(lastname), ''))), '')) n, registrationid FROM hpd_contacts)
SELECT count(*) FROM (SELECT n FROM p WHERE n IS NOT NULL AND registrationid = ANY(%(regs)s) INTERSECT SELECT n FROM p WHERE registrationid = ANY(%(regs_b)s)) s
"""
GRAPH_KEYS = "MATCH (c:Contact) WHERE c.corporationName IS NOT NULL RETURN c.corporationName AS n, c.nameKey AS k"
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
        bad = sum(1 for r in session.run(GRAPH_KEYS) if r["k"] != n3(r["n"]))
        check("Contact.nameKey equals N3 of corporationName on every named contact", bad == 0, f"{bad} differ")
        with psycopg.connect(os.environ["JUSTFIX_DATABASE_URL"]) as pg:
            pg.read_only = True
            with pg.cursor() as cur:
                for f in fx["pairs"]:
                    label = f"{f['a']} and {f['b']}"
                    ka, kb = n3(f["a"]), n3(f["b"])
                    cur.execute(SOURCE_REGS, {"key": ka})
                    regs_a = [r[0] for r in cur.fetchall()]
                    cur.execute(SOURCE_REGS, {"key": kb})
                    regs_b = [r[0] for r in cur.fetchall()]
                    cur.execute(SOURCE_ADDR, {"regs": regs_a, "regs_b": regs_b})
                    src_addr = [(s, z, n) for s, z, n in cur.fetchall()]
                    cur.execute(SOURCE_PEOPLE, {"regs": regs_a, "regs_b": regs_b})
                    src_people = cur.fetchone()[0]
                    rec = session.run(lookup, nameKeyA=ka, nameKeyB=kb).single()
                    check(f"{label}: fixture matches source",
                          (len(regs_a), len(regs_b), len(src_addr), src_people)
                          == (f["registrationsA"], f["registrationsB"], len(f["addresses"]), f["sharedPeople"]),
                          f"source {(len(regs_a), len(regs_b), len(src_addr), src_people)}")
                    if rec is None:
                        check(f"{label}: graph returns a row", False)
                        continue
                    got = sorted((a["street"], a["zip5"], a["registrations"]) for a in rec["sharedAddresses"])
                    check(f"{label}: registrations match", (rec["registrationsA"], rec["registrationsB"]) == (len(regs_a), len(regs_b)))
                    check(f"{label}: shared addresses and hub registrations match source", got == sorted(src_addr), f"graph {got} vs source {sorted(src_addr)}")
                    check(f"{label}: shared addresses match fixture",
                          got == sorted((a["street"], a["zip5"], a["registrations"]) for a in f["addresses"]))
                    check(f"{label}: shared people count matches source", len(rec["sharedPeople"]) == src_people,
                          f"graph {len(rec['sharedPeople'])} vs source {src_people}")
    failed = results.count(False)
    print(f"{len(results) - failed}/{len(results)} checks passed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
