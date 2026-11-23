"""Check the comparison of Owner Portfolio and Operational Network footprints (Q9.4) against the pinned BOR release. Read-only everywhere.

1. Each fixture is re-derived from the release (group_bbls.csv, rental lots), so a stale fixture fails.
2. Each fixture lot is looked up in the graph with tests/q9_4/lookup.cypher.
3. Over the whole graph: the lots in both layers, in the portfolio only and in the network only match the release and the fixture.

Any failure or error is a failure; nothing is skipped. Exit code 0 only if every check passes.
Run: uv run python tests/q9_4/check_compare.py
"""

import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from bor_support import check, connect, finish, group_layer, load_fixtures  # noqa: E402


def main() -> int:
    driver, pg, release = connect()
    pg.close()
    fixtures = load_fixtures(HERE / "fixtures.yaml")
    lookup = (HERE / "lookup.cypher").read_text()
    _, pmem, pof = group_layer(release, "owner_portfolio")
    _, nmem, nof = group_layer(release, "operational_network")

    def derive(bbl):
        p, n = pof.get(bbl), nof.get(bbl)
        pl, nl = set(pmem.get(p, [])), set(nmem.get(n, []))
        return {"portfolioId": p, "networkId": n, "portfolioLots": len(pl), "networkLots": len(nl), "inBoth": len(pl & nl),
                "portfolioOnlyLots": sorted(pl - nl), "networkOnlyLots": sorted(nl - pl)}

    t = fixtures["totals"]
    both, p_only, n_only = set(pof) & set(nof), set(pof) - set(nof), set(nof) - set(pof)
    check("release: lots in both layers match fixture", len(both) == t["in_both"], f"{len(both)}")
    check("release: portfolio-only lots match fixture", len(p_only) == t["portfolio_only"], f"{len(p_only)}")
    check("release: network-only lots match fixture", len(n_only) == t["network_only"], f"{len(n_only)}")

    with driver, driver.session(database=os.environ["NEO4J_DATABASE"], default_access_mode="READ") as session:
        for f in fixtures["lots"]:
            bbl = f["bbl"]
            d = derive(bbl)
            check(f"{bbl} fixture matches release",
                  all(d[k] == f[k] for k in ("portfolioId", "networkId", "portfolioLots", "networkLots", "inBoth"))
                  and (d["portfolioOnlyLots"] == f["portfolioOnly"] if "portfolioOnly" in f else len(d["portfolioOnlyLots"]) == f["portfolioOnly_count"])
                  and (d["networkOnlyLots"] == f["networkOnly"] if "networkOnly" in f else len(d["networkOnlyLots"]) == f["networkOnly_count"]),
                  f"release says {d['portfolioId']} / {d['networkId']}, {d['portfolioLots']}/{d['networkLots']}/{d['inBoth']}")
            rec = session.run(lookup, bbl=bbl).single()
            got = {k: rec[k] for k in ("portfolioId", "networkId", "portfolioLots", "networkLots", "inBoth", "portfolioOnlyLots", "networkOnlyLots")} if rec else None
            check(f"{bbl} graph matches the release", got is not None and {k: sorted(v) if isinstance(v, list) else v for k, v in got.items()} == d,
                  f"graph has {got and {k: (len(v) if isinstance(v, list) else v) for k, v in got.items()}}")
        g = session.run("MATCH (l:Lot) WITH l, EXISTS { (l)-[:IN_PORTFOLIO]->() } AS p, EXISTS { (l)-[:IN_NETWORK]->() } AS n "
                        "RETURN sum(CASE WHEN p AND n THEN 1 ELSE 0 END) AS inBoth, sum(CASE WHEN p AND NOT n THEN 1 ELSE 0 END) AS pOnly, "
                        "sum(CASE WHEN n AND NOT p THEN 1 ELSE 0 END) AS nOnly").single()
        check("graph: lots in both layers, in the portfolio only and in the network only match the release",
              (g["inBoth"], g["pOnly"], g["nOnly"]) == (len(both), len(p_only), len(n_only)), f"graph {dict(g)}")
    return finish()


if __name__ == "__main__":
    sys.exit(main())
