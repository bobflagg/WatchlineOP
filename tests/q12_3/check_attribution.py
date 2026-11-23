"""Check Q12.3 (deeds attributable to the lot's currently registered owner, a derived name lead) against the frozen source.

Each fixture lot set is re-derived from the source with tests/q12_3/expected.sql (owners from HPD, parties from ACRIS, rule N3), looked up with
tests/q12_3/lookup.cypher and compared per (deed, lot): owner count, the not-comparable flag, grantee and grantor matches and the attributable flag.
Deed and attributable counts equal the fixture. Any failure or error is a failure. Run: uv run python tests/q12_3/check_attribution.py
"""

import os
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from q12_support import DEED_TYPES, check, connect, finish  # noqa: E402


def main() -> int:
    fx = yaml.safe_load((HERE / "fixtures.yaml").read_text())
    lookup = (HERE / "lookup.cypher").read_text()
    expected = (HERE / "expected.sql").read_text()
    driver, pg = connect()
    with driver, pg, driver.session(database=os.environ["NEO4J_DATABASE"], default_access_mode="READ") as s, pg.cursor() as cur:
        for f in fx["lots"]:
            label = f"{','.join(f['bbls'])} [{f.get('start')}..]"
            cur.execute(expected, {"bbls": f["bbls"], "types": DEED_TYPES, "start": f.get("start"), "end": None})
            src = {(doc, bbl): (int(owners), bool(g), bool(r)) for doc, bbl, owners, g, r in cur.fetchall()}
            rows = s.run(lookup, bbls=f["bbls"], start=f.get("start"), end=None).data()
            got = {(r["documentId"], r["bbl"]): (r["corporateOwners"], bool(r["granteeMatches"]), bool(r["grantorMatches"])) for r in rows}
            check(f"{label}: deed-lot pairs and matches equal the source", got == src, f"graph {len(got)} vs source {len(src)}")
            deeds = {r["documentId"] for r in rows}
            attributable = {r["documentId"] for r in rows if r["attributable"]}
            check(f"{label}: deed and attributable counts equal the fixture", len(deeds) == f["deeds"] and len(attributable) == f["attributable"],
                  f"graph {len(deeds)}/{len(attributable)}")
            check(f"{label}: attributable is exactly a grantee or grantor match",
                  all(r["attributable"] == bool(r["granteeMatches"] or r["grantorMatches"]) for r in rows))
            if "owner_not_comparable" in f:
                check(f"{label}: owner not comparable is flagged", all(r["ownerNotComparable"] == f["owner_not_comparable"] for r in rows))
            check(f"{label}: owner not comparable exactly when no corporate owner", all(r["ownerNotComparable"] == (r["corporateOwners"] == 0) for r in rows))
    return finish()


if __name__ == "__main__":
    sys.exit(main())
