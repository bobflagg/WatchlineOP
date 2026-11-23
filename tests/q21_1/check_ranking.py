"""Check Q21.1 (open violations by class and rate per unit, ranked, for each lot of a group) against the pinned BOR release and the frozen source.

Members come from the release and violations/units from the source (tests/q21_1/expected.sql); the graph lookup must return the same lots, class counts, units,
rate (null for 0 or absent units) and the rank order. Any failure or error is a failure. Run: uv run python tests/q21_1/check_ranking.py
"""

import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from bor_support import check, connect, finish, load_fixtures  # noqa: E402
from q21_support import lot_figures, members, ranked  # noqa: E402


def main() -> int:
    driver, pg, release = connect()
    fx = load_fixtures(HERE / "fixtures.yaml")
    with driver, pg, driver.session(database=os.environ["NEO4J_DATABASE"], default_access_mode="READ") as s:
        for g in fx["groups"]:
            q = (HERE / f"lookup_{g['layer']}.cypher").read_text()
            lots = members(release, g["layer"], g["groupId"])
            figs = lot_figures(pg, lots)
            rows = s.run(q, groupId=g["groupId"]).data()
            tag = g["groupId"]
            check(f"{tag}: member lots equal the release ({len(lots)})", sorted(r["bbl"] for r in rows) == lots, f"{len(rows)} rows")
            by = {r["bbl"]: r for r in rows}
            bad = [b for b in lots if b in by and (by[b]["open"], by[b]["classA"], by[b]["classB"], by[b]["classC"], by[b]["classI"], by[b]["unitsRes"])
                   != (figs[b]["open"], figs[b]["A"], figs[b]["B"], figs[b]["C"], figs[b]["I"], figs[b]["units"])]
            check(f"{tag}: open counts by class and units equal the source", not bad, str(bad[:3]))
            bad = [b for b in by if (by[b]["rate"] is None) != (figs[b]["rate"] is None) or (figs[b]["rate"] is not None and abs(by[b]["rate"] - figs[b]["rate"]) > 1e-9)]
            check(f"{tag}: rate is null for 0 or absent units, else open / units", not bad, str(bad[:3]))
            check(f"{tag}: rows are ranked by rate, then open count", [r["bbl"] for r in rows] == ranked(figs))
            check(f"{tag}: class counts add to the open count", all(r["classA"] + r["classB"] + r["classC"] + r["classI"] == r["open"] for r in rows))
    return finish()


if __name__ == "__main__":
    sys.exit(main())
