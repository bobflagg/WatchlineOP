"""Check Q26.3 (is the lot in each layer, and if not why?) against the pinned BOR release. Read-only everywhere.
Each fixture is re-derived from the release (bbl_status top-level reason and code; group_bbls), the graph lookup (tests/q26_3/lookup.cypher) must
agree, and a grouped lot carries no reason while an ungrouped lot always has one. Any failure or error is a failure.
Run: uv run python tests/q26_3/check_layer_absence.py
"""

import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from q26_support import NET, PORT, check, connect, finish, load_fixtures, status_rows  # noqa: E402


def release_state(release, bbl, layer):
    for r in status_rows(release, {bbl}, layer):
        return "in_group" if r["status"] == "in_group" else {"reason": r["top_level_reason"], "detail": r["reason_code"]}
    return None


def main() -> int:
    driver, pg, release = connect()
    pg.close()
    fx = load_fixtures(HERE / "fixtures.yaml")
    q = (HERE / "lookup.cypher").read_text()
    with driver, driver.session(database=os.environ["NEO4J_DATABASE"], default_access_mode="READ") as s:
        for f in fx["cases"]:
            b = f["bbl"]
            r = s.run(q, bbl=b).single()
            check(f"{b}: the lot is in the graph", r is not None)
            for layer, key, gid, ab, det in ((NET, "network", "networkGroupId", "networkAbsence", "networkAbsenceDetail"),
                                             (PORT, "portfolio", "portfolioGroupId", "portfolioAbsence", "portfolioAbsenceDetail")):
                check(f"{b} {key}: fixture equals the release", release_state(release, b, layer) == f[key], f"release {release_state(release, b, layer)}")
                if r is None:
                    continue
                got = "in_group" if r[gid] else {"reason": r[ab], "detail": r[det]}
                check(f"{b} {key}: graph equals the fixture", got == f[key], f"graph {got}")
                check(f"{b} {key}: grouped or absent, never both", (r[gid] is None) != (r[ab] is None))
    return finish()


if __name__ == "__main__":
    sys.exit(main())
