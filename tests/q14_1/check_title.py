"""Check Q14.1 (deeds supporting the title holder of a lot on a date) against the frozen source.

Each fixture case is re-derived from the source (tests/q14_1/expected.sql), looked up with tests/q14_1/lookup.cypher and compared: the supporting
documents (ties all returned), their dates, amount, type, flags (document date absent, recorded after the date, confirmatory) and grantee names.
Document ids equal the fixture. Names are entities; a person's name is never printed. Any failure or error is a failure.
Run: uv run python tests/q14_1/check_title.py
"""

import os
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from q14_support import check, connect, finish, source_title  # noqa: E402


def main() -> int:
    fx = yaml.safe_load((HERE / "fixtures.yaml").read_text())
    lookup = (HERE / "lookup.cypher").read_text()
    driver, pg = connect()
    with driver, pg, driver.session(database=os.environ["NEO4J_DATABASE"], default_access_mode="READ") as s, pg.cursor() as cur:
        for f in fx["cases"]:
            label = f"{f['bbl']} {f['date']} [{f['basis']}]"
            src = source_title(cur, f["bbl"], f["date"], f["basis"])
            rows = s.run(lookup, bbl=f["bbl"], date=f["date"], basis=f["basis"]).data()
            got = {r["documentId"]: r for r in rows}
            check(f"{label}: supporting deeds equal the fixture", sorted(got) == sorted(f["deeds"]), f"graph {sorted(got)}")
            check(f"{label}: supporting deeds equal the source", sorted(got) == sorted(src), f"graph {len(got)} vs source {len(src)}")
            for doc, r in got.items():
                d = src.get(doc)
                if d is None:
                    continue
                check(f"{label} {doc}: type, dates and amount equal the source",
                      (r["docType"], str(r["docDate"]) if r["docDate"] else None, str(r["recordedDate"]), r["amount"])
                      == (d["type"], d["docdate"], d["recorded"], d["amount"]))
                check(f"{label} {doc}: flags equal the source",
                      (r["docDateAbsent"], r["recordedAfterDate"], r["confirmatory"]) == (d["docDateAbsent"], d["recordedAfterDate"], d["confirmatory"]))
                names = {g["name"] for g in r["grantees"] if g and g["name"]}
                check(f"{label} {doc}: grantees equal the source", names == d["grantees"], f"graph {len(names)} vs source {len(d['grantees'])}")
                if "recorded_after_date" in f:
                    check(f"{label} {doc}: recorded-after-date equals the fixture", r["recordedAfterDate"] == f["recorded_after_date"])
    return finish()


if __name__ == "__main__":
    sys.exit(main())
