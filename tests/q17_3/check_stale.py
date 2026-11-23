"""Check Q17.3 (is the lot's latest registration older than its latest deed?) against the frozen source.

Each fixture case is re-derived from the source (tests/q17_3/expected.sql): the deeds recorded on the latest date (ties all returned) and the latest
registration date, with the answer derived from them. The graph lookup (tests/q17_3/lookup.cypher) must give the same deeds, dates, amounts, the
not-a-sale flag (amount 0, CORRD or CONDEED) and the answer, and the answer must equal the fixture. Any failure or error is a failure.
Run: uv run python tests/q17_3/check_stale.py
"""

import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from q17_support import check, connect, finish, graph_session, older_than_deed, source_latest  # noqa: E402


def main() -> int:
    fx = yaml.safe_load((HERE / "fixtures.yaml").read_text())
    lookup = (HERE / "lookup.cypher").read_text()
    driver, pg = connect()
    with driver, pg, graph_session(driver) as s, pg.cursor() as cur:
        for f in fx["cases"]:
            label = f["bbl"]
            src = source_latest(cur, f["bbl"])
            r = s.run(lookup, bbl=f["bbl"]).single()
            check(f"{label}: the lot is in the graph", r is not None)
            if r is None:
                continue
            got = {d["documentId"]: d for d in r["latestDeeds"]}
            check(f"{label}: latest deeds equal the fixture", sorted(got) == sorted(f["deeds"]), f"graph {sorted(got)}")
            check(f"{label}: latest deeds equal the source", sorted(got) == sorted(src["deeds"]), f"graph {len(got)} vs source {len(src['deeds'])}")
            for doc, d in src["deeds"].items():
                x = got.get(doc)
                if x is not None:
                    check(f"{label} {doc}: type, recorded date, amount and not-a-sale flag equal the source",
                          (x["docType"], str(x["recordedDate"]), x["amount"], x["notASale"])
                          == (d["type"], d["recorded"], d["amount"], d["amount"] == 0 or d["type"] in ("CORRD", "CONDEED")))
            check(f"{label}: latest registration date equals the source",
                  (str(r["latestRegistered"]) if r["latestRegistered"] else None) == src["latestRegistered"], f"graph {r['latestRegistered']}")
            check(f"{label}: older-than-deed equals the source", r["olderThanDeed"] == older_than_deed(src), f"graph {r['olderThanDeed']}")
            check(f"{label}: older-than-deed equals the fixture", r["olderThanDeed"] == f["older_than_deed"], f"graph {r['olderThanDeed']}")
    return finish()


if __name__ == "__main__":
    sys.exit(main())
