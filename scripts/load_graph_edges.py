"""Load the edges between landlords from the pinned BOR release (Q8.3, Q9.3; release v0.3.0 graph_edges.csv).

Run after scripts/load_networks.py and load_portfolios.py (they load the Landlord nodes) and load_service_addresses.py.
Reads the release with src/watchline/bor_release.py and refuses to load unless the zip checksum, the manifest identity and the
checksum of graph_edges.csv match data/sources.yaml. Four relationship types, each from node_a to node_b (node_a < node_b),
one per row of graph_edges.csv with kept = True (see profiles/bor_layers.yaml):
  - (Landlord)-[:CONNECTED_BY_IDENTITY {stage, evidenceType, evidenceId, portfolioEdgeId, portfolioGroupId, networkEdgeId,
    networkGroupId, weight}]->(Landlord). The same evidence feeds both layers, so one relationship carries both layers' ids: the
    Owner Portfolio row sets stage and portfolioEdgeId; the Operational Network row of the same pair and evidence sets
    networkEdgeId and weight (100). A network identity row with no portfolio row is an error. A registered-LLC pair that several
    entities share has one relationship per set; the network row cites the first set only.
  - (Landlord)-[:CONNECTED_BY_DEED {stage, evidenceType, evidenceId, portfolioEdgeId, portfolioGroupId}]->(Landlord): portfolio only. One
    deed can join the same pair at both stages (held since, linked successor), so the pair, evidence and stage are the identity.
  - (Landlord)-[:CONNECTED_BY_NAME {weight, networkEdgeId, networkGroupId}]->(Landlord) and
    (Landlord)-[:CONNECTED_BY_ADDRESS {weight, networkEdgeId, networkGroupId}]->(Landlord): network only.
  A group id is blank (absent) when the edge crosses a network boundary, or falls in a portfolio BOR dropped as co-op or condo dominated.
Edges set aside (kept = False) are not loaded as relationships: 82 percent of the masked address edges join landlords that are in no
network and no portfolio. Their count per masked address is a property of NetworkMaskedAddress (scripts/load_service_addresses.py).
An edge with an end that is not a Landlord is counted and skipped, never created.

Safe to rerun: relationships are MERGEd on their identity; their properties are set again.
Reads the release read-only and writes only to the POC database.
Run: uv run python scripts/load_graph_edges.py
"""

import os
import sys
import time
from collections import Counter
from pathlib import Path

from dotenv import load_dotenv
from neo4j import GraphDatabase

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from watchline.bor_release import BorRelease  # noqa: E402

POC_DATABASE = "watchline"
BATCH = 5000
REQUIRED_ENV = ("NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD", "NEO4J_DATABASE")
IDENTITY = {"identity.splink_base", "identity.splink_feedback", "identity.curated", "identity.registered_llc"}
DEED = {"deed.held_since", "deed.linked_successor"}
EVIDENCE = {"identity_cluster", "link_set", "evidence_item"}

