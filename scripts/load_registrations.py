"""Load Registration nodes, HAS_REGISTRATION relationships and Contact nodes (Q2.1, Q2.2, Q3.5, Q4).

Run after scripts/load_buildings.py. Rules (see tests/q2_1/expected.sql, tests/q2_2/expected.sql and tests/q4_1/expected.sql):
  - Registration: one per distinct registrationid on a row with a valid BIN (the BIN rule of Q1.2). registrationid 0
    is a placeholder shared by three unrelated buildings, so rows with it (3 pairs, and its 27 contacts, 6 of owner
    type) are excluded and counted, never turned into a registration.
  - HAS_REGISTRATION: one per distinct (BIN, registrationid). lastRegistered and registrationEnd are the
    dates on those rows; if the rows disagree, or only some are null, the date is absent, never picked.
  - Contact: a contact of any of the nine HPD types (CorporateOwner, IndividualOwner, JointOwner, Agent, HeadOfficer,
    Officer, Shareholder, SiteManager, Lessee) on a loaded registration. Exact duplicates (same registration, type,
    corporation name, person name and title) are one contact. registrationcontactid is not unique in the snapshot,
    so the key is contactKey = registrationid|type|corporation|person|title. corporationName is the corporation name;
    personName is the first name, middle initial and last name joined by single spaces; a name part or the title that
    is blank is absent.
  - Contact also carries the business address HPD records (Q3.5, Q4.2): mailingAddress (house number and street name),
    addressLine2 (apartment) and zip, as recorded, blank is absent. When exact duplicate contacts disagree on one
    of them, that value is absent, never picked.
  - Both endpoints must already exist; a missing Building is an error.

Safe to rerun (MERGE). Reads the source read-only and writes only to the POC database.
Run: uv run python scripts/load_registrations.py
"""

import os
import re
import sys
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from neo4j import GraphDatabase

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from watchline.compare import n3  # noqa: E402

POC_DATABASE = "watchline"
BATCH = 5000
OWNER_TYPES = ("CorporateOwner", "IndividualOwner", "JointOwner")
BIN_PATTERN = re.compile(r"^[1-5][0-9]{6}$")
REQUIRED_ENV = ("JUSTFIX_DATABASE_URL", "NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD", "NEO4J_DATABASE")
VALID_BIN = "bin ~ '^[1-5][0-9]{6}$' AND bin !~ '000000$' AND registrationid > 0"

PAIRS_SQL = f"""
SELECT registrationid::bigint, btrim(bin) AS bin,
       CASE WHEN count(DISTINCT lastregistrationdate) = 1 AND count(lastregistrationdate) = count(*)
            THEN min(lastregistrationdate) END AS last_registered,
       CASE WHEN count(DISTINCT registrationenddate) = 1 AND count(registrationenddate) = count(*)
            THEN min(registrationenddate) END AS registration_end
FROM hpd_registrations WHERE bbl IS NOT NULL AND {VALID_BIN}
GROUP BY registrationid, bin ORDER BY registrationid, bin
"""
ADDR = "nullif(btrim(concat_ws(' ', nullif(btrim(c.businesshousenumber), ''), nullif(btrim(c.businessstreetname), ''))), '')"


def agree(expr):
    return (f"CASE WHEN count(DISTINCT {expr}) = 1 AND count({expr}) = count(*) THEN min({expr}) END")


CONTACTS_SQL = f"""
SELECT c.registrationid::bigint, c.type, nullif(btrim(c.corporationname), '') AS corp,
       nullif(btrim(concat_ws(' ', nullif(btrim(c.firstname), ''), nullif(btrim(c.middleinitial), ''),
                                    nullif(btrim(c.lastname), ''))), '') AS person,
       nullif(btrim(c.title), '') AS title,
       {agree(ADDR)} AS mailing_address,
       {agree("nullif(btrim(c.businessapartment), '')")} AS address_line2,
       {agree("nullif(btrim(c.businesszip), '')")} AS zip
FROM hpd_contacts c
WHERE c.registrationid IN (SELECT registrationid FROM hpd_registrations WHERE bbl IS NOT NULL AND {VALID_BIN})
GROUP BY c.registrationid, c.type, 3, 4, 5 ORDER BY 1, 2, 3, 4, 5
"""
CONSTRAINTS = [
    "CREATE CONSTRAINT registration_id_unique IF NOT EXISTS FOR (r:Registration) REQUIRE r.registrationId IS UNIQUE",
    "CREATE CONSTRAINT contact_key_unique IF NOT EXISTS FOR (c:Contact) REQUIRE c.contactKey IS UNIQUE",
    "CREATE INDEX contact_name_key IF NOT EXISTS FOR (c:Contact) ON (c.nameKey)",
]
LOAD_PAIRS = """
UNWIND $rows AS row
MATCH (b:Building {bin: row.bin})
MERGE (r:Registration {registrationId: row.rid})
MERGE (b)-[h:HAS_REGISTRATION]->(r)
SET h.lastRegistered = CASE WHEN row.last IS NULL THEN null ELSE date(row.last) END,
    h.registrationEnd = CASE WHEN row.end IS NULL THEN null ELSE date(row.end) END
RETURN count(*) AS linked
"""
LOAD_CONTACTS = """
UNWIND $rows AS row
MATCH (r:Registration {registrationId: row.rid})
MERGE (c:Contact {contactKey: row.key})
SET c.contactType = row.type, c.corporationName = row.corp, c.nameKey = row.nameKey, c.personName = row.person, c.title = row.title,
    c.mailingAddress = row.addr, c.addressLine2 = row.line2, c.zip = row.zip
MERGE (r)-[:HAS_CONTACT]->(c)
RETURN count(*) AS linked
"""
COUNTS = """
CALL () { MATCH (r:Registration) RETURN count(r) AS regs }
CALL () { MATCH (:Building)-[h:HAS_REGISTRATION]->(:Registration) RETURN count(h) AS pairs,
          count(h.lastRegistered) AS lasts, count(h.registrationEnd) AS ends }
CALL () { MATCH (c:Contact) RETURN count(c) AS contacts, count(c.title) AS titled, count(c.mailingAddress) AS addressed,
          count(CASE WHEN c.contactType IN ['CorporateOwner','IndividualOwner','JointOwner'] THEN 1 END) AS owners }
RETURN regs, pairs, lasts, ends, contacts, titled, addressed, owners
"""


