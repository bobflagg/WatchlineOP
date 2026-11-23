"""Check Q21.3 (one lot, its two layers, and which lots appear in only one list) against the pinned BOR release. Read-only everywhere.
Run: uv run python tests/q21_3/check_layers.py
"""

import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from bor_support import check, connect, finish, load_fixtures  # noqa: E402
from q21_support import NET, PORT, group_layer, network_layer  # noqa: E402


def main() -> int:
    driver, pg, release = connect()
    pg.close()
    fx = load_fixtures(HERE / "fixtures.yaml")
    _, net_members, net_of = network_layer(release)
    _, port_members, port_of = group_layer(release, PORT)
    q = (HERE / "lookup.cypher").read_text()
    with driver, driver.session(database=os.environ["NEO4J_DATABASE"], default_access_mode="READ") as s:
        for f in fx["lots"]:
            bbl = f["bbl"]
            r = s.run(q, bbl=bbl).single()
            if r is None:
                check(f"{bbl}: lot is in the graph", False)
                continue
            ng, pgid = net_of.get(bbl), port_of.get(bbl)
            net, port = set(net_members.get(ng, [])), set(port_members.get(pgid, []))
            check(f"{bbl}: group ids equal the release ({ng}, {pgid})", (r["networkGroupId"], r["portfolioGroupId"]) == (ng, pgid), str(dict(r)))
            check(f"{bbl}: network and portfolio members equal the release", (set(r["netLots"]), set(r["portLots"])) == (net, port))
            check(f"{bbl}: only-network, only-portfolio and both are the set differences",
                  (set(r["onlyNetwork"]), set(r["onlyPortfolio"]), set(r["both"])) == (net - port, port - net, net & port))
            check(f"{bbl}: a lot in no group has an absence reason, not an empty list",
                  (ng is not None or r["networkAbsenceDetail"] is not None or r["networkGroupId"] is None) and (pgid is not None or r["portfolioGroupId"] is None))
    return finish()


if __name__ == "__main__":
    sys.exit(main())
