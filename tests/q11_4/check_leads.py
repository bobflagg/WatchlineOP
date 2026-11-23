"""Check Q11.4 (derived group leads for an entity's lots) against the pinned BOR release. Read-only everywhere.

Each fixture lot is re-derived from the release (group ids, rental member counts, absence reasons from bbl_status) and compared with the
graph lookup (tests/q11_4/lookup.cypher). The set of lots per entity must equal the fixture. Any failure or error is a failure.
Run: uv run python tests/q11_4/check_leads.py
"""

import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parents[1] / "src"))
from bor_support import check, connect, finish, group_layer, load_fixtures, status_rows  # noqa: E402
from watchline.compare import n3  # noqa: E402


def main() -> int:
    driver, pg, release = connect()
    pg.close()
    fx = load_fixtures(HERE / "fixtures.yaml")
    lookup = (HERE / "lookup.cypher").read_text()
    _, pmem, pof = group_layer(release, "owner_portfolio")
    _, nmem, nof = group_layer(release, "operational_network")
    wanted = {f["bbl"] for e in fx["entities"] for f in e["lots"]}
    absence = {}
    for layer in ("operational_network", "owner_portfolio"):
        for r in status_rows(release, wanted, layer):
            if r["status"] in ("not_in_group", "excluded_from_footprint"):
                absence[(layer, r["bbl"])] = r["top_level_reason"]
    with driver, driver.session(database=os.environ["NEO4J_DATABASE"], default_access_mode="READ") as session:
        for e in fx["entities"]:
            rows = [r for r in session.run(lookup, nameKey=n3(e["name"])).data() if r["bbl"] is not None]
            got = {r["bbl"]: r for r in rows}
            check(f"{e['name']}: lots match fixture", sorted(got) == sorted(f["bbl"] for f in e["lots"]), f"graph {sorted(got)}")
            for f in e["lots"]:
                b = f["bbl"]
                n, p = nof.get(b), pof.get(b)
                rel = {"networkGroupId": n, "portfolioGroupId": p, "networkLots": len(nmem.get(n, [])), "portfolioLots": len(pmem.get(p, []))}
                if n is None:
                    rel["networkAbsence"] = absence.get(("operational_network", b))
                if p is None:
                    rel["portfolioAbsence"] = absence.get(("owner_portfolio", b))
                want = {k: v for k, v in f.items() if k != "bbl"}
                want = {k: v for k, v in want.items() if k in rel or v is None} 
                check(f"{b}: fixture matches release", all(rel.get(k) == v for k, v in want.items() if k in rel), f"release {rel}")
                r = got.get(b)
                ok = r is not None and r["networkGroupId"] == n and r["portfolioGroupId"] == p and (n is None or r["networkLots"] == len(nmem[n])) \
                    and (p is None or r["portfolioLots"] == len(pmem[p]))
                if r is not None and n is None:
                    ok = ok and r["networkAbsence"] == rel["networkAbsence"]
                if r is not None and p is None:
                    ok = ok and r["portfolioAbsence"] == rel["portfolioAbsence"]
                check(f"{b}: graph matches the release", ok)
    return finish()


if __name__ == "__main__":
    sys.exit(main())
