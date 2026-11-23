"""Check connectivity before subdivision versus network membership (Q19.3) against the pinned BOR release. Read-only everywhere.

1. Each fixture is re-derived from the release: same component (network_membership.csv), fewest links over the kept network edges
   (graph_edges.csv), same network and split (groups.csv, group_bbls.csv), so a stale fixture fails.
2. The graph path (tests/q19_3/lookup.cypher) exists exactly when the release has a path, has the same fewest links, and shows a
   link that crosses a cut (networkGroupId absent) exactly when the fixture says so.
3. A pair connected before subdivision but in different networks is the case the answer must not call membership.
4. Totals: Louvain networks, and components that hold several networks.

Any failure or error is a failure; nothing is skipped. Exit code 0 only if every check passes.
Run: uv run python tests/q19_3/check_subdivision.py
"""

import os
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from bor_support import check, connect, finish, load_fixtures  # noqa: E402
from q19_support import NET, Pair  # noqa: E402


def main() -> int:
    driver, pg, release = connect()
    pg.close()
    fixtures = load_fixtures(HERE / "fixtures.yaml")
    lookup = (HERE / "lookup.cypher").read_text()
    pair = Pair(release)

    comps = defaultdict(set)
    for r in release.rows("network_membership"):
        if r["operational_network_id"]:
            comps[r["component_id"]].add(r["operational_network_id"])
    t = fixtures["totals"]
    n_louvain = sum(g["split"] == "louvain" for g in pair.net_groups.values())
    check("release: Louvain networks match fixture", n_louvain == t["louvain_networks"], f"{n_louvain} vs {t['louvain_networks']}")
    several = sum(len(s) > 1 for s in comps.values())
    check("release: components in several networks match fixture", several == t["components_in_several_networks"], f"{several}")

    with driver, driver.session(database=os.environ["NEO4J_DATABASE"], default_access_mode="READ") as session:
        for f in fixtures["pairs"]:
            a, b = f["a"], f["b"]
            ga, gb = pair.net_of.get(a), pair.net_of.get(b)
            steps = pair.steps(a, b, NET)
            same_net = bool(ga) and ga == gb
            split = pair.net_groups[ga]["split"] if ga else None
            check(f"{f['id']}: fixture connected matches release", (steps is not None) == f["connected"], f"release steps {steps}")
            check(f"{f['id']}: fixture sameNetwork matches release", same_net == f["sameNetwork"])
            check(f"{f['id']}: connected means the same component", (steps is not None) == pair.same_component(a, b))
            if f["connected"]:
                check(f"{f['id']}: fixture steps match release", steps == f["steps"], f"release says {steps}")
                check(f"{f['id']}: fixture split matches release", split == f["split"], f"release says {split}")
            rec = session.run(lookup, a=a, b=b).single()
            check(f"{f['id']}: graph has a path exactly when the release does", (rec is not None) == f["connected"])
            if rec is not None and f["connected"]:
                check(f"{f['id']}: graph steps match", rec["steps"] == f["steps"], f"{rec['steps']}")
                crosses = any(k["crossesCut"] for k in rec["links"])
                check(f"{f['id']}: crosses a cut as the fixture says", crosses == f["crossesCut"], f"{rec['links']}")
                if f["connected"] and not f["sameNetwork"]:
                    check(f"{f['id']}: connected before subdivision yet in different networks", ga != gb)

        # every pair of Louvain networks of one component is connected by a path, so the cut shows as links with no network group id
        cut = session.run("MATCH ()-[k:CONNECTED_BY_NAME|CONNECTED_BY_ADDRESS|CONNECTED_BY_IDENTITY]->() "
                          "WHERE k.networkEdgeId IS NOT NULL AND k.networkGroupId IS NULL RETURN count(k) AS n").single()["n"]
        rel_cut = sum(1 for e in pair.edges[NET] if not e["group_id"])
        check("graph: links that cross a network cut match the release's kept network edges with no group", cut > 0 and cut == rel_cut, f"graph {cut} vs release {rel_cut}")
    return finish()


if __name__ == "__main__":
    sys.exit(main())
