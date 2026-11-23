"""Check Operational Network membership (Q8.1) against the pinned BOR release. Read-only everywhere.

1. Each fixture is re-derived from the release, so a stale fixture fails.
2. Each fixture lot is looked up in the graph with tests/q8_1/lookup.cypher.
3. Totals: networks, splits and member lots match between the release, the fixtures and the graph; every
   network has the member lots the release lists; no lot is in more than one network.

Any failure or error is a failure; nothing is skipped. Exit code 0 only if every check passes.
Run: uv run python tests/q8_1/check_network.py
"""

import os
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from bor_support import check, connect, finish, load_fixtures, network_layer  # noqa: E402


def main() -> int:
    driver, pg, release = connect()
    pg.close()
    fixtures = load_fixtures(HERE / "fixtures.yaml")
    lookup = (HERE / "lookup.cypher").read_text()
    split, members, group_of = network_layer(release)

    with driver, driver.session(database=os.environ["NEO4J_DATABASE"], default_access_mode="READ") as session:
        for f in fixtures["lots"]:
            bbl = f["bbl"]
            gid = group_of.get(bbl)
            derived = {"groupId": gid, "split": split.get(gid)}
            check(f"{bbl} fixture matches release", derived == {"groupId": f["groupId"], "split": f["split"]}, f"release says {derived}")
            rec = session.run(lookup, bbl=bbl).single()
            got = {"groupId": rec["groupId"], "split": rec["split"]} if rec else None
            check(f"{bbl} graph matches fixture", got == {"groupId": f["groupId"], "split": f["split"]}, f"graph has {got}")
        for f in fixtures["absent_from_graph"]:
            check(f"{f['bbl']} is in the release universe", f["bbl"] not in group_of)
            check(f"{f['bbl']} has no Lot in the graph", session.run(lookup, bbl=f["bbl"]).single() is None)

        t = fixtures["totals"]
        counts = Counter(split.values())
        check("release: network count matches fixture", len(split) == t["networks"], f"{len(split)} vs {t['networks']}")
        check("release: wcc count matches fixture", counts["wcc"] == t["wcc"], f"{counts['wcc']} vs {t['wcc']}")
        check("release: louvain count matches fixture", counts["louvain"] == t["louvain"], f"{counts['louvain']} vs {t['louvain']}")
        check("release: member lot count matches fixture", len(group_of) == t["lots_in_networks"], f"{len(group_of)} vs {t['lots_in_networks']}")
        check("release: every network lists at least one lot and each lot is in one network",
              set(members) == set(split) and sum(len(v) for v in members.values()) == len(group_of))

        g = session.run("MATCH (n:OperationalNetwork) RETURN count(n) AS networks, count(CASE WHEN n.split = 'wcc' THEN 1 END) AS wcc, "
                        "count(CASE WHEN n.split = 'louvain' THEN 1 END) AS louvain").single()
        check("graph: network count matches release", g["networks"] == len(split), f"{g['networks']} vs {len(split)}")
        check("graph: wcc count matches release", g["wcc"] == counts["wcc"], f"{g['wcc']} vs {counts['wcc']}")
        check("graph: louvain count matches release", g["louvain"] == counts["louvain"], f"{g['louvain']} vs {counts['louvain']}")
        edges = session.run("MATCH (:Lot)-[r:IN_NETWORK]->(:OperationalNetwork) RETURN count(r) AS n").single()["n"]
        check("graph: membership edge count matches release", edges == len(group_of), f"{edges} vs {len(group_of)}")
        multi = session.run("MATCH (l:Lot)-[r:IN_NETWORK]->() WITH l, count(r) AS k WHERE k > 1 RETURN count(l) AS n").single()["n"]
        check("graph: no lot is in more than one network", multi == 0, f"{multi} lots")
        sizes = {r["groupId"]: r["lots"] for r in session.run(
            "MATCH (n:OperationalNetwork) OPTIONAL MATCH (n)<-[:IN_NETWORK]-(l:Lot) RETURN n.groupId AS groupId, count(l) AS lots")}
        wrong = [k for k, v in members.items() if sizes.get(k) != len(v)]
        check("graph: every network has the lots the release lists", not wrong, f"{len(wrong)} networks differ, e.g. {wrong[:3]}")

    return finish()


if __name__ == "__main__":
    sys.exit(main())
