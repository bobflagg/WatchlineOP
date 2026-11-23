"""Check Q17.1 (is the lot's registration missing?) against the frozen source.

Each fixture case is re-derived from the source (tests/q17_1/expected.sql), looked up with tests/q17_1/lookup.cypher and compared: missing, whether
the lot has rows but no usable registration, the registration and registered-building counts, and PLUTO's building count. An out-of-scope lot must be
absent. Totals: the registered lots of the graph with no registration record equal the source's lots with rows but no usable registration.
Any failure or error is a failure. Run: uv run python tests/q17_1/check_missing.py
"""

import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from q17_support import check, connect, finish, graph_session, source_missing  # noqa: E402

NO_USABLE_SOURCE = """SELECT DISTINCT r.bbl::text FROM hpd_registrations r WHERE r.bbl::text = ANY(%(bbls)s) AND NOT EXISTS (
  SELECT 1 FROM hpd_registrations x WHERE x.bbl = r.bbl AND x.bin ~ '^[1-5][0-9]{6}$' AND x.bin !~ '000000$' AND x.registrationid > 0)"""


def main() -> int:
    fx = yaml.safe_load((HERE / "fixtures.yaml").read_text())
    lookup = (HERE / "lookup.cypher").read_text()
    driver, pg = connect()
    with driver, pg, graph_session(driver) as s, pg.cursor() as cur:
        for f in fx["cases"]:
            label = f["bbl"]
            src = source_missing(cur, f["bbl"])
            r = s.run(lookup, bbl=f["bbl"]).single()
            check(f"{label}: the lot is in the graph", r is not None)
            if r is None:
                continue
            check(f"{label}: missing equals the fixture", r["missing"] == f["missing"], f"graph {r['missing']}")
            check(f"{label}: missing equals the source", r["missing"] == src["missing"])
            check(f"{label}: no-usable-registration flag equals the source", r["noUsableRegistration"] == src["noUsable"])
            check(f"{label}: registrations and registered buildings equal the source",
                  (r["registrations"], r["registeredBuildings"]) == (src["registrations"], src["registeredBuildings"]), f"graph {r['registrations']}/{r['registeredBuildings']}")
            check(f"{label}: PLUTO building count equals the source", r["plutoNumBuildings"] == src["plutoNumBuildings"])
            if "registrations" in f:
                check(f"{label}: registrations equal the fixture", r["registrations"] == f["registrations"], f"graph {r['registrations']}")
            if "no_usable_registration" in f:
                check(f"{label}: no-usable-registration flag equals the fixture", r["noUsableRegistration"] == f["no_usable_registration"])
        for f in fx["absent"]:
            check(f"{f['bbl']}: an out-of-scope lot is absent from the graph", s.run(lookup, bbl=f["bbl"]).single() is None)
        graph_bbls = [r["bbl"] for r in s.run("MATCH (l:Lot) WHERE l.hpdRegistered AND NOT (l)-[:HAS_BUILDING]->(:Building)-[:HAS_REGISTRATION]->(:Registration) RETURN l.bbl AS bbl")]
        cur.execute("SELECT array_agg(DISTINCT bbl::text) FROM hpd_registrations")
        registered = (cur.fetchone()[0]) or []
        in_graph = {r["bbl"] for r in s.run("MATCH (l:Lot) WHERE l.hpdRegistered RETURN l.bbl AS bbl")}
        cur.execute(NO_USABLE_SOURCE, {"bbls": sorted(in_graph & set(registered))})
        src_bbls = sorted(r[0] for r in cur.fetchall())
        check("total: registered lots without a registration record equal the source's lots with no usable registration",
              sorted(graph_bbls) == src_bbls, f"graph {len(graph_bbls)} vs source {len(src_bbls)}")
    return finish()


if __name__ == "__main__":
    sys.exit(main())
