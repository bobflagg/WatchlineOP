"""Load what a landlord record is called, where it files from, and which one anchors each group (release v0.3.0).

Run after scripts/load_networks.py and load_portfolios.py (they create the Landlord, OperationalNetwork and OwnerPortfolio nodes).
Reads the release with src/watchline/bor_release.py and refuses to load unless the zip checksum, the manifest identity and the
checksums of node_names, node_observations, observation_contacts and groups match data/sources.yaml and the manifest.
  - Landlord.name: node_names.name, exactly as the release spells it (leading punctuation and case kept). Never blank.
  - Landlord.businessAddresses: one string per distinct business address on the HPD contacts that WoW chose for the landlord's lots
    (node_observations.selected_observation_id -> observation_contacts), as filed: "<house> <street> <apartment>, <city>, <state> <zip>"
    with blank parts left out. Spelling variants (BROOKLYN, Brooklyn) stay separate values; sorted. Absent when no selected
    observation has an address (95 landlords have no selected observation).
  - (OwnerPortfolio)-[:ANCHORED_BY]->(Landlord) and (OperationalNetwork)-[:ANCHORED_BY]->(Landlord) from groups.anchor_node_id: the
    member with the most lots, ties to the smallest node id. A display rule, not a finding about ownership; node ids are renumbered by
    every rebuild, so an anchor is valid for this release only.
Safe to rerun (SET and MERGE). Writes only to the POC database. Run: uv run python scripts/load_landlord_labels.py
"""

import os
import sys
from collections import defaultdict
from pathlib import Path

from dotenv import load_dotenv
from neo4j import GraphDatabase

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from watchline.bor_release import BorRelease  # noqa: E402

POC_DATABASE = "watchline"
REQUIRED_ENV = ("NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD", "NEO4J_DATABASE")
BATCH = 5000
TABLES = ("node_names", "node_observations", "observation_contacts", "groups", "group_members")

CLEAR = "MATCH (a:Landlord) WHERE a.businessAddresses IS NOT NULL REMOVE a.businessAddresses"
LOAD_LABELS = """
UNWIND $rows AS row
MATCH (a:Landlord {nodeId: row.nodeId})
SET a.name = row.name
FOREACH (_ IN CASE WHEN size(row.addresses) > 0 THEN [1] ELSE [] END | SET a.businessAddresses = row.addresses)
RETURN count(*) AS set
"""
LOAD_ANCHOR_P = """
UNWIND $rows AS row
MATCH (g:OwnerPortfolio {groupId: row.groupId})
MATCH (a:Landlord {nodeId: row.nodeId})
MERGE (g)-[:ANCHORED_BY]->(a)
RETURN count(*) AS linked
"""
LOAD_ANCHOR_N = LOAD_ANCHOR_P.replace("OwnerPortfolio", "OperationalNetwork")
COUNTS = """
CALL () { MATCH (a:Landlord) WHERE a.name IS NOT NULL RETURN count(a) AS named }
CALL () { MATCH (a:Landlord) WHERE a.businessAddresses IS NOT NULL RETURN count(a) AS withAddress }
CALL () { MATCH (:OwnerPortfolio)-[r:ANCHORED_BY]->(:Landlord) RETURN count(r) AS portfolios }
CALL () { MATCH (:OperationalNetwork)-[r:ANCHORED_BY]->(:Landlord) RETURN count(r) AS networks }
RETURN named, withAddress, portfolios, networks
"""


def address(c: dict) -> str | None:
    street = " ".join(p.strip() for p in (c["business_house"], c["business_street"], c["business_apartment"]) if p and p.strip())
    state_zip = " ".join(p.strip() for p in (c["business_state"], c["business_zip"]) if p and p.strip())
    parts = [p for p in (street, (c["business_city"] or "").strip(), state_zip) if p]
    return ", ".join(parts) or None


def batches(rows):
    for i in range(0, len(rows), BATCH):
        yield rows[i:i + BATCH]


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
    names = {int(r["node_id"]): r["name"] for r in release.rows("node_names")}
    if any(not names.get(n) for n in nodes):
        print("refusing: a group member has no name in node_names", file=sys.stderr)
        return 1
    contacts = {r["observation_id"]: r for r in release.rows("observation_contacts")}
    found: dict[int, set[str]] = defaultdict(set)
    for r in release.rows("node_observations"):
        n = int(r["node_id"])
        c = contacts.get(r["selected_observation_id"])
        if n in nodes and c and (a := address(c)):
            found[n].add(a)
    rows = [{"nodeId": n, "name": names[n], "addresses": sorted(found.get(n, ()))} for n in sorted(nodes)]
    anchors = {"owner_portfolio": [], "operational_network": []}
    for g in release.rows("groups"):
        if int(g["anchor_node_id"]) not in nodes:
            print(f"refusing: anchor {g['anchor_node_id']} of {g['group_id']} is not a group member", file=sys.stderr)
            return 1
        anchors[g["layer"]].append({"groupId": g["group_id"], "nodeId": int(g["anchor_node_id"])})

    driver = GraphDatabase.driver(os.environ["NEO4J_URI"], auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]))
    with driver, driver.session(database=POC_DATABASE) as session:
        session.run(CLEAR).consume()
        for b in batches(rows):
            session.execute_write(lambda tx, b=b: tx.run(LOAD_LABELS, rows=b).consume())
        for query, layer in ((LOAD_ANCHOR_P, "owner_portfolio"), (LOAD_ANCHOR_N, "operational_network")):
            for b in batches(anchors[layer]):
                session.execute_write(lambda tx, b=b, q=query: tx.run(q, rows=b).consume())
        got = session.run(COUNTS).single()
    want = (len(rows), sum(1 for r in rows if r["addresses"]), len(anchors["owner_portfolio"]), len(anchors["operational_network"]))
    have = (got["named"], got["withAddress"], got["portfolios"], got["networks"])
    print(f"named {have[0]:,} (release {want[0]:,}), with address {have[1]:,} (release {want[1]:,}), "
          f"portfolio anchors {have[2]:,} (release {want[2]:,}), network anchors {have[3]:,} (release {want[3]:,})")
    return 0 if have == want else 1


if __name__ == "__main__":
    sys.exit(main())
