"""Check the connecting path between two lots of one group (Q19.2) against the pinned BOR release. Read-only everywhere.

1. Each fixture's step count is re-derived from graph_edges.csv (kept edges of the group), so a stale fixture fails.
2. The graph's representative path (tests/q19_2/lookup_*.cypher) has the fewest links, joins landlord records that cover the two lots,
   and every link is a kept release edge of that group with the same stage and evidence id. A pair with no common group has no path.
3. Where the fixture names stages, the graph path carries exactly those stage codes.

Any failure or error is a failure; nothing is skipped. Exit code 0 only if every check passes.
Run: uv run python tests/q19_2/check_path.py
"""

import os
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from bor_support import check, connect, finish, load_fixtures  # noqa: E402
from q19_support import NET, PORT, Pair  # noqa: E402


def main() -> int:
    driver, pg, release = connect()
    pg.close()
    fixtures = load_fixtures(HERE / "fixtures.yaml")
    lookups = {PORT: (HERE / "lookup_portfolio.cypher").read_text(), NET: (HERE / "lookup_network.cypher").read_text()}
    pair = Pair(release)

    with driver, driver.session(database=os.environ["NEO4J_DATABASE"], default_access_mode="READ") as session:
        for f in fixtures["paths"]:
            a, b, layer, g = f["a"], f["b"], f["layer"], f["groupId"]
            of = pair.net_of if layer == NET else pair.port_of
            check(f"{f['id']}: both lots are in {g} in the release", of.get(a) == g and of.get(b) == g)
            steps = pair.steps(a, b, layer, g)
            check(f"{f['id']}: fixture steps match release", steps == f["steps"], f"release says {steps}")
            rec = session.run(lookups[layer], a=a, b=b, groupId=g).single()
            if rec is None:
                check(f"{f['id']}: graph has a path", False)
                continue
            check(f"{f['id']}: graph path has the fewest links", rec["steps"] == steps, f"graph {rec['steps']} vs release {steps}")
            links = rec["links"]
            check(f"{f['id']}: path length equals its links", len(links) == rec["steps"])
            keys = pair.edge_keys(layer, g)
            if layer == PORT:
                bad = [k for k in links if (k["stage"], k["nodeA"], k["nodeB"], k["evidenceId"]) not in keys]
            else:
                pairs_ = {(x, y) for _, x, y, _ in keys}
                bad = [k for k in links if (k["nodeA"], k["nodeB"]) not in pairs_]
            check(f"{f['id']}: every link is a kept release edge of the group", not bad, f"{bad}")
            ends = rec["nodeIds"]
            check(f"{f['id']}: the path starts and ends at records covering the lots",
                  str(ends[0]) in pair.nodes_of[a] and str(ends[-1]) in pair.nodes_of[b], f"{ends}")
            if "stages" in f:
                check(f"{f['id']}: stages match fixture", Counter(k["stage"] for k in links) == Counter(f["stages"]), f"{[k['stage'] for k in links]}")
        for f in fixtures["no_path"]:
            a, b, layer, g = f["a"], f["b"], f["layer"], f["groupId"]
            of = pair.net_of if layer == NET else pair.port_of
            check(f"{f['id']}: the lots are not both in {g} in the release", not (of.get(a) == g and of.get(b) == g))
            check(f"{f['id']}: graph returns no path", session.run(lookups[layer], a=a, b=b, groupId=g).single() is None)
    return finish()


if __name__ == "__main__":
    sys.exit(main())
