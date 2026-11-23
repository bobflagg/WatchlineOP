"""Check the link kinds that explain each lot in one layer and not the other (Q10.2). Read-only everywhere.

1. The lots in one layer only are re-derived from the release (group_bbls.csv, rental lots) and must equal the fixture's lots and the graph's.
2. Each differing lot's link kinds and distinct link count come from tests/q10_2/lookup.cypher and must equal the fixture.
3. A network-only lot is explained by network links that carry no portfolio id; a portfolio-only lot by portfolio links that carry no network id.

Any failure or error is a failure; nothing is skipped. Exit code 0 only if every check passes.
Run: uv run python tests/q10_2/check_evidence.py
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

    with driver, driver.session(database=os.environ["NEO4J_DATABASE"], default_access_mode="READ") as session:
        for f in fixtures["lots"]:
            bbl = f["bbl"]
            p, n = pof.get(bbl), nof.get(bbl)
            pl, nl = set(pmem.get(p, [])), set(nmem.get(n, []))
            want = {(b, "network_only") for b in nl - pl} | {(b, "portfolio_only") for b in pl - nl}
            fx = {(d["bbl"], d["side"]): d for d in f["differences"]}
            check(f"{bbl} fixture lists exactly the release's differing lots", set(fx) == want, f"release has {len(want)}, fixture {len(fx)}")
            rec = session.run(lookup, bbl=bbl).single()
            got = {(d["bbl"], d["side"]): d for d in rec["differences"]} if rec else {}
            check(f"{bbl} graph lists exactly the release's differing lots", set(got) == want, f"graph has {len(got)}")
            check(f"{bbl} link kinds match the fixture", all(sorted(got[k]["kinds"]) == sorted(v["kinds"]) and got[k]["links"] == v["links"]
                                                              for k, v in fx.items() if k in got) and set(fx) <= set(got),
                  "; ".join(f"{k[0]} {got[k]['kinds']} {got[k]['links']}" for k in sorted(got)[:3]))
    return finish()


if __name__ == "__main__":
    sys.exit(main())