LOAD_IDENTITY = """
UNWIND $rows AS row
MATCH (a:Landlord {nodeId: row.nodeA})
MATCH (b:Landlord {nodeId: row.nodeB})
MERGE (a)-[k:CONNECTED_BY_IDENTITY {evidenceId: row.evidenceId}]->(b)
SET k.stage = row.stage, k.evidenceType = row.evidenceType, k.portfolioEdgeId = row.portfolioEdgeId,
    k.portfolioGroupId = row.portfolioGroupId, k.networkEdgeId = row.networkEdgeId, k.networkGroupId = row.networkGroupId,
    k.weight = row.weight
RETURN count(*) AS linked
"""
LOAD_DEED = """
UNWIND $rows AS row
MATCH (a:Landlord {nodeId: row.nodeA})
MATCH (b:Landlord {nodeId: row.nodeB})
MERGE (a)-[k:CONNECTED_BY_DEED {evidenceId: row.evidenceId, stage: row.stage}]->(b)
SET k.evidenceType = row.evidenceType, k.portfolioEdgeId = row.portfolioEdgeId,
    k.portfolioGroupId = row.portfolioGroupId
RETURN count(*) AS linked
"""
LOAD_NAME_ADDRESS = """
UNWIND $rows AS row
MATCH (a:Landlord {nodeId: row.nodeA})
MATCH (b:Landlord {nodeId: row.nodeB})
MERGE (a)-[k:%s]->(b)
SET k.weight = row.weight, k.networkEdgeId = row.networkEdgeId, k.networkGroupId = row.networkGroupId
RETURN count(*) AS linked
"""
COUNTS = """
CALL () { MATCH (:Landlord)-[k:CONNECTED_BY_IDENTITY]->(:Landlord) RETURN count(k) AS identity }
CALL () { MATCH (:Landlord)-[k:CONNECTED_BY_DEED]->(:Landlord) RETURN count(k) AS deed }
CALL () { MATCH (:Landlord)-[k:CONNECTED_BY_NAME]->(:Landlord) RETURN count(k) AS name }
CALL () { MATCH (:Landlord)-[k:CONNECTED_BY_ADDRESS]->(:Landlord) RETURN count(k) AS address }
RETURN identity, deed, name, address
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


def edge_rows(release):
    """Group the kept rows of graph_edges.csv into the relationships to load. Returns (identity, deed, name, address, skipped_ids)."""
    kept = [r for r in release.rows("graph_edges") if r["kept"] == "True"]
    portfolio, network = [r for r in kept if r["layer"] == "owner_portfolio"], [r for r in kept if r["layer"] == "operational_network"]
    identity, deed, name, address = {}, [], [], []
    for r in portfolio:
        base = {"nodeA": int(r["node_a"]), "nodeB": int(r["node_b"]), "stage": r["stage"], "evidenceType": r["evidence_type"],
                "evidenceId": r["evidence_id"], "portfolioEdgeId": r["edge_id"], "portfolioGroupId": r["group_id"] or None}
        if r["evidence_type"] not in EVIDENCE or not r["evidence_id"]:
            raise ValueError(f"portfolio edge {r['edge_id']} has no evidence")
        if r["stage"] in IDENTITY:
            key = (base["nodeA"], base["nodeB"], r["evidence_id"])
            if key in identity:
                raise ValueError(f"portfolio identity edge {key} appears twice")
            identity[key] = dict(base, networkEdgeId=None, networkGroupId=None, weight=None)
        elif r["stage"] in DEED:
            deed.append(base)
        else:
            raise ValueError(f"unexpected portfolio stage {r['stage']!r} for {r['edge_id']}")
    for r in network:
        a, b = int(r["node_a"]), int(r["node_b"])
        if r["stage"] == "network.identity":
            e = identity.get((a, b, r["evidence_id"]))
            if e is None:
                raise ValueError(f"network identity edge {r['edge_id']} {(a, b, r['evidence_id'])} has no portfolio row")
            e.update(networkEdgeId=r["edge_id"], networkGroupId=r["group_id"] or None, weight=float(r["weight"]))
        elif r["stage"] in ("network.name", "network.address"):
            row = {"nodeA": a, "nodeB": b, "weight": float(r["weight"]), "networkEdgeId": r["edge_id"], "networkGroupId": r["group_id"] or None}
            (name if r["stage"] == "network.name" else address).append(row)
        else:
            raise ValueError(f"unexpected network stage {r['stage']!r} for {r['edge_id']}")
    return list(identity.values()), deed, name, address


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
    if not release.verify_member("graph_edges"):
        problems.append("graph_edges.csv checksum differs from the manifest")
    if problems:
        print("refusing: the release is not the pinned one:\n  " + "\n  ".join(problems), file=sys.stderr)
        return 1
    print(f"release {release.source['release']} run {release.source['run_id']} verified")

    identity, deed, name, address = edge_rows(release)
    print(f"  staged from the release: {len(identity):,} identity, {len(deed):,} deed, {len(name):,} name, {len(address):,} address", flush=True)

    driver = GraphDatabase.driver(os.environ["NEO4J_URI"], auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]))
    try:
        driver.verify_connectivity()
    except Exception as exc:  # start the DBMS in Neo4j Desktop first
        print(f"cannot reach Neo4j ({type(exc).__name__}). Is the DBMS started in Neo4j Desktop?", file=sys.stderr)
        return 1

    started = time.time()
    loaded, skipped = Counter(), Counter()
    with driver, driver.session(database=POC_DATABASE) as session:
        landlords = {r["n"] for r in session.run("MATCH (a:Landlord) RETURN a.nodeId AS n")}
        for kind, query, rows in (("identity", LOAD_IDENTITY, identity), ("deed", LOAD_DEED, deed),
                                  ("name", LOAD_NAME_ADDRESS % "CONNECTED_BY_NAME", name),
                                  ("address", LOAD_NAME_ADDRESS % "CONNECTED_BY_ADDRESS", address)):
            usable = [r for r in rows if r["nodeA"] in landlords and r["nodeB"] in landlords]
            skipped[kind] = len(rows) - len(usable)
            for batch in batches(usable):
                n = session.execute_write(lambda tx, b=batch, q=query: tx.run(q, rows=b).single()["linked"])
                if n != len(batch):
                    print(f"error: {len(batch) - n} {kind} edges join landlords that were not loaded", file=sys.stderr)
                    return 1
                loaded[kind] += n
            print(f"  {kind} edges loaded: {loaded[kind]:,}, skipped (an end is not a Landlord): {skipped[kind]:,} ({time.time() - started:.0f}s)", flush=True)
        graph = session.run(COUNTS).single()

    print(f"staged: {dict(loaded)}; skipped: {dict(skipped)}")
    print(f"graph:  identity {graph['identity']:,}, deed {graph['deed']:,}, name {graph['name']:,}, address {graph['address']:,}")
    ok = all(graph[k] == loaded[k] for k in ("identity", "deed", "name", "address"))
    print("counts reconcile" if ok else "COUNTS DO NOT RECONCILE", f"({time.time() - started:.0f}s)")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
