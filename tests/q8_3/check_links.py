"""Check the landlords and links of Operational Networks (Q8.3) against the pinned release and the frozen source. Read-only everywhere.

1. Each fixture is re-derived from the release, and every covered lot's registration is looked up in hpd_registrations.
2. Each network is looked up in the graph with tests/q8_3/lookup*.cypher.
3. Over the whole Operational Network layer (landlords that cover network lots, those covers, and every relationship the network used):
   the graph equals the release, field by field; the pairs equal the release's network_edges, and the kinds of each pair sum to that
   row's name, address and identity weights; networkGroupId is absent exactly when the two landlords sit in different networks.

Any failure or error is a failure; nothing is skipped. Exit code 0 only if every check passes.
Run: uv run python tests/q8_3/check_links.py
"""

import os
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from bor_support import check, connect, expected_relationships, finish, load_fixtures, network_layer  # noqa: E402

NETWORK_TYPES = ("CONNECTED_BY_NAME", "CONNECTED_BY_ADDRESS", "CONNECTED_BY_IDENTITY")


def same(a: dict, b: dict) -> bool:
    return a.keys() == b.keys() and all(abs(a[k] - b[k]) < 1e-9 if isinstance(a[k], float) else a[k] == b[k] for k in a)


def link_row(key, props, node_net=None):
    t, a, b, ev = key
    return {"type": t, "nodeA": a, "nodeB": b, "weight": props["weight"], "stage": props.get("stage"), "evidenceId": ev or None,
            "networkGroupId": props["networkGroupId"]}


