"""Check the release-wide disagreement between the layers (Q10.3) against the pinned BOR release. Read-only everywhere.

1. Counts are re-derived from the release (group_bbls.csv): networks holding several portfolios, and portfolios spanning several
   networks, over rental lots and over all lots (the second differs by the portfolios that reach a second network only through co-op or condo lots).
2. The graph (tests/q10_3/lookup.cypher) equals the rental-lot counts and the fixture's list of spanning portfolios.
3. Cause: every spanning portfolio joins its networks through at least one deed link, or a registered-LLC identity link, that carries no network id.

Any failure or error is a failure; nothing is skipped. Exit code 0 only if every check passes.
Run: uv run python tests/q10_3/check_release_wide.py
"""

import os
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from bor_support import check, connect, finish, group_layer, load_fixtures  # noqa: E402

CAUSE = """MATCH (p:OwnerPortfolio {groupId: $pid})<-[:IN_PORTFOLIO]-(:Lot)<-[:COVERS]-(:Landlord)-[k:CONNECTED_BY_DEED|CONNECTED_BY_IDENTITY]-(:Landlord)
WHERE k.portfolioGroupId = $pid AND k.networkGroupId IS NULL RETURN count(DISTINCT k) AS links"""


def span(release):
    _, _, pof = group_layer(release, "owner_portfolio")
    _, _, nof = group_layer(release, "operational_network")
    nets_of_p, ps_of_n = defaultdict(set), defaultdict(set)
    for b, p in pof.items():
        if b in nof:
            nets_of_p[p].add(nof[b])
            ps_of_n[nof[b]].add(p)
    return {p for p, v in nets_of_p.items() if len(v) > 1}, {n for n, v in ps_of_n.items() if len(v) > 1}


def main() -> int:
    driver, pg, release = connect()
    pg.close()
    fixtures = load_fixtures(HERE / "fixtures.yaml")
    t = fixtures["totals"]
    lookup = (HERE / "lookup.cypher").read_text()
    spanning, many = span(release)
    check("release: networks with several portfolios match fixture", len(many) == t["networks_with_many_portfolios"], f"{len(many)}")
    check("release: spanning portfolios (rental lots) match fixture", sorted(spanning) == sorted(fixtures["spanning_portfolios"]), f"{len(spanning)}")

    # all lots: group_bbls rows regardless of the rental flag
    nets_all = defaultdict(set)
    nof_all = {r["bbl"]: r["group_id"] for r in release.rows("group_bbls", layer="operational_network")}
    for r in release.rows("group_bbls", layer="owner_portfolio"):
        if r["bbl"] in nof_all:
            nets_all[r["group_id"]].add(nof_all[r["bbl"]])
    span_all = {p for p, v in nets_all.items() if len(v) > 1}
    check("release: spanning portfolios over all lots match fixture", len(span_all) == t["portfolios_spanning_all_lots"], f"{len(span_all)}")
    check("release: the extra portfolio is the one in the fixture", sorted(span_all - spanning) == sorted(fixtures["spanning_only_via_non_rental"]), f"{sorted(span_all - spanning)}")

    with driver, driver.session(database=os.environ["NEO4J_DATABASE"], default_access_mode="READ") as session:
        rec = session.run(lookup).single()
        check("graph: networks with several portfolios match the release", rec["networksWithManyPortfolios"] == len(many), f"{rec['networksWithManyPortfolios']}")
        check("graph: spanning portfolios match the release", sorted(rec["spanningPortfolios"]) == sorted(spanning), f"{rec['portfoliosWithManyNetworks']}")
        for pid in fixtures["spanning_portfolios"]:
            n = session.run(CAUSE, pid=pid).single()["links"]
            check(f"{pid} is joined across networks by a deed or identity link no network uses", n > 0, f"{n} links")
    return finish()


if __name__ == "__main__":
    sys.exit(main())
