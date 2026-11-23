"""Shared helpers for tests/q8_*: expected answers derived from the pinned BOR release, and graph access.

Read-only on the release, the source database and the graph. The derivations here read the release files
directly and are independent of scripts/load_networks.py.
"""

import os
import sys
from pathlib import Path

import psycopg
import yaml
from dotenv import load_dotenv
from neo4j import GraphDatabase

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from watchline.bor_release import BorRelease  # noqa: E402

REQUIRED_ENV = ("JUSTFIX_DATABASE_URL", "NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD", "NEO4J_DATABASE")
LAYER = "operational_network"
results: list[bool] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  ({detail})" if detail and not ok else ""))


def finish() -> int:
    failed = results.count(False)
    print(f"{len(results) - failed}/{len(results)} checks passed")
    return 0 if failed == 0 else 1


def connect():
    """Return (neo4j driver, pg connection, release); exit 1 when .env is incomplete or the release is not the pinned one."""
    load_dotenv(ROOT / ".env")
    missing = [k for k in REQUIRED_ENV if not os.environ.get(k)]
    if missing:
        print(f"missing in .env: {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)
    release = BorRelease()
    problems = release.verify_identity()
    check("release zip matches the sha256 in data/sources.yaml", release.verify_zip())
    check("release manifest matches run, snapshot and schema in data/sources.yaml", not problems, "; ".join(problems))
    driver = GraphDatabase.driver(os.environ["NEO4J_URI"], auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]))
    pg = psycopg.connect(os.environ["JUSTFIX_DATABASE_URL"])
    pg.read_only = True
    return driver, pg, release


def load_fixtures(path: Path) -> dict:
    return yaml.safe_load(path.read_text())


def network_layer(release: BorRelease) -> tuple[dict, dict, dict]:
    """Operational Network groups from the release: (split by group id, member BBLs by group id, group id by BBL)."""
    split = {r["group_id"]: r["split"] for r in release.rows("groups", layer=LAYER)}
    members: dict[str, list[str]] = {}
    group_of: dict[str, str] = {}
    for r in release.rows("group_bbls", layer=LAYER):
        members.setdefault(r["group_id"], []).append(r["bbl"])
        group_of[r["bbl"]] = r["group_id"]
    return split, members, group_of


def group_layer(release: BorRelease, layer: str) -> tuple[dict, dict, dict]:
    """One layer's groups from the release: (group rows by id, rental member BBLs by group id, group id by rental BBL)."""
    groups = {r["group_id"]: r for r in release.rows("groups", layer=layer)}
    members: dict[str, list[str]] = {}
    group_of: dict[str, str] = {}
    for r in release.rows("group_bbls", layer=layer):
        if r["rental"] == "True":
            members.setdefault(r["group_id"], []).append(r["bbl"])
            group_of[r["bbl"]] = r["group_id"]
    return groups, members, group_of


def status_rows(release: BorRelease, bbls: set[str] | None = None, layer: str = LAYER):
    """bbl_status rows of one layer (default Operational Network), optionally only for the given BBLs."""
    for r in release.rows("bbl_status", layer=layer):
        if bbls is None or r["bbl"] in bbls:
            yield r


def expected_relationships(release) -> dict:
    """The relationships the graph must hold between landlords, derived from the release alone (independent of the loader):
    {(type, node_a, node_b, evidence_id or ""): properties}. Built from the kept rows of graph_edges.csv.

    CONNECTED_BY_NAME and CONNECTED_BY_ADDRESS: a network.name or network.address row. CONNECTED_BY_DEED: a deed.* portfolio row (keyed by evidence id and stage: one deed can join a pair at both stages).
    CONNECTED_BY_IDENTITY: an identity.* portfolio row, joined with the network.identity row of the same pair and evidence."""
    out: dict = {}
    network_identity = {}
    for e in release.rows("graph_edges", kept="True"):
        a, b = int(e["node_a"]), int(e["node_b"])
        gid = e["group_id"] or None
        if e["layer"] == "operational_network":
            if e["stage"] == "network.identity":
                network_identity[(a, b, e["evidence_id"])] = e
            else:
                t = {"network.name": "CONNECTED_BY_NAME", "network.address": "CONNECTED_BY_ADDRESS"}[e["stage"]]
                out[(t, a, b, "")] = {"weight": float(e["weight"]), "networkEdgeId": e["edge_id"], "networkGroupId": gid}
        else:
            t = "CONNECTED_BY_DEED" if e["stage"].startswith("deed.") else "CONNECTED_BY_IDENTITY"
            props = {"stage": e["stage"], "evidenceType": e["evidence_type"], "portfolioEdgeId": e["edge_id"], "portfolioGroupId": gid}
            if t == "CONNECTED_BY_IDENTITY":
                props.update(networkEdgeId=None, networkGroupId=None, weight=None)
            out[(t, a, b, e["evidence_id"] + ("|" + e["stage"] if t == "CONNECTED_BY_DEED" else ""))] = props
    for (a, b, ev), e in network_identity.items():
        p = out[("CONNECTED_BY_IDENTITY", a, b, ev)]       # KeyError: a network identity edge no portfolio row explains
        p.update(networkEdgeId=e["edge_id"], networkGroupId=e["group_id"] or None, weight=float(e["weight"]))
    return out
