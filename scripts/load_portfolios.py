"""Load Owner Portfolios from the pinned BOR release (Q9.1 to Q9.5).

Run after scripts/load_lots.py, load_buildings.py and load_networks.py. Reads the release with src/watchline/bor_release.py and
refuses to load unless the zip checksum, the manifest identity and the checksum of each file read all match data/sources.yaml.
Rules (see tests/q9_1 to q9_5 and profiles/bor_layers.yaml):
  - OwnerPortfolio per Owner Portfolio row of groups.csv, with groupId (OP-<n>, run-local) and composition
    (identity, deed_only or deed_bridged, as BOR spells them).
  - (Lot)-[:IN_PORTFOLIO]->(OwnerPortfolio) per rental row of group_bbls.csv (43318). Every member lot must already be a Lot:
    a missing Lot is an error, never created here. Co-op and condo lots outside the footprint (rental false) get no relationship.
  - Landlord for each node of group_members.csv (MERGE: 15512 already exist from load_networks.py; 111 are new) and
    (Landlord)-[:COVERS {registrationId}]->(Lot) for each node_observations row of those nodes. The graph's Landlord layer is the
    union of the two layers' nodes.
  - Edges between landlords are loaded by scripts/load_graph_edges.py (release v0.3.0 publishes every edge in graph_edges.csv).
  - Lot.portfolioAbsence (top-level reason) and Lot.portfolioAbsenceDetail (BOR's code) for each not_in_group or
    excluded_from_footprint row of bbl_status.csv whose BBL is a Lot. Rows for BBLs outside the graph are counted, not loaded.

Safe to rerun: everything is MERGEd and the two reason properties are cleared and set again.
Reads the release read-only and writes only to the POC database.
Run: uv run python scripts/load_portfolios.py
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
LAYER = "owner_portfolio"
REQUIRED_ENV = ("NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD", "NEO4J_DATABASE")
TABLES = ("groups", "group_bbls", "bbl_status", "group_members", "node_observations")
COMPOSITIONS = {"identity", "deed_only", "deed_bridged"}
TOP_LEVEL = {"no_qualifying_linkage", "excluded_by_policy", "below_eligibility_rule", "outside_source_coverage", "outside_method_input"}
DETAIL = {"no_linkage", "no_registration", "no_owner_contact", "unmatched_node", "address_evidence_masked", "coop_condo_excluded",
          "coop_condo_dominated", "institutional_screen", "first_name_veto", "common_name_veto", "shared_company_degree_unknown",
          "shared_company_name_not_rare", "shared_company_first_name_conflict", "shared_company_degree_cap", "deed_not_latest",
          "deed_parcels_out_of_range", "successor_not_shell", "successor_transfer_not_nominal"}

CONSTRAINT = "CREATE CONSTRAINT owner_portfolio_id_unique IF NOT EXISTS FOR (p:OwnerPortfolio) REQUIRE p.groupId IS UNIQUE"
LOAD_PORTFOLIOS = "UNWIND $rows AS row MERGE (p:OwnerPortfolio {groupId: row.groupId}) SET p.composition = row.composition"
LOAD_MEMBERS = """
UNWIND $rows AS row
MATCH (l:Lot {bbl: row.bbl})
MATCH (p:OwnerPortfolio {groupId: row.groupId})
MERGE (l)-[:IN_PORTFOLIO]->(p)
RETURN count(*) AS linked
"""
LOAD_LANDLORDS = "UNWIND $rows AS row MERGE (:Landlord {nodeId: row.nodeId})"
LOAD_COVERS = """
UNWIND $rows AS row
MATCH (a:Landlord {nodeId: row.nodeId})
MATCH (l:Lot {bbl: row.bbl})
MERGE (a)-[c:COVERS]->(l)
SET c.registrationId = row.registrationId
RETURN count(*) AS linked
"""
CLEAR_REASONS = ("MATCH (l:Lot) WHERE l.portfolioAbsence IS NOT NULL OR l.portfolioAbsenceDetail IS NOT NULL "
                 "REMOVE l.portfolioAbsence, l.portfolioAbsenceDetail")
LOAD_REASONS = """
UNWIND $rows AS row
MATCH (l:Lot {bbl: row.bbl})
SET l.portfolioAbsence = row.top, l.portfolioAbsenceDetail = row.detail
RETURN count(*) AS set
"""
COUNTS = """
CALL () { MATCH (p:OwnerPortfolio) RETURN count(p) AS portfolios }
CALL () { MATCH (:Lot)-[r:IN_PORTFOLIO]->(:OwnerPortfolio) RETURN count(r) AS members }
CALL () { MATCH (a:Landlord) RETURN count(a) AS landlords }
CALL () { MATCH (:Landlord)-[c:COVERS]->(:Lot) RETURN count(c) AS covers }
CALL () { MATCH (l:Lot) WHERE l.portfolioAbsenceDetail IS NOT NULL RETURN count(l) AS reasons }
RETURN portfolios, members, landlords, covers, reasons
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
    problems += [f"{t}.csv checksum differs from the manifest" for t in TABLES if not release.verify_member(t)]
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
    portfolios = members = landlords = covers = reasons_staged = reasons_set = outside = 0
    with driver, driver.session(database=POC_DATABASE) as session:
        session.run(CONSTRAINT).consume()

        def portfolio_rows():
            for r in release.rows("groups", layer=LAYER):
                if r["composition"] not in COMPOSITIONS:
                    raise ValueError(f"unexpected composition {r['composition']!r} for {r['group_id']}")
                yield {"groupId": r["group_id"], "composition": r["composition"]}

        for batch in batches(portfolio_rows()):
            session.execute_write(lambda tx, b=batch: tx.run(LOAD_PORTFOLIOS, rows=b).consume())
            portfolios += len(batch)
        print(f"  portfolios loaded: {portfolios:,} ({time.time() - started:.0f}s)", flush=True)

        def member_rows():
            for r in release.rows("group_bbls", layer=LAYER):
                if r["rental"] == "True":
                    yield {"bbl": r["bbl"], "groupId": r["group_id"]}
                elif r["rental"] != "False":
                    raise ValueError(f"unexpected rental flag {r['rental']!r} for {r['bbl']}")

        for batch in batches(member_rows()):
            n = session.execute_write(lambda tx, b=batch: tx.run(LOAD_MEMBERS, rows=b).single()["linked"])
            if n != len(batch):
                print(f"error: {len(batch) - n} member lots are not Lots in the graph (load_lots.py first?)", file=sys.stderr)
                return 1
            members += n
        print(f"  memberships loaded: {members:,} ({time.time() - started:.0f}s)", flush=True)

        nodes = {r["node_id"] for r in release.rows("group_members", layer=LAYER)}
        for batch in batches({"nodeId": int(n)} for n in sorted(nodes, key=int)):
            session.execute_write(lambda tx, b=batch: tx.run(LOAD_LANDLORDS, rows=b).consume())
            landlords += len(batch)
        print(f"  landlords of portfolios merged: {landlords:,} ({time.time() - started:.0f}s)", flush=True)

        def cover_rows():
            for r in release.rows("node_observations"):
                if r["node_id"] in nodes:
                    yield {"nodeId": int(r["node_id"]), "bbl": r["bbl"], "registrationId": int(r["registration_id"])}

        for batch in batches(cover_rows()):
            n = session.execute_write(lambda tx, b=batch: tx.run(LOAD_COVERS, rows=b).single()["linked"])
            if n != len(batch):
                print(f"error: {len(batch) - n} covered lots are not Lots in the graph", file=sys.stderr)
                return 1
            covers += n
        print(f"  covers merged: {covers:,} ({time.time() - started:.0f}s)", flush=True)

        session.run(CLEAR_REASONS).consume()
        lots = {r["bbl"] for r in session.run("MATCH (l:Lot) RETURN l.bbl AS bbl")}

        def reason_rows():
            nonlocal outside
            for r in release.rows("bbl_status", layer=LAYER):
                if r["status"] == "in_group":
                    continue
                if r["status"] not in ("not_in_group", "excluded_from_footprint"):
                    raise ValueError(f"unexpected status {r['status']!r} for {r['bbl']}")
                if r["top_level_reason"] not in TOP_LEVEL or r["reason_code"] not in DETAIL:
                    raise ValueError(f"unexpected reason {r['top_level_reason']!r}/{r['reason_code']!r} for {r['bbl']}")
                if r["bbl"] in lots:
                    yield {"bbl": r["bbl"], "top": r["top_level_reason"], "detail": r["reason_code"]}
                else:
                    outside += 1

        for batch in batches(reason_rows()):
            reasons_set += session.execute_write(lambda tx, b=batch: tx.run(LOAD_REASONS, rows=b).single()["set"])
            reasons_staged += len(batch)
        graph = session.run(COUNTS).single()

    print(f"reasons for BBLs outside the graph (not loaded): {outside:,}")
    print(f"staged: {portfolios:,} portfolios, {members:,} memberships, {reasons_staged:,} reasons")
    print(f"graph:  {graph['portfolios']:,} portfolios, {graph['members']:,} memberships, "
          f"{graph['reasons']:,} reasons; {graph['landlords']:,} landlords, {graph['covers']:,} covers (both layers)")
    ok = (graph["portfolios"] == portfolios and graph["members"] == members
          and graph["reasons"] == reasons_staged == reasons_set)
    print("counts reconcile" if ok else "COUNTS DO NOT RECONCILE", f"({time.time() - started:.0f}s)")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
