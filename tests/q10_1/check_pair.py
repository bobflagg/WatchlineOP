"""Check a lot's Operational Network and Owner Portfolio side by side (Q10.1) against the pinned BOR release. Read-only everywhere.

1. Each fixture is re-derived from the release (groups.csv, group_bbls.csv, rental lots), so a stale fixture fails.
2. Each fixture lot is looked up in the graph with tests/q10_1/lookup.cypher.
3. Both ids carry the run: every network has a split and every portfolio a composition in the graph.

Any failure or error is a failure; nothing is skipped. Exit code 0 only if every check passes.
Run: uv run python tests/q10_1/check_pair.py
"""

import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from bor_support import check, connect, finish, group_layer, load_fixtures  # noqa: E402

KEYS = ("networkId", "networkSplit", "portfolioId", "composition", "networkLots", "portfolioLots", "networkOnlyLots", "portfolioOnlyLots")


def main() -> int:
    driver, pg, release = connect()
    pg.close()
    fixtures = load_fixtures(HERE / "fixtures.yaml")
    lookup = (HERE / "lookup.cypher").read_text()
    pg_groups, pmem, pof = group_layer(release, "owner_portfolio")
    ng_groups, nmem, nof = group_layer(release, "operational_network")

    def derive(bbl):
        p, n = pof.get(bbl), nof.get(bbl)
        pl, nl = set(pmem.get(p, [])), set(nmem.get(n, []))
        return {"networkId": n, "networkSplit": ng_groups[n]["split"] if n else None, "portfolioId": p,
                "composition": pg_groups[p]["composition"] if p else None, "networkLots": len(nl), "portfolioLots": len(pl),
                "networkOnlyLots": sorted(nl - pl), "portfolioOnlyLots": sorted(pl - nl)}

    with driver, driver.session(database=os.environ["NEO4J_DATABASE"], default_access_mode="READ") as session:
        for f in fixtures["lots"]:
            bbl = f["bbl"]
            d = derive(bbl)
            expect = {k: f[k] for k in ("networkId", "networkSplit", "portfolioId", "composition", "networkLots", "portfolioLots")}
            check(f"{bbl} fixture matches release", all(d[k] == v for k, v in expect.items())
                  and len(d["networkOnlyLots"]) == f["networkOnly"] and len(d["portfolioOnlyLots"]) == f["portfolioOnly"],
                  f"release says {d['networkId']} / {d['portfolioId']}, {d['networkLots']}/{d['portfolioLots']}")
            rec = session.run(lookup, bbl=bbl).single()
            got = {k: rec[k] for k in KEYS} if rec else None
            check(f"{bbl} graph matches the release", got is not None and {k: sorted(v) if isinstance(v, list) else v for k, v in got.items()} == d,
                  f"graph has {got and {k: (len(v) if isinstance(v, list) else v) for k, v in got.items()}}")
        n = session.run("MATCH (n:OperationalNetwork) WHERE n.split IS NULL RETURN count(n) AS c").single()["c"]
        check("graph: every network has a split", n == 0, f"{n} networks")
        p = session.run("MATCH (p:OwnerPortfolio) WHERE p.composition IS NULL RETURN count(p) AS c").single()["c"]
        check("graph: every portfolio has a composition", p == 0, f"{p} portfolios")
    return finish()


if __name__ == "__main__":
    sys.exit(main())
