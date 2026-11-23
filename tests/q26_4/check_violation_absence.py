"""Check Q26.4 (does the graph hold any violation for the lot, and what does none mean?) against the frozen source. Read-only everywhere.
Outcome per lot: present (graph holds violations), none-in-snapshot (registered lot, none), not-loaded (lot not registered: violations are not
loaded, even where the source holds some). Each fixture is re-derived from hpd_violations and hpd_registrations. Any failure or error is a failure.
Run: uv run python tests/q26_4/check_violation_absence.py
"""

import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from q26_support import check, connect, finish, load_fixtures, source_missing, source_violations  # noqa: E402


def outcome(registered: bool, n: int) -> str:
    return "not-loaded" if not registered else ("present" if n else "none-in-snapshot")


def main() -> int:
    driver, pg, _release = connect()
    fx = load_fixtures(HERE / "fixtures.yaml")
    q = (HERE / "lookup.cypher").read_text()
    with driver, pg, pg.cursor() as cur, driver.session(database=os.environ["NEO4J_DATABASE"], default_access_mode="READ") as s:
        for f in fx["cases"]:
            b = f["bbl"]
            reg = source_missing(cur, b)["hpdRegistered"]
            src = source_violations(cur, b)
            check(f"{b}: fixture equals the source", outcome(reg, src["loadable"]) == f["outcome"], f"source {reg} {src}")
            r = s.run(q, bbl=b).single()
            check(f"{b}: the lot is in the graph", r is not None)
            if r is None:
                continue
            check(f"{b}: graph outcome equals the fixture", outcome(r["loadedScope"], r["violations"]) == f["outcome"], str(dict(r)))
            check(f"{b}: graph count equals the loadable source count", r["violations"] == src["loadable"], f"graph {r['violations']} vs {src['loadable']}")
            if f["outcome"] == "not-loaded" and src["total"]:
                check(f"{b}: source holds violations the graph does not (not-loaded is not none)", r["violations"] == 0 and src["total"] > 0)
    return finish()


if __name__ == "__main__":
    sys.exit(main())
