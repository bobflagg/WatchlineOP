"""Check what each landlord record is called, its business addresses and the anchor of each group (Q8.3, Q8.1, Q9.1) against the pinned
release. Read-only on the graph and the release.

1. The release itself: every group member has a name; the anchor of each group is a member with the most lots, ties to the smallest
   node id; the fixtures below equal the release.
2. The graph, over all 31035 landlords: name equals node_names.name; businessAddresses equals the sorted distinct addresses of the
   selected observations (absent when there are none); every group has the one anchor the release names.

Any failure or error is a failure; nothing is skipped. Exit code 0 only if every check passes.
Run: uv run python tests/q8_3/check_labels.py
"""

import os
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from bor_support import check, connect, finish, load_fixtures  # noqa: E402

ADDRESS_PARTS = ("business_house", "business_street", "business_apartment", "business_city", "business_state", "business_zip")


def address(c: dict) -> str | None:
    street = " ".join(p.strip() for p in (c["business_house"], c["business_street"], c["business_apartment"]) if p and p.strip())
    state_zip = " ".join(p.strip() for p in (c["business_state"], c["business_zip"]) if p and p.strip())
    parts = [p for p in (street, (c["business_city"] or "").strip(), state_zip) if p]
    return ", ".join(parts) or None


def main() -> int:
    driver, pg, release = connect()
    fx = load_fixtures(HERE / "fixtures_labels.yaml")
    members = {int(r["node_id"]) for r in release.rows("group_members")}
    names = {int(r["node_id"]): r["name"] for r in release.rows("node_names")}
    contacts = {r["observation_id"]: r for r in release.rows("observation_contacts")}
    lots = defaultdict(set)
    addresses = defaultdict(set)
    for r in release.rows("node_observations"):
        n = int(r["node_id"])
        lots[n].add(r["bbl"])
        c = contacts.get(r["selected_observation_id"])
        if n in members and c and (a := address(c)):
            addresses[n].add(a)
    groups = {(g["layer"], g["group_id"]): int(g["anchor_node_id"]) for g in release.rows("groups")}
    group_nodes = defaultdict(set)
    for r in release.rows("group_members"):
        group_nodes[(r["layer"], r["group_id"])].add(int(r["node_id"]))

    check("release: every group member has a non-blank name", all(names.get(n) for n in members))
    check("release: every anchor is a member of its group", all(a in group_nodes[k] for k, a in groups.items()))
    check("release: every anchor has the most lots in its group, ties to the smallest node id",
          all(a == min(group_nodes[k], key=lambda n: (-len(lots[n]), n)) for k, a in groups.items()))
    t = fx["totals"]
    check("release: landlords, with address, and anchors match the fixture",
          (len(members), sum(1 for n in members if addresses[n]), Counter(k[0] for k in groups)) ==
          (t["landlords"], t["with_address"], Counter(t["anchors"])), f"{len(members)}")
    for f in fx["landlords"]:
        n = f["nodeId"]
        check(f"fixture node {n} matches the release", names[n] == f["name"] and sorted(addresses[n]) == f["businessAddresses"])
    for f in fx["anchors"]:
        check(f"fixture {f['groupId']} anchor matches the release", groups[(f["layer"], f["groupId"])] == f["anchor"] and names[f["anchor"]] == f["name"])

    with driver, driver.session(database=os.environ["NEO4J_DATABASE"], default_access_mode="READ") as s:
        g = {r["n"]: (r["name"], r["addr"]) for r in s.run("MATCH (a:Landlord) RETURN a.nodeId AS n, a.name AS name, a.businessAddresses AS addr")}
        check("graph: every landlord's name equals node_names", {n: v[0] for n, v in g.items()} == {n: names[n] for n in members}, f"{len(g)} in graph")
        check("graph: every landlord's businessAddresses equal the sorted distinct addresses of its selected observations (absent when none)",
              {n: v[1] for n, v in g.items()} == {n: (sorted(addresses[n]) if addresses[n] else None) for n in members})
        ga = {(r["layer"], r["gid"]): r["anchor"] for r in s.run(
            "MATCH (g)-[:ANCHORED_BY]->(a:Landlord) WHERE g:OperationalNetwork OR g:OwnerPortfolio "
            "RETURN CASE WHEN g:OperationalNetwork THEN 'operational_network' ELSE 'owner_portfolio' END AS layer, g.groupId AS gid, a.nodeId AS anchor")}
        check("graph: every group is anchored by the landlord the release names", ga == groups, f"{len(ga)} in graph vs {len(groups)}")
        for f in fx["anchors"]:
            rec = s.run(open(HERE.parent / ("q8_1" if f["layer"] == "operational_network" else "q9_1") / "lookup_anchor.cypher").read(), groupId=f["groupId"]).single()
            check(f"graph: lookup of {f['groupId']} gives anchor {f['anchor']} {f['name']}", rec and rec["nodeId"] == f["anchor"] and rec["name"] == f["name"], f"graph has {dict(rec) if rec else None}")
    pg.close()
    return finish()


if __name__ == "__main__":
    sys.exit(main())
