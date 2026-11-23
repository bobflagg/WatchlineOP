"""Check which Owner Portfolio a lot belongs to (Q9.1) against the pinned BOR release. Read-only everywhere.

1. Each fixture is re-derived from the release (groups.csv, group_bbls.csv), so a stale fixture fails.
2. Each fixture lot is looked up in the graph with tests/q9_1/lookup.cypher.
3. Over the whole layer: the graph's portfolios, compositions and memberships equal the release's; every portfolio has a
   rental member; co-op and condo lots outside the footprint have no membership.

Any failure or error is a failure; nothing is skipped. Exit code 0 only if every check passes.
Run: uv run python tests/q9_1/check_portfolio.py
"""

import os
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from bor_support import check, connect, finish, group_layer, load_fixtures  # noqa: E402

LAYER = "owner_portfolio"


def main() -> int:
    driver, pg, release = connect()
    pg.close()
    fixtures = load_fixtures(HERE / "fixtures.yaml")
    lookup = (HERE / "lookup.cypher").read_text()
    groups, members, group_of = group_layer(release, LAYER)
    excluded = {r["bbl"] for r in release.rows("group_bbls", layer=LAYER) if r["rental"] == "False"}

    t = fixtures["totals"]
    check("release: portfolio count matches fixture", len(groups) == t["portfolios"], f"{len(groups)} vs {t['portfolios']}")
    check("release: compositions match fixture", dict(Counter(g["composition"] for g in groups.values())) == t["by_composition"])
    check("release: rental memberships match fixture", len(group_of) == t["rental_memberships"], f"{len(group_of)} vs {t['rental_memberships']}")
    check("release: excluded lots match fixture", len(excluded) == t["excluded_lots"], f"{len(excluded)} vs {t['excluded_lots']}")
    check("release: single-lot portfolios match fixture", sum(len(v) == 1 for v in members.values()) == t["single_lot_portfolios"])
    check("release: every portfolio has a rental member", set(members) == set(groups))

    with driver, driver.session(database=os.environ["NEO4J_DATABASE"], default_access_mode="READ") as session:
        for f in fixtures["lots"]:
            bbl = f["bbl"]
            gid = group_of.get(bbl)
            derived = {"groupId": gid, "composition": groups[gid]["composition"] if gid else None}
            expected = {"groupId": f["groupId"], "composition": f["composition"]}
            check(f"{bbl} fixture matches release", derived == expected, f"release says {derived}")
            rec = session.run(lookup, bbl=bbl).single()
            got = {"groupId": rec["groupId"], "composition": rec["composition"]} if rec else None
            check(f"{bbl} graph matches fixture", got == expected, f"graph has {got}")
        for f in fixtures["absent_from_graph"]:
            check(f"{f['bbl']} has no Lot in the graph", session.run(lookup, bbl=f["bbl"]).single() is None)

        g = {r["groupId"]: r["composition"] for r in session.run("MATCH (p:OwnerPortfolio) RETURN p.groupId AS groupId, p.composition AS composition")}
        check("graph: portfolios and compositions match the release", g == {k: v["composition"] for k, v in groups.items()}, f"{len(g)} vs {len(groups)}")
        m = {r["bbl"]: r["groupId"] for r in session.run("MATCH (l:Lot)-[:IN_PORTFOLIO]->(p:OwnerPortfolio) RETURN l.bbl AS bbl, p.groupId AS groupId")}
        check("graph: every membership matches the release", m == group_of, f"{len(m)} vs {len(group_of)}")
        multi = session.run("MATCH (l:Lot)-[r:IN_PORTFOLIO]->() WITH l, count(r) AS n WHERE n > 1 RETURN count(l) AS n").single()["n"]
        check("graph: no lot is in two portfolios", multi == 0, f"{multi} lots")
        stray = session.run("MATCH (l:Lot)-[:IN_PORTFOLIO]->() WHERE l.bbl IN $b RETURN count(l) AS n", b=sorted(excluded)).single()["n"]
        check("graph: co-op and condo lots outside the footprint have no membership", stray == 0, f"{stray} lots")
    return finish()


if __name__ == "__main__":
    sys.exit(main())
