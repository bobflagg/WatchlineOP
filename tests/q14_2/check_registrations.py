"""Check Q14.2 (HPD registrations of a lot's buildings and their status on a date, with owner contacts) against the frozen source.

Each fixture case is re-derived from the source (tests/q14_2/expected.sql), looked up with tests/q14_2/lookup.cypher and compared per
(BIN, registrationid): the dates, the status, the corporate owner name keys (rule N3) and whether an individual or joint owner is recorded.
The registration count and the statuses equal the fixture. Any failure or error is a failure. Run: uv run python tests/q14_2/check_registrations.py
"""

import os
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from q14_support import check, connect, finish, source_registrations  # noqa: E402


def main() -> int:
    fx = yaml.safe_load((HERE / "fixtures.yaml").read_text())
    lookup = (HERE / "lookup.cypher").read_text()
    driver, pg = connect()
    with driver, pg, driver.session(database=os.environ["NEO4J_DATABASE"], default_access_mode="READ") as s, pg.cursor() as cur:
        for f in fx["cases"]:
            label = f"{f['bbl']} {f['date']}"
            src = source_registrations(cur, f["bbl"], f["date"])
            rows = s.run(lookup, bbl=f["bbl"], date=f["date"]).data()
            got = {(r["bin"], r["registrationId"]): r for r in rows}
            check(f"{label}: registrations equal the source", sorted(got) == sorted(src), f"graph {len(got)} vs source {len(src)}")
            check(f"{label}: registration count equals the fixture", len(got) == f["registrations"], f"graph {len(got)}")
            check(f"{label}: statuses equal the fixture",
                  {f"{b}|{i}": r["status"] for (b, i), r in got.items()} == f["status"], str({k: r["status"] for k, r in got.items()}))
            for key, r in got.items():
                d = src.get(key)
                if d is None:
                    continue
                check(f"{label} {key}: dates and status equal the source",
                      (str(r["lastRegistered"]) if r["lastRegistered"] else None, str(r["registrationEnd"]) if r["registrationEnd"] else None, r["status"])
                      == (d["lastRegistered"], d["registrationEnd"], d["status"]))
                owners = [o for o in r["owners"] if o]
                keys = {o["nameKey"] for o in owners if o["contactType"] == "CorporateOwner" and o["nameKey"]}
                check(f"{label} {key}: corporate owner keys equal the source", keys == d["corporateKeys"], f"graph {len(keys)} vs source {len(d['corporateKeys'])}")
                ind = any(o["contactType"] in ("IndividualOwner", "JointOwner") for o in owners)
                check(f"{label} {key}: individual owner flag equals the source", ind == d["hasIndividualOwner"])
                if "has_individual_owner" in f:
                    check(f"{label} {key}: individual owner flag equals the fixture", ind == f["has_individual_owner"])
    return finish()


if __name__ == "__main__":
    sys.exit(main())
