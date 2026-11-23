"""Check the reason a lot is in no Operational Network (Q8.4) against the pinned BOR release. Read-only everywhere.

1. Each fixture is re-derived from the release (bbl_status.csv), so a stale fixture fails.
2. Each fixture lot is looked up in the graph with tests/q8_4/lookup.cypher.
3. Totals over the lots in the graph: reasons by detail code match the release and the fixtures; every lot has a
   network or a reason or neither (never both); the lots with neither are exactly those the release has no row for.

Any failure or error is a failure; nothing is skipped. Exit code 0 only if every check passes.
Run: uv run python tests/q8_4/check_absence.py
"""

import os
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from bor_support import check, connect, finish, load_fixtures, network_layer, status_rows  # noqa: E402


def main() -> int:
    driver, pg, release = connect()
    pg.close()
    fixtures = load_fixtures(HERE / "fixtures.yaml")
    lookup = (HERE / "lookup.cypher").read_text()
    _, _, group_of = network_layer(release)
    wanted = {f["bbl"] for f in fixtures["lots"]} | {f["bbl"] for f in fixtures["absent_from_graph"]}
    status = {r["bbl"]: r for r in status_rows(release, wanted)}

    with driver, driver.session(database=os.environ["NEO4J_DATABASE"], default_access_mode="READ") as session:
        for f in fixtures["lots"]:
            bbl = f["bbl"]
            row = status.get(bbl)
            derived = ({"networkAbsence": row["top_level_reason"] or None, "networkAbsenceDetail": row["reason_code"] or None}
                       if row and row["status"] == "not_in_group" else {"networkAbsence": None, "networkAbsenceDetail": None})
            expected = {"networkAbsence": f["networkAbsence"], "networkAbsenceDetail": f["networkAbsenceDetail"]}
            check(f"{bbl} fixture matches release", derived == expected, f"release says {derived}")
            rec = session.run(lookup, bbl=bbl).single()
            got = {"networkAbsence": rec["networkAbsence"], "networkAbsenceDetail": rec["networkAbsenceDetail"]} if rec else None
            check(f"{bbl} graph matches fixture", got == expected, f"graph has {got}")
            check(f"{bbl} is in a network exactly when it has no reason and a status row says in_group",
                  rec is not None and (rec["groupId"] is not None) == (bbl in group_of))
        for f in fixtures["absent_from_graph"]:
            row = status.get(f["bbl"])
            check(f"{f['bbl']} is in the release as not_in_group", bool(row) and row["status"] == "not_in_group")
            check(f"{f['bbl']} has no Lot in the graph", session.run(lookup, bbl=f["bbl"]).single() is None)

        # totals over the lots in the graph
        lots = {r["bbl"] for r in session.run("MATCH (l:Lot) RETURN l.bbl AS bbl")}
        by_detail, in_group, with_row = Counter(), 0, set()
        top_of = {}
        for r in status_rows(release):
            if r["bbl"] not in lots:
                continue
            with_row.add(r["bbl"])
            if r["status"] == "in_group":
                in_group += 1
            else:
                by_detail[r["reason_code"]] += 1
                top_of[r["reason_code"]] = r["top_level_reason"]
        t = fixtures["totals"]
        check("release: lots with a reason match fixture", sum(by_detail.values()) == t["lots_with_reason"], f"{sum(by_detail.values())} vs {t['lots_with_reason']}")
        check("release: lots in a network match fixture", in_group == t["lots_in_network"], f"{in_group} vs {t['lots_in_network']}")
        check("release: lots with no status row match fixture", len(lots) - len(with_row) == t["lots_with_neither"], f"{len(lots) - len(with_row)} vs {t['lots_with_neither']}")
        check("release: reasons by detail code match fixture", dict(by_detail) == t["by_detail"], f"{dict(by_detail)}")

        g = session.run("MATCH (l:Lot) WHERE l.networkAbsenceDetail IS NOT NULL "
                        "RETURN l.networkAbsenceDetail AS detail, collect(DISTINCT l.networkAbsence) AS tops, count(l) AS n").data()
        check("graph: reasons by detail code match release", {r["detail"]: r["n"] for r in g} == dict(by_detail))
        check("graph: each detail code has the release's top-level reason",
              all(r["tops"] == [top_of[r["detail"]]] for r in g), f"{[r for r in g if r['tops'] != [top_of.get(r['detail'])]]}")
        k = session.run("MATCH (l:Lot) WHERE l.networkAbsence IS NOT NULL AND l.networkAbsenceDetail IS NULL RETURN count(l) AS n").single()["n"]
        check("graph: a lot with a top-level reason also has a detail code", k == 0, f"{k} lots")
        both = session.run("MATCH (l:Lot)-[:IN_NETWORK]->() WHERE l.networkAbsence IS NOT NULL RETURN count(l) AS n").single()["n"]
        check("graph: no lot is both in a network and absent", both == 0, f"{both} lots")
        neither = session.run("MATCH (l:Lot) WHERE NOT (l)-[:IN_NETWORK]->() AND l.networkAbsence IS NULL RETURN l.bbl AS bbl").data()
        check("graph: lots with neither a network nor a reason are exactly those the release has no row for",
              {r["bbl"] for r in neither} == lots - with_row, f"{len(neither)} vs {len(lots - with_row)}")

    return finish()


if __name__ == "__main__":
    sys.exit(main())