def main() -> int:
    driver, pg, release = connect()
    fixtures = load_fixtures(HERE / "fixtures.yaml")
    lookup_links = (HERE / "lookup.cypher").read_text()
    lookup_landlords = (HERE / "lookup_landlords.cypher").read_text()
    _, members, group_of = network_layer(release)

    node_net = {r["node_id"]: r["operational_network_id"] for r in release.rows("network_membership") if r["operational_network_id"]}
    covers = {}   # (nodeId, bbl) -> registrationId
    for r in release.rows("node_observations"):
        if r["node_id"] in node_net:
            covers[(int(r["node_id"]), r["bbl"])] = int(r["registration_id"])
    rels = {k: v for k, v in expected_relationships(release).items() if v.get("networkEdgeId")}
    edges = [link_row(k, v) for k, v in rels.items()]
    pairs = {(a, b) for _, a, b, _ in rels}
    crossing = {(a, b) for (_, a, b, _), v in rels.items() if node_net[str(a)] != node_net[str(b)]}
    check("release: every covered lot is a network member of the landlord's network",
          all(group_of.get(b) == node_net[str(n)] for (n, b) in covers))
    check("release: every lot is covered by exactly one landlord", len({b for _, b in covers}) == len(covers) == len(group_of))
    check("release: networkGroupId is absent exactly when the landlords sit in different networks",
          all((node_net[str(e["nodeA"])] == node_net[str(e["nodeB"])]) == (e["networkGroupId"] == node_net[str(e["nodeA"])])
              and (e["networkGroupId"] is None) == (node_net[str(e["nodeA"])] != node_net[str(e["nodeB"])]) for e in edges))
    # the relationships of a pair sum, by kind, to the weights of the pair's row in network_edges.csv
    sums = defaultdict(lambda: {"name": 0.0, "address": 0.0, "identity": 0.0})
    for e in edges:
        sums[(e["nodeA"], e["nodeB"])][{"CONNECTED_BY_NAME": "name", "CONNECTED_BY_ADDRESS": "address", "CONNECTED_BY_IDENTITY": "identity"}[e["type"]]] += e["weight"]
    old = {(int(r["node_a"]), int(r["node_b"])): (float(r["name_weight"]), float(r["address_weight"]), float(r["identity_weight"]))
           for r in release.rows("network_edges")}
    check("release: the pairs are the rows of network_edges", set(sums) == set(old) == pairs, f"{len(sums)} vs {len(old)}")
    check("release: each pair's name, address and identity weights equal its network_edges row",
          all(abs(sums[p]["name"] - w[0]) + abs(sums[p]["address"] - w[1]) + abs(sums[p]["identity"] - w[2]) < 1e-9 for p, w in old.items()))

    t = fixtures["totals"]
    check("release: landlord count matches fixture", len(node_net) == t["landlords"], f"{len(node_net)} vs {t['landlords']}")
    check("release: covers count matches fixture", len(covers) == t["covers"], f"{len(covers)} vs {t['covers']}")
    check("release: pair count matches fixture", len(pairs) == t["links"], f"{len(pairs)} vs {t['links']}")
    check("release: boundary pair count matches fixture", len(crossing) == t["boundary_links"], f"{len(crossing)}")
    kinds = {k: sum(1 for e in edges if e["type"] == k) for k in NETWORK_TYPES}
    check("release: relationships by type match fixture", kinds == t["relationships"], f"{kinds}")
    check("release: set-aside address edges match fixture",
          sum(1 for _ in release.rows("graph_edges", drop_reason="address_mask")) == t["masked_edges_not_loaded"])

    def by_network(gid):
        nodes = {int(n) for n, g in node_net.items() if g == gid}
        inside = [e for e in edges if e["nodeA"] in nodes and e["nodeB"] in nodes]
        boundary = [e for e in edges if (e["nodeA"] in nodes) != (e["nodeB"] in nodes)]
        return nodes, inside, boundary

    def pair_count(es):
        return len({(e["nodeA"], e["nodeB"]) for e in es})

    with driver, driver.session(database=os.environ["NEO4J_DATABASE"], default_access_mode="READ") as session, pg.cursor() as cur:
        for f in fixtures["networks"]:
            gid = f["groupId"]
            nodes, inside, boundary = by_network(gid)
            derived_lots = defaultdict(list)
            for (n, b), reg in sorted(covers.items()):
                if n in nodes:
                    derived_lots[n].append({"bbl": b, "registrationId": reg})
            fx_lots = {x["nodeId"]: sorted(x["lots"], key=lambda r: r["bbl"]) for x in f["landlords"]}
            check(f"{gid} landlords fixture matches release", {n: sorted(v, key=lambda r: r["bbl"]) for n, v in derived_lots.items()} == fx_lots)
            check(f"{gid} links fixture matches release", len(inside) + len(boundary) == len(f["links"]) and
                  all(any(same(e, x) for e in inside + boundary) for x in f["links"]))
            for x in f["landlords"]:
                for lot in x["lots"]:
                    cur.execute("SELECT count(*) FROM hpd_registrations WHERE bbl = %s AND registrationid = %s", (lot["bbl"], lot["registrationId"]))
                    check(f"{gid} node {x['nodeId']}: registration {lot['registrationId']} is on lot {lot['bbl']} in HPD", cur.fetchone()[0] > 0)
            got_l = {r["nodeId"]: sorted(r["lots"], key=lambda r: r["bbl"]) for r in session.run(lookup_landlords, groupId=gid)}
            check(f"{gid} graph landlords match fixture", got_l == fx_lots, f"graph has {got_l}")
            got = [dict(r) for r in session.run(lookup_links, groupId=gid)]
            check(f"{gid} graph links match fixture", len(got) == len(f["links"]) and all(any(same(g, x) for g in got) for x in f["links"]), f"graph has {got}")

        for f in fixtures["counts"]:
            gid = f["groupId"]
            nodes, inside, boundary = by_network(gid)
            check(f"{gid} fixture counts match release", (len(nodes), pair_count(inside), pair_count(boundary)) == (f["landlords"], f["inside"], f["boundary"]),
                  f"release says {(len(nodes), pair_count(inside), pair_count(boundary))}")
            got_l = list(session.run(lookup_landlords, groupId=gid))
            got = [dict(r) for r in session.run(lookup_links, groupId=gid)]
            check(f"{gid} graph counts match fixture", (len(got_l), pair_count([g for g in got if g["networkGroupId"] is not None]),
                                                        pair_count([g for g in got if g["networkGroupId"] is None])) ==
                  (f["landlords"], f["inside"], f["boundary"]))

        h = fixtures["hub_landlord"]
        rec = session.run("MATCH (a:Landlord {nodeId: $n})-[c:COVERS]->(l:Lot)-[:IN_NETWORK]->(g:OperationalNetwork) "
                          "RETURN count(l) AS lots, collect(DISTINCT g.groupId) AS networks", n=h["nodeId"]).single()
        check(f"hub landlord {h['nodeId']} covers {h['lots']} lots in {h['groupId']}", rec["lots"] == h["lots"] and rec["networks"] == [h["groupId"]],
              f"graph has {dict(rec)}")
        check("release: the hub landlord is the one covering the most lots",
              max(__import__("collections").Counter(n for n, _ in covers).items(), key=lambda kv: kv[1]) == (h["nodeId"], h["lots"]))

        # whole layer, graph against release
        g_nodes = session.run("MATCH (a:Landlord)-[:COVERS]->(:Lot)-[:IN_NETWORK]->() RETURN count(DISTINCT a) AS n").single()["n"]
        check("graph: landlords covering network lots match the release's network nodes", g_nodes == len(node_net), f"{g_nodes} vs {len(node_net)}")
        g_cov = {(r["n"], r["b"]): r["reg"] for r in session.run("MATCH (a:Landlord)-[c:COVERS]->(l:Lot)-[:IN_NETWORK]->() RETURN a.nodeId AS n, l.bbl AS b, c.registrationId AS reg")}
        check("graph: every cover of a network lot and its registration matches the release", g_cov == covers, f"{len(g_cov)} in graph vs {len(covers)}")
        g_rels = {}
        for r in session.run("MATCH (x:Landlord)-[k:CONNECTED_BY_NAME|CONNECTED_BY_ADDRESS|CONNECTED_BY_IDENTITY]->(y:Landlord) WHERE k.networkEdgeId IS NOT NULL "
                             "RETURN type(k) AS type, x.nodeId AS a, y.nodeId AS b, k.evidenceId AS ev, k.weight AS weight, k.stage AS stage, "
                             "k.networkEdgeId AS networkEdgeId, k.networkGroupId AS networkGroupId"):
            g_rels[(r["type"], r["a"], r["b"], r["ev"] or "")] = {"weight": r["weight"], "networkEdgeId": r["networkEdgeId"], "networkGroupId": r["networkGroupId"],
                                                                  **({"stage": r["stage"]} if r["type"] == "CONNECTED_BY_IDENTITY" else {})}
        want = {k: {x: y for x, y in v.items() if x in ("weight", "networkEdgeId", "networkGroupId", "stage") and (x != "stage" or k[0] == "CONNECTED_BY_IDENTITY")}
                for k, v in rels.items()}
        check("graph: every relationship the network used matches the release field by field",
              g_rels.keys() == want.keys() and all(same(g_rels[k], want[k]) for k in want), f"{len(g_rels)} in graph vs {len(want)}")
        # every covered registration exists in the frozen source (bounded: one query for all pairs)
        cur.execute("SELECT count(*) FROM (SELECT unnest(%(b)s::text[]) AS bbl, unnest(%(r)s::int[]) AS rid) t "
                    "WHERE NOT EXISTS (SELECT 1 FROM hpd_registrations h WHERE h.bbl = t.bbl AND h.registrationid = t.rid)",
                    {"b": [b for _, b in covers], "r": list(covers.values())})
        missing = cur.fetchone()[0]
        check("source: every covered lot has that registration in hpd_registrations", missing == 0, f"{missing} pairs not found")
    pg.close()
    return finish()


if __name__ == "__main__":
    sys.exit(main())
