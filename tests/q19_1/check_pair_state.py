"""Check the state of a pair of lots in each layer (Q19.1) against the pinned BOR release. Read-only everywhere.

1. Each fixture pair is re-derived from the release (groups, group_bbls, bbl_status), so a stale fixture fails.
2. Each lot is looked up in the graph with tests/q19_1/lookup.cypher; the state (same, different, ungrouped), group ids and
   reason codes the graph gives equal the fixture.
3. A grouped lot never carries an absence reason; an ungrouped lot always does.

Any failure or error is a failure; nothing is skipped. Exit code 0 only if every check passes.
Run: uv run python tests/q19_1/check_pair_state.py
"""

import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from bor_support import check, connect, finish, load_fixtures  # noqa: E402
from q19_support import NET, PORT, Pair  # noqa: E402

KEYS = ("state", "groupA", "groupB", "reasonA", "reasonB")


def graph_state(rows, a, b, layer):
    by = {r["bbl"]: r for r in rows}
    gid, absence = ("networkGroupId", "networkAbsenceDetail") if layer == NET else ("portfolioGroupId", "portfolioAbsenceDetail")
    ga, gb = by[a][gid], by[b][gid]
    return {"state": ("same" if ga == gb else "different") if ga and gb else "ungrouped", "groupA": ga, "groupB": gb,
            "reasonA": None if ga else by[a][absence], "reasonB": None if gb else by[b][absence]}


def main() -> int:
    driver, pg, release = connect()
    pg.close()
    fixtures = load_fixtures(HERE / "fixtures.yaml")
    lookup = (HERE / "lookup.cypher").read_text()
    pair = Pair(release)

    with driver, driver.session(database=os.environ["NEO4J_DATABASE"], default_access_mode="READ") as session:
        for f in fixtures["pairs"]:
            a, b = f["a"], f["b"]
            rows = session.run(lookup, a=a, b=b).data()
            check(f"{f['id']}: both lots are in the graph", {r["bbl"] for r in rows} == {a, b})
            for layer in (NET, PORT):
                exp = {k: f[layer].get(k) for k in KEYS}
                derived = pair.layer_state(a, b, layer)
                check(f"{f['id']} {layer}: fixture matches release", derived == exp, f"release says {derived}")
                if {r["bbl"] for r in rows} == {a, b}:
                    got = graph_state(rows, a, b, layer)
                    check(f"{f['id']} {layer}: graph matches fixture", got == exp, f"graph has {got}")
            for r in rows:
                for gid, ab in (("networkGroupId", "networkAbsence"), ("portfolioGroupId", "portfolioAbsence")):
                    check(f"{f['id']} {r['bbl']} {gid}: grouped or absent, never both",
                          (r[gid] is None) != (r[ab] is None) or (r[gid] is None and r[ab] is None), f"{r}")
    return finish()


if __name__ == "__main__":
    sys.exit(main())
