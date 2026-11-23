"""Check Q21.2 (share of a group's open violations held by its top 3 lots) against the pinned BOR release and the frozen source.
Run: uv run python tests/q21_2/check_concentration.py
"""

import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from bor_support import check, connect, finish, load_fixtures  # noqa: E402
from q21_support import TOP, concentration, lot_figures, members  # noqa: E402


def main() -> int:
    driver, pg, release = connect()
    fx = load_fixtures(HERE / "fixtures.yaml")
    with driver, pg, driver.session(database=os.environ["NEO4J_DATABASE"], default_access_mode="READ") as s:
        for g in fx["groups"]:
            exp = concentration(lot_figures(pg, members(release, g["layer"], g["groupId"])))
            r = s.run((HERE / f"lookup_{g['layer']}.cypher").read_text(), groupId=g["groupId"], top=TOP).single()
            tag = g["groupId"]
            check(f"{tag}: member lots, lots with open violations, sum and top-3 count equal the source",
                  r is not None and (r["memberLots"], r["lotsWithOpen"], r["sumOpen"], r["topOpen"]) == (exp["memberLots"], exp["lotsWithOpen"], exp["sumOpen"], exp["topOpen"]),
                  f"{r and dict(r)} vs {exp}")
            check(f"{tag}: share is null with no open violation, else top / sum",
                  r is not None and ((r["topShare"] is None) if exp["topShare"] is None else abs(r["topShare"] - exp["topShare"]) < 1e-9))
            check(f"{tag}: distinct open violations never exceed the sum of lot counts", r is not None and r["distinctOpen"] <= r["sumOpen"])
    return finish()


if __name__ == "__main__":
    sys.exit(main())
