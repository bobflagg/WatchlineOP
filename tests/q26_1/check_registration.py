"""Check Q26.1 (does the HPD registration data hold a record for the lot?) against the frozen source. Read-only everywhere.
Each fixture is re-derived from the source (tests/q17_1/expected.sql), looked up with tests/q26_1/lookup.cypher and compared; an out-of-scope lot
must be absent. Any failure or error is a failure. Run: uv run python tests/q26_1/check_registration.py
"""

import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from q26_support import check, connect, finish, load_fixtures, source_missing  # noqa: E402


def main() -> int:
    driver, pg, _release = connect()
    fx = load_fixtures(HERE / "fixtures.yaml")
    q = (HERE / "lookup.cypher").read_text()
    with driver, pg, pg.cursor() as cur, driver.session(database=os.environ["NEO4J_DATABASE"], default_access_mode="READ") as s:
        for f in fx["cases"]:
            src = source_missing(cur, f["bbl"])
            check(f"{f['bbl']}: fixture equals the source", (not src["hpdRegistered"]) == (not f["present"]), f"source {src}")
            r = s.run(q, bbl=f["bbl"]).single()
            check(f"{f['bbl']}: the lot is in the graph", r is not None)
            if r is not None:
                check(f"{f['bbl']}: the graph equals the source", r["hpdRegistered"] == src["hpdRegistered"], str(dict(r)))
                reason = None if r["hpdRegistered"] else "outside_source_coverage"
                check(f"{f['bbl']}: absence reason equals the fixture", reason == f.get("reason"), f"graph {reason}")
        for f in fx["absent"]:
            check(f"{f['bbl']}: out-of-scope lot is absent from the graph", s.run(q, bbl=f["bbl"]).single() is None)
    return finish()


if __name__ == "__main__":
    sys.exit(main())
