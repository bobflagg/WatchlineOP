"""Check the fixture tests/agent_eval/fixtures/mice-portfolio-op-16799.yaml against the pinned BOR release, the frozen source and the graph.

Members come from the release; BINs, units, mice complaints (minor category PESTS, problem code MICE, since 2021-01-01) and mice violations (orders 569 and 869)
come from the source with the same scope as Q27.1 and Q15.1; the graph lookup must return the same buildings and counts. A stale fixture fails.
Read-only on the release, the source database and the graph. Any failure or error is a failure.
Run: uv run python tests/agent_eval/check_mice_portfolio.py
"""

import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from bor_support import check, connect, finish, load_fixtures  # noqa: E402
from q21_support import members  # noqa: E402

SCOPE = """
WITH rb AS (SELECT DISTINCT bbl FROM hpd_registrations WHERE bbl IS NOT NULL),
     rbin AS (SELECT DISTINCT bin FROM hpd_registrations WHERE bbl IS NOT NULL AND bin ~ '^[1-5][0-9]{6}$' AND bin !~ '000000$')
"""
COMPLAINTS = SCOPE + """
SELECT c.bin, count(*), count(*) FILTER (WHERE c.problemstatus = 'OPEN'), min(c.receiveddate)::date, max(c.receiveddate)::date
FROM hpd_complaints_and_problems c JOIN rb ON rb.bbl = c.bbl JOIN rbin ON rbin.bin = c.bin
WHERE c.bin = ANY(%(bins)s) AND c.minorcategory = 'PESTS' AND c.problemcode = 'MICE' AND c.receiveddate >= DATE '2021-01-01'
GROUP BY c.bin
"""
VIOLATIONS = SCOPE + """
SELECT v.bin, count(*), count(*) FILTER (WHERE v.violationstatus = 'Open')
FROM hpd_violations v JOIN rb ON rb.bbl = v.bbl JOIN rbin ON rbin.bin = v.bin
WHERE v.bin = ANY(%(bins)s) AND v.ordernumber IN ('569', '869')
GROUP BY v.bin
"""
BUILDINGS = SCOPE + "SELECT DISTINCT bbl, bin FROM hpd_registrations WHERE bbl = ANY(%(bbls)s) AND bin IN (SELECT bin FROM rbin) ORDER BY bbl, bin"


def main() -> int:
    driver, pg, release = connect()
    fx = load_fixtures(HERE / "fixtures" / "mice-portfolio-op-16799.yaml")
    gid = fx["groupId"]
    want = {b["bin"]: b for b in fx["buildings"]}
    with driver, pg, driver.session(database=os.environ["NEO4J_DATABASE"], default_access_mode="READ") as s, pg.cursor() as cur:
        lots = members(release, fx["layer"], gid)
        check(f"{gid}: member lots equal the release and the fixture", lots == sorted(b["bbl"] for b in fx["buildings"]), str(lots))
        cur.execute(BUILDINGS, {"bbls": lots})
        pairs = sorted((b, n) for b, n in cur.fetchall())
        check(f"{gid}: registered buildings of the member lots equal the fixture", pairs == sorted((b["bbl"], b["bin"]) for b in fx["buildings"]), str(pairs))
        bins = sorted(want)
        cur.execute(COMPLAINTS, {"bins": bins})
        comp = {r[0]: (int(r[1]), int(r[2]), str(r[3]), str(r[4])) for r in cur.fetchall()}
        cur.execute(VIOLATIONS, {"bins": bins})
        viol = {r[0]: (int(r[1]), int(r[2])) for r in cur.fetchall()}
        for b in fx["buildings"]:
            check(f"{b['bin']}: mice complaints, open count and dates equal the source",
                  comp.get(b["bin"]) == (b["mice_complaints"], b["mice_open"], b["first"], b["last"]), str(comp.get(b["bin"])))
            check(f"{b['bin']}: mice violations and open count equal the source", viol.get(b["bin"]) == (b["mice_violations"], b["mice_violations_open"]), str(viol.get(b["bin"])))
        t = fx["totals"]
        check("fixture totals equal the building rows", (len(fx["buildings"]), sum(1 for b in fx["buildings"] if b["mice_complaints"] > 0),
              sum(b["mice_complaints"] for b in fx["buildings"]), sum(b["mice_violations"] for b in fx["buildings"]), sum(b["mice_violations_open"] for b in fx["buildings"]))
              == (t["buildings"], t["buildings_with_mice_complaints"], t["mice_complaints"], t["mice_violations"], t["mice_violations_open"]))
        rows = s.run((HERE / "lookup_mice_portfolio.cypher").read_text(), groupId=gid).data()
        got = {r["bin"]: (r["bbl"], r["unitsRes"], r["miceComplaints"], r["miceOpen"], r["first"], r["last"], r["miceViolations"], r["miceViolationsOpen"]) for r in rows}
        exp = {b["bin"]: (b["bbl"], b["units"], b["mice_complaints"], b["mice_open"], b["first"], b["last"], b["mice_violations"], b["mice_violations_open"]) for b in fx["buildings"]}
        check(f"{gid}: the graph lookup returns the fixture buildings and counts", got == exp, f"graph {got}")
        comp_all = s.run("MATCH (op:OwnerPortfolio {groupId: $g})<-[:IN_PORTFOLIO]-(:Lot)-[:HAS_BUILDING]->(:Building)-[:HAS_PROBLEM]->(p:Problem {problemCode: 'MICE'}) "
                         "WHERE p.minorCategory <> 'PESTS' RETURN count(p) AS n", g=gid).single()["n"]
        check("no MICE problem code sits outside the PESTS minor category", comp_all == 0, str(comp_all))
    return finish()


if __name__ == "__main__":
    sys.exit(main())
