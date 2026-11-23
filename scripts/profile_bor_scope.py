"""Compare the BOR release's Operational Network layer with the Lots in the POC graph (read-only).

Prints how many network members and absence rows have a Lot in the graph. Uses NEO4J_* from .env and
BOR_RELEASE_DIR (default ~/Learning/Sabbatical/beneficial-ownership-resolution/release/v0.2.1). Superseded: the pinned release is v0.3.0 (data/sources.yaml); this one-off profile reads v0.2.1 files.
"""
import collections
import csv
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from neo4j import GraphDatabase

ROOT = Path(__file__).resolve().parent.parent
LAYER = "operational_network"


def main() -> int:
    load_dotenv(ROOT / ".env")
    if os.environ.get("NEO4J_DATABASE") != "watchline":
        print("refusing: NEO4J_DATABASE is not 'watchline'", file=sys.stderr)
        return 1
    release = Path(os.environ.get("BOR_RELEASE_DIR", "~/Learning/Sabbatical/beneficial-ownership-resolution/release/v0.2.1")).expanduser()
    driver = GraphDatabase.driver(os.environ["NEO4J_URI"], auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]))
    with driver, driver.session(database="watchline") as s:
        lots = {r["bbl"] for r in s.run("MATCH (l:Lot) RETURN l.bbl AS bbl")}
    print(f"Lots in the graph: {len(lots):,}")

    members = collections.defaultdict(list)
    for r in csv.DictReader(open(release / "group_bbls.csv")):
        if r["layer"] == LAYER:
            members[r["group_id"]].append(r["bbl"])
    in_graph = sum(b in lots for bs in members.values() for b in bs)
    total = sum(len(bs) for bs in members.values())
    print(f"Network member lots: {total:,}; in the graph: {in_graph:,}; not in the graph: {total - in_graph:,}")
    parts = collections.Counter("all in graph" if all(b in lots for b in bs) else
                                "none in graph" if not any(b in lots for b in bs) else "partly in graph"
                                for bs in members.values())
    print(f"Networks ({len(members):,}): {dict(parts)}")

    reasons, outside = collections.Counter(), 0
    with open(release / "bbl_status.csv") as f:
        for r in csv.DictReader(f):
            if r["layer"] != LAYER or r["status"] == "in_group":
                continue
            if r["bbl"] in lots:
                reasons[(r["top_level_reason"], r["reason_code"])] += 1
            else:
                outside += 1
    print(f"Absence rows for lots in the graph: {sum(reasons.values()):,}; for lots not in the graph: {outside:,}")
    for k, v in reasons.most_common():
        print(f"  {v:>8,}  {k[0]} / {k[1]}")
    with_status = sum(reasons.values()) + in_graph
    print(f"Graph lots with no status row at all: {len(lots) - with_status:,}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
