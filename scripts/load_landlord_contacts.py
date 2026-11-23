"""Load (Landlord)-[:BASED_ON_CONTACT]->(Contact): the HPD contacts Who Owns What chose to stand for each landlord record (release v0.3.0).

Run after scripts/load_registrations.py and scripts/load_landlord_labels.py. Reads the release with src/watchline/bor_release.py and
refuses to load unless the zip checksum, the manifest identity and the checksums of node_observations, observation_contacts and
group_members match data/sources.yaml and the manifest.
  - For each landlord record, each distinct selected observation (node_observations.selected_observation_id -> observation_contacts)
    names an HPD contact by registration, type, corporation name and person name (first name, middle initial and last name joined by
    single spaces, blanks left out). It is linked to every Contact on that Registration with that type and those two names.
  - The release records no title, so contacts that differ only in title are all linked (the graph key includes the title).
  - A registration that is not in the graph (no valid BIN) or a contact the graph does not hold is counted and not linked; nothing is
    created and no match is guessed. The link is the record WoW used, not a finding that the landlord is the owner.
Safe to rerun (the links are cleared and rebuilt). Writes only to the POC database. Run: uv run python scripts/load_landlord_contacts.py
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from neo4j import GraphDatabase

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from watchline.bor_release import BorRelease  # noqa: E402

POC_DATABASE = "watchline"
REQUIRED_ENV = ("NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD", "NEO4J_DATABASE")
BATCH = 5000
TABLES = ("node_observations", "observation_contacts", "group_members")

CLEAR = "MATCH (:Landlord)-[r:BASED_ON_CONTACT]->(:Contact) DELETE r"
LOAD = """
UNWIND $rows AS row
MATCH (a:Landlord {nodeId: row.nodeId})
OPTIONAL MATCH (r:Registration {registrationId: row.rid})
OPTIONAL MATCH (r)-[:HAS_CONTACT]->(c:Contact {contactType: row.type})
  WHERE coalesce(c.corporationName, '') = row.corp AND coalesce(c.personName, '') = row.person
WITH row, a, r, collect(c) AS cs
FOREACH (c IN cs | MERGE (a)-[:BASED_ON_CONTACT]->(c))
RETURN count(*) AS rows,
       sum(CASE WHEN r IS NULL THEN 1 ELSE 0 END) AS noRegistration,
       sum(CASE WHEN r IS NOT NULL AND size(cs) = 0 THEN 1 ELSE 0 END) AS noContact,
       sum(CASE WHEN size(cs) = 1 THEN 1 ELSE 0 END) AS one,
       sum(CASE WHEN size(cs) > 1 THEN 1 ELSE 0 END) AS several,
       sum(size(cs)) AS links
"""
COUNT = "MATCH (:Landlord)-[r:BASED_ON_CONTACT]->(:Contact) RETURN count(r) AS n, count(DISTINCT startNode(r)) AS landlords"


def person(c: dict) -> str:
    return " ".join(p.strip() for p in (c["first_name"], c["middle_initial"], c["last_name"]) if p and p.strip())


def main() -> int:
    load_dotenv(ROOT / ".env")
    missing = [k for k in REQUIRED_ENV if not os.environ.get(k)]
    if missing:
        print(f"missing in .env: {', '.join(missing)}", file=sys.stderr)
        return 1
    if os.environ["NEO4J_DATABASE"] != POC_DATABASE:
        print(f"refusing: NEO4J_DATABASE is not the POC database '{POC_DATABASE}'", file=sys.stderr)
        return 1
    release = BorRelease()
    problems = release.verify_identity()
    if not release.verify_zip():
        problems.append("zip sha256 differs from data/sources.yaml")
    problems += [f"{t}.csv checksum differs from the manifest" for t in TABLES if not release.verify_member(t)]
    if problems:
        print("refusing: the release is not the pinned one:\n  " + "\n  ".join(problems), file=sys.stderr)
        return 1

    nodes = {int(r["node_id"]) for r in release.rows("group_members")}
    contacts = {r["observation_id"]: r for r in release.rows("observation_contacts")}
    keys = set()
    for r in release.rows("node_observations"):
        n = int(r["node_id"])
        c = contacts.get(r["selected_observation_id"])
        if n in nodes and c:
            keys.add((n, int(r["registration_id"]), c["contact_type"], (c["corporation_name"] or "").strip(), person(c)))
    rows = [{"nodeId": n, "rid": rid, "type": t, "corp": co, "person": pe} for n, rid, t, co, pe in sorted(keys)]

    total = dict.fromkeys(("rows", "noRegistration", "noContact", "one", "several", "links"), 0)
    driver = GraphDatabase.driver(os.environ["NEO4J_URI"], auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]))
    with driver, driver.session(database=POC_DATABASE) as session:
        session.run(CLEAR).consume()
        for i in range(0, len(rows), BATCH):
            got = session.execute_write(lambda tx, b=rows[i:i + BATCH]: tx.run(LOAD, rows=b).single())
            for k in total:
                total[k] += got[k]
        g = session.run(COUNT).single()
    print(f"selected contacts {len(rows):,}: linked to one contact {total['one']:,}, to several (titles differ) {total['several']:,}, "
          f"registration not in the graph {total['noRegistration']:,}, no matching contact {total['noContact']:,}")
    print(f"BASED_ON_CONTACT: graph {g['n']:,} on {g['landlords']:,} landlords, loader {total['links']:,}")
    ok = total["rows"] == len(rows) and g["n"] == total["links"]
    print("reconciled" if ok else "MISMATCH between loaded and graph counts", file=sys.stdout if ok else sys.stderr)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
