"""Check Q26.2 (does the DOS active-entity snapshot hold a record for the lot's owner entity?) against the frozen source. Read-only everywhere.
Each fixture is re-derived from hpd_contacts and dos_active_corporations (rule N3), the graph lookup (tests/q26_2/lookup.cypher) must give the same
names and record counts, and the lot-level reason must equal the fixture. Any failure or error is a failure.
Run: uv run python tests/q26_2/check_dos_absence.py
"""

import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from q26_support import check, connect, finish, load_fixtures, source_dos  # noqa: E402


def graph_outcome(rows) -> tuple[dict, str | None]:
    names = {r["corporationName"]: r["dosRecords"] for r in rows if r["corporationName"]}
    if any(names.values()):
        return names, None
    return names, "no_qualifying_linkage" if names else "outside_method_input"


def main() -> int:
    driver, pg, _release = connect()
    fx = load_fixtures(HERE / "fixtures.yaml")
    q = (HERE / "lookup.cypher").read_text()
    with driver, pg, pg.cursor() as cur, driver.session(database=os.environ["NEO4J_DATABASE"], default_access_mode="READ") as s:
        for f in fx["cases"]:
            src = source_dos(cur, f["bbl"])
            check(f"{f['bbl']}: fixture reason equals the source", src["reason"] == f["reason"], f"source {src['reason']}")
            rows = s.run(q, bbl=f["bbl"]).data()
            check(f"{f['bbl']}: the lot is in the graph", bool(rows))
            names, reason = graph_outcome(rows)
            check(f"{f['bbl']}: owner names and record counts equal the source",
                  names == {k: len(v) for k, v in src["names"].items()}, f"graph {names}")
            check(f"{f['bbl']}: graph reason equals the fixture", reason == f["reason"], f"graph {reason}")
    return finish()


if __name__ == "__main__":
    sys.exit(main())
