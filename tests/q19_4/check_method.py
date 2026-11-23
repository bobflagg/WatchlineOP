"""Check that stage precision stays a method property (Q19.4) against the pinned BOR release. Read-only everywhere.

1. Each fixture stage's `evaluated` flag is re-derived from method_metrics.csv (a numeric precision exists), so a stale fixture fails.
2. The graph returns the stage codes of a portfolio's links (tests/q19_4/lookup.cypher) and they equal the fixture.
3. No link, landlord, lot or group in the graph stores a precision, probability or confidence property (it is stated per stage at
   answer time, never per link).

Any failure or error is a failure; nothing is skipped. Exit code 0 only if every check passes.
Run: uv run python tests/q19_4/check_method.py
"""

import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from bor_support import check, connect, finish, load_fixtures  # noqa: E402


def main() -> int:
    driver, pg, release = connect()
    pg.close()
    fixtures = load_fixtures(HERE / "fixtures.yaml")
    lookup = (HERE / "lookup.cypher").read_text()

    evaluated = {}
    for r in release.rows("method_metrics"):
        if r["precision"].strip():
            evaluated[r["stage"]] = True
        else:
            evaluated.setdefault(r["stage"], False)
    for f in fixtures["stages"]:
        check(f"{f['stage']}: fixture evaluated flag matches release", evaluated.get(f["stage"]) == f["evaluated"], f"release says {evaluated.get(f['stage'])}")

    with driver, driver.session(database=os.environ["NEO4J_DATABASE"], default_access_mode="READ") as session:
        for f in fixtures["portfolios"]:
            got = sorted(r["stage"] for r in session.run(lookup, groupId=f["groupId"]))
            check(f"{f['groupId']}: stage codes match fixture", got == sorted(set(f["stages"])), f"graph has {got}")
        bad = session.run("""
            MATCH ()-[k]->() WHERE type(k) STARTS WITH 'CONNECTED_BY' AND any(p IN keys(k) WHERE toLower(p) CONTAINS 'precision' OR toLower(p) CONTAINS 'probab' OR toLower(p) CONTAINS 'confidence')
            RETURN count(k) AS n""").single()["n"]
        check("graph: no link stores a precision, probability or confidence", bad == 0, f"{bad} links")
        bad = session.run("""
            MATCH (n) WHERE (n:Landlord OR n:Lot OR n:OwnerPortfolio OR n:OperationalNetwork)
              AND any(p IN keys(n) WHERE toLower(p) CONTAINS 'precision' OR toLower(p) CONTAINS 'probab')
            RETURN count(n) AS n""").single()["n"]
        check("graph: no landlord, lot or group stores a precision or probability", bad == 0, f"{bad} nodes")
    return finish()


if __name__ == "__main__":
    sys.exit(main())
