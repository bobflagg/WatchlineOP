"""Check Q12.2 (deeds for the lots of a lot's Owner Portfolio, counted once each) against the pinned BOR release and the frozen source.

1. Each fixture lot's portfolio id and rental member lots are re-derived from the release (groups.csv, group_bbls.csv).
2. The deeds on those lots and period are re-derived from the source (tests/q12_1/expected.sql) and compared with the graph lookup:
   the document set, the not-a-sale count and the lots each deed covers inside the portfolio. A multi-lot deed is counted once.
Any failure or error is a failure. Run: uv run python tests/q12_2/check_portfolio_deeds.py
"""

import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from bor_support import check as bcheck, connect as bconnect, finish as bfinish, group_layer, load_fixtures  # noqa: E402
from q12_support import source_deeds  # noqa: E402


def main() -> int:
    driver, pg, release = bconnect()
    fx = load_fixtures(HERE / "fixtures.yaml")
    lookup = (HERE / "lookup.cypher").read_text()
    _, pmem, pof = group_layer(release, "owner_portfolio")
    with driver, pg, driver.session(database=os.environ["NEO4J_DATABASE"], default_access_mode="READ") as s, pg.cursor() as cur:
        for f in fx["lots"]:
            pid = pof.get(f["bbl"])
            members = sorted(pmem.get(pid, [f["bbl"]])) if pid else [f["bbl"]]
            bcheck(f"{f['bbl']}: portfolio id and lot count match the release and the fixture",
                   pid == f["portfolioId"] and len(members) == f["portfolioLots"], f"release {pid}, {len(members)} lots")
            for per in f["periods"]:
                label = f"{f['bbl']} [{per['start']}..{per['end']}]"
                src = source_deeds(cur, members, per["start"], per["end"])
                rec = s.run(lookup, bbl=f["bbl"], start=per["start"], end=per["end"]).single()
                deeds = {d["documentId"]: d for d in rec["deeds"]}
                bcheck(f"{label}: portfolio id and lots equal the release", rec["portfolioGroupId"] == pid and sorted(rec["portfolioLots"]) == members,
                       f"graph {rec['portfolioGroupId']}, {len(rec['portfolioLots'])} lots")
                bcheck(f"{label}: deeds equal the source and the fixture", sorted(deeds) == sorted(src) and len(deeds) == per["deeds"],
                       f"graph {len(deeds)}, source {len(src)}, fixture {per['deeds']}")
                bcheck(f"{label}: not-a-sale count equals the source and the fixture",
                       sum(1 for d in deeds.values() if d["notSale"]) == sum(1 for d in src.values() if d["notSale"]) == per["not_sales"],
                       f"graph {sum(1 for d in deeds.values() if d['notSale'])}, source {sum(1 for d in src.values() if d['notSale'])}, fixture {per['not_sales']}")
                bcheck(f"{label}: each deed's covered lots equal the source (a multi-lot deed is one deed)",
                       all(sorted(deeds[k]["lots"]) == sorted(src[k]["lots"]) for k in deeds if k in src))
                if "documents" in per:
                    bcheck(f"{label}: fixture documents equal the graph", sorted(per["documents"]) == sorted(deeds))
    return bfinish()


if __name__ == "__main__":
    sys.exit(main())
