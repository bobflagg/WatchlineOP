"""Load Operational Networks from the pinned BOR release (Q8.1, Q8.2, Q8.3, Q8.4).

Run after scripts/load_lots.py and load_buildings.py. Reads the release with src/watchline/bor_release.py and
refuses to load unless the zip checksum, the manifest identity and the checksum of each file read all match
data/sources.yaml. Rules (see tests/q8_1, q8_2, q8_4 and profiles/bor_layers.yaml):
  - OperationalNetwork per Operational Network group in groups.csv, with groupId and split (wcc or louvain).
    groupId is run-local; the run is recorded once in data/sources.yaml, not on the node.
  - (Lot)-[:IN_NETWORK]->(OperationalNetwork) per row of group_bbls.csv. Every member lot must already be a Lot:
    a missing Lot is an error, never created here. All members are rental lots, so no flag is stored.
  - Lot.networkAbsence (top-level reason) and Lot.networkAbsenceDetail (BOR's code) for each not_in_group row of
    bbl_status.csv whose BBL is a Lot. Rows for BBLs outside the graph are counted, not loaded. A Lot with no
    status row (an HPD lot missing from PLUTO) gets neither property.
  - Landlord per node of network_membership that has a network (a Who Owns What landlord record: contact kind, name and
    business address as filed with HPD; the name and addresses are set by scripts/load_landlord_labels.py). Keyed by nodeId, which is run-local.
  - (Landlord)-[:COVERS {registrationId}]->(Lot) per node_observations row of such a node. Every lot must be a Lot.
  - Edges between landlords are loaded by scripts/load_graph_edges.py (release v0.3.0 publishes every edge in graph_edges.csv).

Safe to rerun: networks and memberships are MERGEd, and the two reason properties are cleared and set again.
Reads the release read-only and writes only to the POC database.
Run: uv run python scripts/load_networks.py
"""

import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from neo4j import GraphDatabase

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from watchline.bor_release import BorRelease  # noqa: E402

POC_DATABASE = "watchline"
BATCH = 5000
LAYER = "operational_network"
REQUIRED_ENV = ("NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD", "NEO4J_DATABASE")
TOP_LEVEL = {"no_qualifying_linkage", "excluded_by_policy", "below_eligibility_rule", "outside_source_coverage", "outside_method_input"}
DETAIL = {"no_linkage", "no_registration", "no_owner_contact", "aggregator_address_masked", "address_evidence_masked", "first_name_veto",
          "common_name_veto", "shared_company_degree_unknown", "shared_company_name_not_rare", "shared_company_first_name_conflict",
          "shared_company_degree_cap"}

CONSTRAINT = "CREATE CONSTRAINT operational_network_id_unique IF NOT EXISTS FOR (n:OperationalNetwork) REQUIRE n.groupId IS UNIQUE"
LOAD_NETWORKS = "UNWIND $rows AS row MERGE (n:OperationalNetwork {groupId: row.groupId}) SET n.split = row.split"
LOAD_MEMBERS = """
UNWIND $rows AS row
MATCH (l:Lot {bbl: row.bbl})
MATCH (n:OperationalNetwork {groupId: row.groupId})
MERGE (l)-[:IN_NETWORK]->(n)
RETURN count(*) AS linked
"""
CONSTRAINT_L = "CREATE CONSTRAINT landlord_id_unique IF NOT EXISTS FOR (a:Landlord) REQUIRE a.nodeId IS UNIQUE"
LOAD_LANDLORDS = "UNWIND $rows AS row MERGE (:Landlord {nodeId: row.nodeId})"
LOAD_COVERS = """
UNWIND $rows AS row
MATCH (a:Landlord {nodeId: row.nodeId})
MATCH (l:Lot {bbl: row.bbl})
MERGE (a)-[c:COVERS]->(l)
SET c.registrationId = row.registrationId
RETURN count(*) AS linked
"""
CLEAR_REASONS = "MATCH (l:Lot) WHERE l.networkAbsence IS NOT NULL OR l.networkAbsenceDetail IS NOT NULL REMOVE l.networkAbsence, l.networkAbsenceDetail"
LOAD_REASONS = """
UNWIND $rows AS row
MATCH (l:Lot {bbl: row.bbl})
SET l.networkAbsence = row.top, l.networkAbsenceDetail = row.detail
RETURN count(*) AS set
"""
COUNTS = """
CALL () { MATCH (n:OperationalNetwork) RETURN count(n) AS networks }
CALL () { MATCH (:Lot)-[r:IN_NETWORK]->(:OperationalNetwork) RETURN count(r) AS members }
CALL () { MATCH (l:Lot) WHERE l.networkAbsenceDetail IS NOT NULL RETURN count(l) AS reasons }
// Landlord and COVERS are shared with the Owner Portfolio layer (load_portfolios.py), so count only the network's own: those on a lot in a network
CALL () { MATCH (a:Landlord)-[:COVERS]->(:Lot)-[:IN_NETWORK]->(:OperationalNetwork) RETURN count(DISTINCT a) AS landlords }
CALL () { MATCH (:Landlord)-[c:COVERS]->(:Lot)-[:IN_NETWORK]->(:OperationalNetwork) RETURN count(c) AS covers }
RETURN networks, members, reasons, landlords, covers
"""


