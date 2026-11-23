"""Check the links behind Owner Portfolios (Q9.3) and the shared Landlord layer against the pinned BOR release. Read-only everywhere.

1. Each fixture is re-derived from the release, so a stale fixture fails.
2. Each portfolio's links are looked up in the graph with tests/q9_3/lookup.cypher.
3. Over the whole layer: the graph's CONNECTED_BY_IDENTITY and CONNECTED_BY_DEED relationships equal the release's kept portfolio
   edges (less the edges with an end that is not a Landlord), including the stage, evidence and group of each; the Landlord layer is
   the union of the Operational Network and Owner Portfolio nodes, with every cover and its registration.

Any failure or error is a failure; nothing is skipped. Exit code 0 only if every check passes.
Run: uv run python tests/q9_3/check_signals.py
"""

import os
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from bor_support import check, connect, expected_relationships, finish, group_layer, load_fixtures  # noqa: E402

LAYER = "owner_portfolio"


def main() -> int:
    driver, pg, release = connect()
    pg.close()
    fixtures = load_fixtures(HERE / "fixtures.yaml")
    lookup = (HERE / "lookup.cypher").read_text()
    groups, members, group_of = group_layer(release, LAYER)

    node_group = {r["node_id"]: r["group_id"] for r in release.rows("group_members", layer=LAYER)}
    net_nodes = {r["node_id"] for r in release.rows("network_membership") if r["operational_network_id"]}
    all_nodes = set(node_group) | net_nodes
    covers, rental_nodes = {}, defaultdict(set)
    for r in release.rows("node_observations"):
        if r["node_id"] in all_nodes:
            covers[(int(r["node_id"]), r["bbl"])] = int(r["registration_id"])
        if r["node_id"] in node_group and group_of.get(r["bbl"]) == node_group[r["node_id"]]:
            rental_nodes[node_group[r["node_id"]]].add(int(r["node_id"]))
    rels = {k: v for k, v in expected_relationships(release).items() if k[0] in ("CONNECTED_BY_IDENTITY", "CONNECTED_BY_DEED")}
    landlords = {int(n) for n in all_nodes}
    loadable = {k: v for k, v in rels.items() if k[1] in landlords and k[2] in landlords}
    t = fixtures["totals"]
    check("release: portfolio landlord count matches fixture", len(node_group) == t["portfolio_landlords"], f"{len(node_group)}")
    check("release: portfolio-only landlords match fixture", len(set(node_group) - net_nodes) == t["portfolio_only_landlords"])
    no_rental = sum(1 for n in node_group if int(n) not in rental_nodes[node_group[n]])
    check("release: landlords without a rental lot match fixture", no_rental == t["landlords_without_rental_lot"], f"{no_rental}")
    check("release: union of landlords matches fixture", len(all_nodes) == t["landlords_both_layers_union"], f"{len(all_nodes)}")
    check("release: union of covers matches fixture", len(covers) == t["covers_union"], f"{len(covers)}")
    stages = Counter(v["stage"] for v in rels.values())
    check("release: edges by stage match fixture", dict(stages) == t["edges_by_stage"], f"{dict(stages)}")
    check("release: relationships by type match fixture", dict(Counter(k[0] for k in rels)) == t["relationships"])
    check("release: edges in a dropped portfolio match fixture", sum(1 for v in rels.values() if v["portfolioGroupId"] is None) == t["edges_without_portfolio"])
    check("release: edges skipped because an end is not a Landlord match fixture", len(rels) - len(loadable) == t["edges_skipped_not_landlord"], f"{len(rels) - len(loadable)}")
    check("release: every edge in a portfolio joins two members of that portfolio",
          all(node_group.get(str(k[1])) == v["portfolioGroupId"] and node_group.get(str(k[2])) == v["portfolioGroupId"]
              for k, v in rels.items() if v["portfolioGroupId"] is not None))
    # the kept edges of a portfolio connect its landlords: one component per portfolio
    parent = {n: n for n in node_group}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for k, v in rels.items():
        if v["portfolioGroupId"] is not None:
            parent[find(str(k[1]))] = find(str(k[2]))
    roots = defaultdict(set)
    for n, g in node_group.items():
        roots[g].add(find(n))
    check("release: the edges of each portfolio connect all its landlords", all(len(v) == 1 for v in roots.values()))

    def edges_of(gid):
        return sorted((k[0], k[1], k[2], v["stage"], k[3].split("|")[0]) for k, v in rels.items()
                      if v["portfolioGroupId"] == gid and (k[1] in rental_nodes[gid] or k[2] in rental_nodes[gid]))

    with driver, driver.session(database=os.environ["NEO4J_DATABASE"], default_access_mode="READ") as session:
        for f in fixtures["portfolios"]:
            gid = f["groupId"]
            want = sorted(tuple(x) for x in f["links"])
            check(f"{gid} fixture matches the release's edges", edges_of(gid) == want, f"release says {edges_of(gid)}")
            got = sorted((r["type"], r["nodeA"], r["nodeB"], r["stage"], r["evidenceId"]) for r in session.run(lookup, groupId=gid))
            check(f"{gid} graph matches fixture", got == want, f"graph has {got}")

        g_rels = {}
        for r in session.run("MATCH (x:Landlord)-[k:CONNECTED_BY_IDENTITY|CONNECTED_BY_DEED]->(y:Landlord) "
                             "RETURN type(k) AS type, x.nodeId AS a, y.nodeId AS b, k.evidenceId AS ev, k.stage AS stage, k.evidenceType AS et, "
                             "k.portfolioEdgeId AS pe, k.portfolioGroupId AS pg, k.networkEdgeId AS ne, k.networkGroupId AS ng, k.weight AS w"):
            key = (r["type"], r["a"], r["b"], r["ev"] + ("|" + r["stage"] if r["type"] == "CONNECTED_BY_DEED" else ""))
            g_rels[key] = {"stage": r["stage"], "evidenceType": r["et"], "portfolioEdgeId": r["pe"], "portfolioGroupId": r["pg"],
                           **({"networkEdgeId": r["ne"], "networkGroupId": r["ng"], "weight": r["w"]} if r["type"] == "CONNECTED_BY_IDENTITY" else {})}
        check("graph: every relationship matches the release field by field",
              g_rels.keys() == loadable.keys() and all(g_rels[k] == loadable[k] for k in loadable), f"{len(g_rels)} in graph vs {len(loadable)}")
        g_nodes = session.run("MATCH (a:Landlord) RETURN count(a) AS n").single()["n"]
        check("graph: the Landlord layer is the union of both layers' landlord records", g_nodes == len(all_nodes), f"{g_nodes} vs {len(all_nodes)}")
        g_cov = {(r["n"], r["b"]): r["reg"] for r in session.run(
            "MATCH (a:Landlord)-[c:COVERS]->(l:Lot) RETURN a.nodeId AS n, l.bbl AS b, c.registrationId AS reg")}
        check("graph: every cover and its registration matches the release", g_cov == covers, f"{len(g_cov)} vs {len(covers)}")
    return finish()


if __name__ == "__main__":
    sys.exit(main())
