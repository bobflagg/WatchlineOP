"""Check Q24.1 (records that carry an entity name, with role, record, building, lot and basis) against the frozen source. Read-only on both databases.

Each fixture name is re-derived from the source (HPD contacts, deed parties on in-scope lots, DOS records), then looked up in the graph with lookup.cypher.
Any failure or error is a failure. Run: uv run python tests/q24_1/check_entity.py
"""

import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from q24_support import check, connect, deed_parties, finish, hpd_corporation, load_fixtures, n3  # noqa: E402
from q5_support import SOURCE_CANDIDATES  # noqa: E402


def basis(given: str, recorded: str) -> str:
    return "exact" if recorded == given.strip() else "normalized"


def main() -> int:
    fx = load_fixtures(HERE)
    q = (HERE / "lookup.cypher").read_text()
    driver, pg = connect()
    with driver, driver.session(database=os.environ["NEO4J_DATABASE"], default_access_mode="READ") as s, pg, pg.cursor() as cur:
        for f in fx["names"]:
            given, key = f["name"], n3(f["name"])
            rows = s.run(q, key=key).data()
            hpd = {(r[0], r[1], r[3], r[4]) for r in hpd_corporation(cur, key)}
            g_hpd = {(int(r["ref"]), r["role"], r["bin"], r["bbl"]) for r in rows if r["source"] == "hpd_contacts"}
            check(f"{given}: HPD registrations, roles, buildings and lots equal the source", g_hpd == hpd, f"graph {len(g_hpd)}, source {len(hpd)}")
            deeds = deed_parties(cur, [key])
            g_deed = {(r["role"], r["ref"]): set() for r in rows if r["source"] == "acris_parties"}
            for r in rows:
                if r["source"] == "acris_parties":
                    g_deed[(r["role"], r["ref"])].add(r["bbl"])
            check(f"{given}: deed grantee and grantor records and lots equal the source", {k: sorted(v) for k, v in g_deed.items()} == deeds, f"graph {len(g_deed)}, source {len(deeds)}")
            cur.execute(SOURCE_CANDIDATES, {"name": given})
            src_dos = {str(r[0]) for r in cur.fetchall()}
            g_dos = {r["ref"] for r in rows if r["source"] == "nys_corporations"}
            check(f"{given}: DOS ids in the graph are the source's (the graph holds only name-matched records)", g_dos <= src_dos and (not g_dos or g_dos == src_dos), f"graph {sorted(g_dos)}, source {sorted(src_dos)}")
            check(f"{given}: every row's name has the N3 key of the input", all(n3(r["name"]) == key for r in rows))
            bases = {basis(given, r["name"]) for r in rows}
            check(f"{given}: basis is exact or normalized for every row", bases <= {"exact", "normalized"} and bool(rows), str(bases))
            if f["name"] == "702 plaza llc":
                check(f"{given}: lower-case input is never an exact match", bases == {"normalized"}, str(bases))
            if f["name"] == "5413 PLAZA LLC":
                check(f"{given}: three sources, each with its own role", {(r["source"], r["role"]) for r in rows} >= {("hpd_contacts", "CorporateOwner"), ("acris_parties", "grantee"), ("nys_corporations", "filed entity")})
        for f in fx["absent"]:
            check(f"{f['name']}: no row", s.run(q, key=n3(f["name"])).data() == [])
    return finish()


if __name__ == "__main__":
    sys.exit(main())
