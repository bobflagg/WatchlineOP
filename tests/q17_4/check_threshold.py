"""Check Q17.4 (does the lot meet the registration dataset's 3-unit threshold?) against the frozen source.

Each fixture case is re-derived from the source (tests/q17_4/expected.sql): PLUTO's unit count (kept as recorded; 0 means none recorded) and year
built (0 is unknown), with the outcome derived against the threshold. The graph lookup (tests/q17_4/lookup.cypher) must give the same values and
outcome, and the outcome must equal the fixture. Any failure or error is a failure. Run: uv run python tests/q17_4/check_threshold.py
"""

import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from q17_support import check, connect, finish, graph_session, source_units, threshold_outcome  # noqa: E402


def main() -> int:
    fx = yaml.safe_load((HERE / "fixtures.yaml").read_text())
    lookup = (HERE / "lookup.cypher").read_text()
    driver, pg = connect()
    with driver, pg, graph_session(driver) as s, pg.cursor() as cur:
        for f in fx["cases"]:
            label = f["bbl"]
            src = source_units(cur, f["bbl"]) or {"units": None, "yearBuilt": None}
            r = s.run(lookup, bbl=f["bbl"], threshold=fx["threshold"]).single()
            check(f"{label}: the lot is in the graph", r is not None)
            if r is None:
                continue
            check(f"{label}: units equal the source", r["unitsRes"] == src["units"], f"graph {r['unitsRes']} vs source {src['units']}")
            check(f"{label}: year built equals the source", r["yearBuilt"] == src["yearBuilt"], f"graph {r['yearBuilt']}")
            check(f"{label}: outcome equals the source", r["thresholdOutcome"] == threshold_outcome(src["units"]), f"graph {r['thresholdOutcome']}")
            check(f"{label}: outcome equals the fixture", r["thresholdOutcome"] == f["outcome"], f"graph {r['thresholdOutcome']}")
            if "units" in f:
                check(f"{label}: units equal the fixture", r["unitsRes"] == f["units"])
            if "year_built" in f:
                check(f"{label}: year built equals the fixture", r["yearBuilt"] == f["year_built"])
            check(f"{label}: the threshold is {fx['threshold']}", r["threshold"] == fx["threshold"])
    return finish()


if __name__ == "__main__":
    sys.exit(main())