def batches(pg, name, sql):
    with pg.cursor(name=name) as cur:
        cur.itersize = BATCH
        cur.execute(sql)
        while rows := cur.fetchmany(BATCH):
            yield rows


def main() -> int:
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    missing = [k for k in REQUIRED_ENV if not os.environ.get(k)]
    if missing:
        print(f"missing in .env: {', '.join(missing)}", file=sys.stderr)
        return 1
    if os.environ["NEO4J_DATABASE"] != POC_DATABASE:
        print(f"refusing: NEO4J_DATABASE is not the POC database '{POC_DATABASE}'", file=sys.stderr)
        return 1

    staged = {"pairs": 0, "lasts": 0, "ends": 0, "contacts": 0, "titled": 0, "addressed": 0, "owners": 0}
    regs = set()
    linked_pairs = linked_contacts = 0
    driver = GraphDatabase.driver(os.environ["NEO4J_URI"], auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]))
    try:
        driver.verify_connectivity()
    except Exception as exc:
        print(f"cannot reach Neo4j ({type(exc).__name__}). Is the DBMS started in Neo4j Desktop?", file=sys.stderr)
        return 1

    with driver, driver.session(database=POC_DATABASE) as session:
        for c in CONSTRAINTS:
            session.run(c).consume()
        # registrationid 0 was loaded before it was found to be a placeholder; remove it and its contacts
        session.run("MATCH (r:Registration) WHERE r.registrationId < 1 OPTIONAL MATCH (r)-[:HAS_CONTACT]->(c) DETACH DELETE c, r").consume()
        with psycopg.connect(os.environ["JUSTFIX_DATABASE_URL"]) as pg:
            pg.read_only = True
            for rows in batches(pg, "pairs", PAIRS_SQL):
                batch = []
                for rid, b, last, end in rows:
                    if not BIN_PATTERN.match(b):
                        raise ValueError(f"invalid BIN from source: {b!r}")
                    batch.append({"rid": rid, "bin": b, "last": last.isoformat() if last else None,
                                  "end": end.isoformat() if end else None})
                    regs.add(rid)
                staged["pairs"] += len(batch)
                staged["lasts"] += sum(1 for r in batch if r["last"])
                staged["ends"] += sum(1 for r in batch if r["end"])
                linked_pairs += session.execute_write(lambda tx, b=batch: tx.run(LOAD_PAIRS, rows=b).single()["linked"])
            print(f"  registrations {len(regs):,}, pairs {staged['pairs']:,}", flush=True)
            for rows in batches(pg, "contacts", CONTACTS_SQL):
                batch = [{"key": f"{r}|{t}|{co or ''}|{pe or ''}|{ti or ''}", "rid": r, "type": t, "corp": co, "person": pe,
                          "title": ti, "addr": a, "line2": l, "zip": z, "nameKey": n3(co) if co else None} for r, t, co, pe, ti, a, l, z in rows]
                staged["contacts"] += len(batch)
                staged["titled"] += sum(1 for r in batch if r["title"])
                staged["addressed"] += sum(1 for r in batch if r["addr"])
                staged["owners"] += sum(1 for r in batch if r["type"] in OWNER_TYPES)
                linked_contacts += session.execute_write(lambda tx, b=batch: tx.run(LOAD_CONTACTS, rows=b).single()["linked"])
        g = session.run(COUNTS).single()

    print(f"staged: registrations {len(regs):,}, pairs {staged['pairs']:,} (dates {staged['lasts']:,}/{staged['ends']:,}), "
          f"contacts {staged['contacts']:,} (owner types {staged['owners']:,}, titled {staged['titled']:,}, addressed {staged['addressed']:,})")
    print(f"graph:  registrations {g['regs']:,}, pairs {g['pairs']:,} (dates {g['lasts']:,}/{g['ends']:,}), "
          f"contacts {g['contacts']:,} (owner types {g['owners']:,}, titled {g['titled']:,}, addressed {g['addressed']:,})")
    ok = (linked_pairs == staged["pairs"] and linked_contacts == staged["contacts"]
          and (len(regs), staged["pairs"], staged["lasts"], staged["ends"], staged["contacts"], staged["titled"],
               staged["addressed"], staged["owners"])
          == (g["regs"], g["pairs"], g["lasts"], g["ends"], g["contacts"], g["titled"], g["addressed"], g["owners"]))
    print("reconciled" if ok else "MISMATCH between staged and graph counts", file=sys.stdout if ok else sys.stderr)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
