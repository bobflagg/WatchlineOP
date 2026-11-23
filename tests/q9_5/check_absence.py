"""Check the reason a lot is in no Owner Portfolio (Q9.5) against the pinned BOR release. Read-only everywhere.

1. Each fixture is re-derived from the release (bbl_status.csv), so a stale fixture fails.
2. Each fixture lot is looked up in the graph with tests/q9_5/lookup.cypher.
3. Totals over the lots in the graph: reasons by detail code match the release; each detail code has its release top-level
   reason; no lot is both in a portfolio and absent; lots with neither are exactly those the release has no row for.

Any failure or error is a failure; nothing is skipped. Exit code 0 only if every check passes.
Run: uv run python tests/q9_5/check_absence.py
"""

import os
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from bor_support import check, connect, finish, group_layer, load_fixtures, status_rows  # noqa: E402

LAYER = "owner_portfolio"


def main() -> int:
    driver, pg, release = connect()
    pg.close()
    fixtures = load_fixtures(HERE / "fixtures.yaml")
    lookup = (HERE / "lookup.cypher").read_text()
    _, _, group_of = group_layer(release, LAYER)
    wanted = {f["bbl"] for f in fixtures["lots"]} | {f["bbl"] for f in fixtures["absent_from_graph"]}
    status = {r["bbl"]: r for r in status_rows(release, wanted, LAYER)}

    with driver, driver.session(database=os.environ["NEO4J_DATABASE"], default_access_mode="READ") as session:
        for f in fixtures["lots"]:
            bbl = f["bbl"]
            row = status.get(bbl)
            absent = row is not None and row["status"] in ("not_in_group", "excluded_from_footprint")
            derived = ({"portfolioAbsence": row["top_level_reason"], "portfolioAbsenceDetail": row["reason_code"]} if absent
                       else {"portfolioAbsence": None, "portfolioAbsenceDetail": None})
            expected = {"portfolioAbsence": f["portfolioAbsence"], "portfolioAbsenceDetail": f["portfolioAbsenceDetail"]}
            check(f"{bbl} fixture matches release", derived == expected, f"release says {derived}")
            rec = session.run(lookup, bbl=bbl).single()
            got = {"portfolioAbsence": rec["portfolioAbsence"], "portfolioAbsenceDetail": rec["portfolioAbsenceDetail"]} if rec else None
            check(f"{bbl} graph matches fixture", got == expected, f"graph has {got}")
            check(f"{bbl} is in a portfolio exactly when it has no reason and a rental membership",
                  rec is not None and (rec["groupId"] is not None) == (bbl in group_of))
        for f in fixtures["absent_from_graph"]:
            row = status.get(f["bbl"])
            check(f"{f['bbl']} is in the release as not_in_group", bool(row) and row["status"] == "not_in_group")
            check(f"{f['bbl']} has no Lot in the graph", session.run(lookup, bbl=f["bbl"]).single() is None)

        lots = {r["bbl"] for r in session.run("MATCH (l:Lot) RETURN l.bbl AS bbl")}
        by_detail, in_group, with_row, top_of = Counter(), 0, set(), {}
        statuses = Counter()
        for r in status_rows(release, None, LAYER):
            statuses[r["status"]] += 1
            if r["bbl"] not in lots:
                continue
            with_row.add(r["bbl"])
            if r["status"] == "in_group":
                in_group += 1
            else:
                by_detail[r["reason_code"]] += 1
                top_of[r["reason_code"]] = r["top_level_reason"]
        t = fixtures["totals"]
        check("release: lots in a portfolio (all lots) match fixture", statuses["in_group"] == t["release_lots_in_portfolio"], f"{statuses['in_group']}")
        check("release: lots excluded from the footprint match fixture", statuses["excluded_from_footprint"] == t["release_lots_excluded_from_footprint"])
        check("release: detail codes in the layer match fixture", len(top_of) == t["detail_codes_in_layer"], f"{len(top_of)}: {sorted(top_of)}")
        check("release: every rental lot in a portfolio is a Lot in the graph", in_group == t["release_lots_in_portfolio"], f"{in_group} of {t['release_lots_in_portfolio']}")

        g = session.run("MATCH (l:Lot) WHERE l.portfolioAbsenceDetail IS NOT NULL "
                        "RETURN l.portfolioAbsenceDetail AS detail, collect(DISTINCT l.portfolioAbsence) AS tops, count(l) AS n").data()
        check("graph: reasons by detail code match release", {r["detail"]: r["n"] for r in g} == dict(by_detail), f"{ {r['detail']: r['n'] for r in g} }")
        check("graph: each detail code has the release's top-level reason",
              all(r["tops"] == [top_of[r["detail"]]] for r in g), f"{[r for r in g if r['tops'] != [top_of.get(r['detail'])]]}")
        k = session.run("MATCH (l:Lot) WHERE (l.portfolioAbsence IS NULL) <> (l.portfolioAbsenceDetail IS NULL) RETURN count(l) AS n").single()["n"]
        check("graph: a lot has both reason levels or neither", k == 0, f"{k} lots")
        both = session.run("MATCH (l:Lot)-[:IN_PORTFOLIO]->() WHERE l.portfolioAbsence IS NOT NULL RETURN count(l) AS n").single()["n"]
        check("graph: no lot is both in a portfolio and absent", both == 0, f"{both} lots")
        neither = session.run("MATCH (l:Lot) WHERE NOT (l)-[:IN_PORTFOLIO]->() AND l.portfolioAbsence IS NULL RETURN l.bbl AS bbl").data()
        check("graph: lots with neither a portfolio nor a reason are exactly those the release has no row for",
              {r["bbl"] for r in neither} == lots - with_row, f"{len(neither)} vs {len(lots - with_row)}")
    return finish()


if __name__ == "__main__":
    sys.exit(main())
