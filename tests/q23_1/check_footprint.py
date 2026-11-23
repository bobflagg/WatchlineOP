"""Check Q23.1 (registrations, buildings and lots that disclose a managing agent, by spelling) against the frozen source. Read-only on both databases.

Each fixture is re-derived from the source (tests/q23_1/expected.sql, rule N3 applied in code), then looked up in the graph with lookup.cypher.
Any failure or error is a failure. Run: uv run python tests/q23_1/check_footprint.py
"""

import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from bor_support import check, connect, finish, load_fixtures  # noqa: E402
from q23_support import agent_rows, footprint  # noqa: E402


def main() -> int:
    driver, pg, _ = connect()
    fx = load_fixtures(HERE / "fixtures.yaml")
    q = (HERE / "lookup.cypher").read_text()
    with driver, pg, driver.session(database=os.environ["NEO4J_DATABASE"], default_access_mode="READ") as s:
        for f in fx["agents"]:
            k = f["nameKey"]
            src = footprint(pg, agent_rows(pg, k))
            check(f"{k}: source footprint matches fixture", (src["registrations"], src["buildings"], src["lots"]) == (f["registrations"], f["buildings"], f["lots"]), str(src))
            if "spellings" in f:
                check(f"{k}: spellings match fixture", src["spellings"] == f["spellings"], str(src["spellings"]))
            rows = s.run(q, nameKey=k).data()
            agent = [r for r in rows if r["contactType"] == "Agent"]
            got_spell = {r["spelling"]: r["registrations"] for r in agent}
            check(f"{k}: graph Agent spellings and registrations per spelling equal the source", got_spell == src["spellings"], str(got_spell))
            check(f"{k}: rows of other contact types are reported apart, never in the Agent counts", all(r["contactType"] != "Agent" for r in rows if r not in agent))
            tot = s.run("MATCH (c:Contact {nameKey: $k, contactType: 'Agent'})<-[:HAS_CONTACT]-(r:Registration) OPTIONAL MATCH (b:Building)-[:HAS_REGISTRATION]->(r) "
                        "OPTIONAL MATCH (l:Lot)-[:HAS_BUILDING]->(b) RETURN count(DISTINCT r) AS r, count(DISTINCT b) AS b, count(DISTINCT l) AS l", k=k).single()
            check(f"{k}: distinct registrations, buildings and lots equal the source", (tot["r"], tot["b"], tot["l"]) == (src["registrations"], src["buildings"], src["lots"]), str(dict(tot)))
        for f in fx["absent"]:
            check(f"{f['nameKey']}: no rows", s.run(q, nameKey=f["nameKey"]).data() == [])
    return finish()


if __name__ == "__main__":
    sys.exit(main())
