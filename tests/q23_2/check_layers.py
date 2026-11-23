"""Check Q23.2 (an agent's footprint lots against the reference building's Operational Network and Owner Portfolio) against the pinned BOR release and the frozen source.

Footprint lots come from the source (tests/q23_1/expected.sql, rule N3), reference lots from tests/q23_2/expected.sql, groups from the release.
The graph lookup must give the same counts. Any failure or error is a failure. Run: uv run python tests/q23_2/check_layers.py
"""

import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from bor_support import check, connect, finish, load_fixtures, network_layer  # noqa: E402
from q23_support import NET, PORT, agent_rows, group_layer, layer_state, lots_of_bins  # noqa: E402


def main() -> int:
    driver, pg, release = connect()
    fx = load_fixtures(HERE / "fixtures.yaml")
    q = (HERE / "lookup.cypher").read_text()
    port_of = group_layer(release, PORT)[2]
    net_of = network_layer(release)[2]
    with driver, pg, driver.session(database=os.environ["NEO4J_DATABASE"], default_access_mode="READ") as s:
        for f in fx["cases"]:
            tag = f"{f['nameKey']} vs BIN {f['bin']}"
            lots = lots_of_bins(pg, {r[4] for r in agent_rows(pg, f["nameKey"])})
            ref = lots_of_bins(pg, {f["bin"]})
            check(f"{tag}: footprint has {f['lots']} lots in the source", len(lots) == f["lots"], str(len(lots)))
            if f.get("referenceLot"):
                check(f"{tag}: reference lot is {f['referenceLot']}", ref == {f["referenceLot"]}, str(ref))
            n, p = layer_state(lots, ref, net_of), layer_state(lots, ref, port_of)
            check(f"{tag}: release groups ({n['group']}, {p['group']}) match fixture", (n["group"], p["group"]) == (f["network"], f["portfolio"]), f"{n['group']} {p['group']}")
            if "networkSame" in f:
                check(f"{tag}: release counts match fixture",
                      (n["same"], n["other"], n["none"], p["same"], p["other"], p["none"]) ==
                      (f["networkSame"], f["networkOther"], f["networkNone"], f["portfolioSame"], f["portfolioOther"], f["portfolioNone"]), f"{n} {p}")
            rows = s.run(q, bin=f["bin"], nameKey=f["nameKey"]).data()
            check(f"{tag}: one row per reference lot", sorted(r["referenceLot"] for r in rows) == sorted(ref), str([r["referenceLot"] for r in rows]))
            for r in rows:
                got = (r["network"], r["portfolio"], r["lots"], r["networkSame"], r["networkOther"], r["networkNone"], r["portfolioSame"], r["portfolioOther"], r["portfolioNone"])
                want = (n["group"], p["group"], n["lots"], n["same"], n["other"], n["none"], p["same"], p["other"], p["none"])
                check(f"{tag}: graph counts equal the release and source", got == want, f"graph {got}, derived {want}")
                check(f"{tag}: same + other + none = lots, for both layers",
                      r["networkSame"] + r["networkOther"] + r["networkNone"] == r["lots"] == r["portfolioSame"] + r["portfolioOther"] + r["portfolioNone"])
    return finish()


if __name__ == "__main__":
    sys.exit(main())
