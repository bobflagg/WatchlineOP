"""Shared helpers for tests/q19_*: expected answers about a pair of lots, derived from the pinned BOR release alone.

Read-only on the release and the graph. Independent of the loaders: layer membership from groups/group_bbls/bbl_status, paths by a
breadth-first search over the kept rows of graph_edges.csv.
"""

from collections import defaultdict, deque
from functools import lru_cache

from bor_support import group_layer, status_rows  # noqa: F401  (re-exported for the checks)

NET, PORT = "operational_network", "owner_portfolio"


class Pair:
    """Release facts needed for pair questions, loaded once per check."""

    def __init__(self, release):
        self.release = release
        self.nodes_of = defaultdict(set)  # bbl -> node ids (landlord records covering the lot)
        for r in release.rows("node_observations"):
            self.nodes_of[r["bbl"]].add(r["node_id"])
        self.landlords = {NET: {r["node_id"] for r in release.rows("network_membership") if r["operational_network_id"]},
                          PORT: {r["node_id"] for r in release.rows("group_members", layer=PORT)}}
        self.net_groups, _, self.net_of = group_layer(release, NET)
        self.port_groups, _, self.port_of = group_layer(release, PORT)
        self.component = {r["node_id"]: r["component_id"] for r in release.rows("network_membership") if r["component_id"]}
        self.edges = {NET: [], PORT: []}
        for e in release.rows("graph_edges", kept="True"):
            self.edges[e["layer"]].append(e)

    def status(self, bbl, layer):
        for r in status_rows(self.release, {bbl}, layer):
            return r
        return None

    def layer_state(self, a, b, layer):
        """{'state': same|different|ungrouped, groups, reasons} for two lots in one layer, as the release says."""
        of = self.net_of if layer == NET else self.port_of
        ga, gb = of.get(a), of.get(b)
        reason = lambda bbl: (lambda r: r["reason_code"] if r and r["status"] != "in_group" else None)(self.status(bbl, layer))
        if ga and gb:
            state = "same" if ga == gb else "different"
        else:
            state = "ungrouped"
        return {"state": state, "groupA": ga, "groupB": gb,
                "reasonA": None if ga else reason(a), "reasonB": None if gb else reason(b)}

    def steps(self, a, b, layer, group=None):
        """Fewest links between a landlord record of lot a and one of lot b over kept edges (of one group when given), or None."""
        adj = defaultdict(list)
        for e in self.edges[layer]:
            if group is None or e["group_id"] == group:
                adj[e["node_a"]].append(e["node_b"])
                adj[e["node_b"]].append(e["node_a"])
        keep = self.landlords[NET if layer == NET else PORT]  # only landlord records the graph holds
        targets = self.nodes_of[b] & keep
        seen = {n: 0 for n in self.nodes_of[a] & keep}
        q = deque(seen)
        while q:
            n = q.popleft()
            if n in targets:
                return seen[n]
            for m in adj[n]:
                if m not in seen:
                    seen[m] = seen[n] + 1
                    q.append(m)
        return None

    def same_component(self, a, b):
        ca = {self.component[n] for n in self.nodes_of[a] if n in self.component}
        cb = {self.component[n] for n in self.nodes_of[b] if n in self.component}
        return bool(ca & cb)

    def edge_keys(self, layer, group=None):
        """{(stage, node_a, node_b, evidence_id)} of kept edges of a layer (of one group when given)."""
        return {(e["stage"], int(e["node_a"]), int(e["node_b"]), e["evidence_id"]) for e in self.edges[layer]
                if group is None or e["group_id"] == group}