def batches(rows):
    batch = []
    for row in rows:
        batch.append(row)
        if len(batch) == BATCH:
            yield batch
            batch = []
    if batch:
        yield batch


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
    problems += [f"{t}.csv checksum differs from the manifest" for t in ("groups", "group_bbls", "bbl_status", "network_membership", "node_observations") if not release.verify_member(t)]
    if problems:
        print("refusing: the release is not the pinned one:\n  " + "\n  ".join(problems), file=sys.stderr)
        return 1
    print(f"release {release.source['release']} run {release.source['run_id']} verified")

    driver = GraphDatabase.driver(os.environ["NEO4J_URI"], auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]))
    try:
        driver.verify_connectivity()
    except Exception as exc:  # start the DBMS in Neo4j Desktop first
        print(f"cannot reach Neo4j ({type(exc).__name__}). Is the DBMS started in Neo4j Desktop?", file=sys.stderr)
        return 1

    started = time.time()
    networks = members = reasons_staged = reasons_set = outside = landlords = covers = 0
    with driver, driver.session(database=POC_DATABASE) as session:
        session.run(CONSTRAINT).consume()

        def network_rows():
            for r in release.rows("groups", layer=LAYER):
                if r["split"] not in ("wcc", "louvain"):
                    raise ValueError(f"unexpected split {r['split']!r} for {r['group_id']}")
                yield {"groupId": r["group_id"], "split": r["split"]}

        for batch in batches(network_rows()):
            session.execute_write(lambda tx, b=batch: tx.run(LOAD_NETWORKS, rows=b).consume())
            networks += len(batch)
        print(f"  networks loaded: {networks:,} ({time.time() - started:.0f}s)", flush=True)

        def member_rows():
            for r in release.rows("group_bbls", layer=LAYER):
                if r["rental"] != "True":
                    raise ValueError(f"non-rental lot {r['bbl']} in a network: the model stores no rental flag")
                yield {"bbl": r["bbl"], "groupId": r["group_id"]}

        for batch in batches(member_rows()):
            n = session.execute_write(lambda tx, b=batch: tx.run(LOAD_MEMBERS, rows=b).single()["linked"])
            if n != len(batch):
                print(f"error: {len(batch) - n} member lots are not Lots in the graph (load_lots.py first?)", file=sys.stderr)
                return 1
            members += n
        print(f"  memberships loaded: {members:,} ({time.time() - started:.0f}s)", flush=True)

        session.run(CLEAR_REASONS).consume()
        lots = {r["bbl"] for r in session.run("MATCH (l:Lot) RETURN l.bbl AS bbl")}

        def reason_rows():
            nonlocal outside
            for r in release.rows("bbl_status", layer=LAYER, status="not_in_group"):
                if r["top_level_reason"] not in TOP_LEVEL or r["reason_code"] not in DETAIL:
                    raise ValueError(f"unexpected reason {r['top_level_reason']!r}/{r['reason_code']!r} for {r['bbl']}")
                if r["bbl"] in lots:
                    yield {"bbl": r["bbl"], "top": r["top_level_reason"], "detail": r["reason_code"]}
                else:
                    outside += 1

        for batch in batches(reason_rows()):
            reasons_set += session.execute_write(lambda tx, b=batch: tx.run(LOAD_REASONS, rows=b).single()["set"])
            reasons_staged += len(batch)

        session.run(CONSTRAINT_L).consume()
        node_net = {r["node_id"] for r in release.rows("network_membership") if r["operational_network_id"]}
        for batch in batches({"nodeId": int(n)} for n in sorted(node_net, key=int)):
            session.execute_write(lambda tx, b=batch: tx.run(LOAD_LANDLORDS, rows=b).consume())
            landlords += len(batch)
        print(f"  landlords loaded: {landlords:,} ({time.time() - started:.0f}s)", flush=True)

        def cover_rows():
            for r in release.rows("node_observations"):
                if r["node_id"] in node_net:
                    yield {"nodeId": int(r["node_id"]), "bbl": r["bbl"], "registrationId": int(r["registration_id"])}

        for batch in batches(cover_rows()):
            n = session.execute_write(lambda tx, b=batch: tx.run(LOAD_COVERS, rows=b).single()["linked"])
            if n != len(batch):
                print(f"error: {len(batch) - n} covered lots are not Lots in the graph", file=sys.stderr)
                return 1
            covers += n
        print(f"  covers loaded: {covers:,} ({time.time() - started:.0f}s)", flush=True)

        graph = session.run(COUNTS).single()

    print(f"reasons for BBLs outside the graph (not loaded): {outside:,}")
    print(f"staged: {networks:,} networks, {members:,} memberships, {reasons_staged:,} reasons")
    print(f"graph:  {graph['networks']:,} networks, {graph['members']:,} memberships, {graph['reasons']:,} reasons")
    print(f"staged: {landlords:,} landlords, {covers:,} covers")
    print(f"graph:  {graph['landlords']:,} landlords, {graph['covers']:,} covers")
    ok = (graph["networks"] == networks and graph["members"] == members and graph["reasons"] == reasons_staged == reasons_set
          and graph["landlords"] == landlords and graph["covers"] == covers)
    print("counts reconcile" if ok else "COUNTS DO NOT RECONCILE", f"({time.time() - started:.0f}s)")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
