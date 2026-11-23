"""Check the members of Owner Portfolios (Q9.2) against the pinned release and the frozen source. Read-only everywhere.

1. Each fixture is re-derived: lots from the release, buildings, units and missing units from the source database.
2. Each portfolio is looked up in the graph with tests/q9_2/lookup.cypher.
3. Over every portfolio, the graph's lot, building and unit counts equal the source's, so a wrong edge anywhere fails.

Any failure or error is a failure; nothing is skipped. Exit code 0 only if every check passes.
Run: uv run python tests/q9_2/check_members.py
"""

import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from bor_support import check, connect, finish, group_layer, load_fixtures  # noqa: E402

KEYS = ("lots", "buildings", "units", "lotsMissingUnits")
ALL_PORTFOLIOS = """
MATCH (n:OwnerPortfolio)<-[:IN_PORTFOLIO]-(l:Lot)
WITH n, collect(l) AS lots
UNWIND lots AS lot
OPTIONAL MATCH (lot)-[:HAS_BUILDING]->(b:Building)
WITH n, lots, collect(DISTINCT b) AS buildings
RETURN n.groupId AS groupId, size(lots) AS lots, size(buildings) AS buildings,
       reduce(u = 0, x IN lots | u + coalesce(x.unitsRes, 0)) AS units,
       size([x IN lots WHERE x.unitsRes IS NULL]) AS lotsMissingUnits
"""


ALL_SQL = """
WITH m AS (SELECT * FROM unnest(%(gids)s::text[], %(bbls)s::text[]) AS t(gid, bbl)),
     b AS (SELECT m.gid, count(DISTINCT r.bin) AS buildings FROM m JOIN hpd_registrations r ON r.bbl = m.bbl
           WHERE r.bin ~ '^[1-5][0-9]{6}$' AND r.bin !~ '000000$' GROUP BY m.gid),
     u AS (SELECT m.gid, count(*) AS lots, coalesce(sum(p.unitsres), 0) AS units,
                  count(*) FILTER (WHERE p.unitsres IS NULL) AS missing
           FROM m LEFT JOIN pluto_latest p ON p.bbl = m.bbl GROUP BY m.gid)
SELECT u.gid, u.lots, coalesce(b.buildings, 0), u.units, u.missing FROM u LEFT JOIN b ON b.gid = u.gid
"""


def main() -> int:
    driver, pg, release = connect()
    fixtures = load_fixtures(HERE / "fixtures.yaml")
    expected_sql = (HERE / "expected.sql").read_text()
    lookup = (HERE / "lookup.cypher").read_text()
    groups, members, _ = group_layer(release, "owner_portfolio")

    def from_source(cur, gid):
        cur.execute(expected_sql, {"bbls": members[gid]})
        lots, buildings, units, missing = cur.fetchone()
        return {"lots": lots, "buildings": buildings, "units": int(units), "lotsMissingUnits": missing}

    with driver, driver.session(database=os.environ["NEO4J_DATABASE"], default_access_mode="READ") as session, pg.cursor() as cur:
        for f in fixtures["portfolios"] + fixtures["hub"]:
            gid = f["groupId"]
            check(f"{gid} composition matches release", groups[gid]["composition"] == f["composition"], f"release says {groups[gid]['composition']}")
            check(f"{gid} rental lot count matches release", len(members[gid]) == f["lots"], f"release lists {len(members[gid])}")
            src = from_source(cur, gid)
            rec = session.run(lookup, groupId=gid).single()
            got = {k: rec[k] for k in KEYS} if rec else None
            if "buildings" in f:
                expected = {k: f[k] for k in KEYS}
                check(f"{gid} fixture matches source", src == expected, f"source says {src}")
                check(f"{gid} graph matches fixture", got == expected, f"graph has {got}")
            else:
                check(f"{gid} graph matches source", got == src, f"graph {got} vs source {src}")
            check(f"{gid} lots in more than one counting unit are not mixed up", got is not None and got["lots"] == len(members[gid]))

        rows = {r["groupId"]: {k: r[k] for k in KEYS} for r in session.run(ALL_PORTFOLIOS)}
        check("graph: every portfolio is returned", set(rows) == set(members), f"{len(rows)} vs {len(members)}")
        # Every network against the source, in one pass: the same rules as expected.sql, grouped by network.
        gids = [g for g, bbls in members.items() for _ in bbls]
        bbls = [b for bbls in members.values() for b in bbls]
        cur.execute(ALL_SQL, {"gids": gids, "bbls": bbls})
        src_all = {gid: {"lots": lots, "buildings": buildings, "units": int(units), "lotsMissingUnits": missing}
                   for gid, lots, buildings, units, missing in cur.fetchall()}
        wrong = [g for g in members if rows.get(g) != src_all.get(g)]
        check(f"graph: all {len(members):,} portfolios match the source on lots, buildings, units and missing units",
              not wrong, f"{len(wrong)} differ, e.g. {wrong[:3]}")
    pg.close()
    return finish()


if __name__ == "__main__":
    sys.exit(main())
