"""Check Q11.2 (HPD-recorded parties alongside an entity, by role) against the frozen source. Read-only on both databases.

Each fixture entity is re-derived from the source with tests/q11_2/expected.sql (registrations, own and other contacts by type), looked up
in the graph with lookup.cypher and compared: registration count, own roles, other roles and the affiliation-type counts from the fixture
type_map. Every contact type the graph holds must be in the type_map. Person names are never printed. Any failure or error is a failure.
Run: uv run python tests/q11_2/check_roles.py
"""

import os
import sys
from collections import Counter
from pathlib import Path

import psycopg
import yaml
from dotenv import load_dotenv
from neo4j import GraphDatabase

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "src"))
from watchline.compare import n3  # noqa: E402

REQUIRED_ENV = ("JUSTFIX_DATABASE_URL", "NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD", "NEO4J_DATABASE")
results = []


def check(name, ok, detail=""):
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  ({detail})" if detail and not ok else ""))


def main() -> int:
    load_dotenv(ROOT / ".env")
    missing = [k for k in REQUIRED_ENV if not os.environ.get(k)]
    if missing:
        print(f"missing in .env: {', '.join(missing)}", file=sys.stderr)
        return 1
    fx = yaml.safe_load((HERE / "fixtures.yaml").read_text())
    lookup = (HERE / "lookup.cypher").read_text()
    expected = (HERE / "expected.sql").read_text()
    tmap = fx["type_map"]
    driver = GraphDatabase.driver(os.environ["NEO4J_URI"], auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]))
    with driver, driver.session(database=os.environ["NEO4J_DATABASE"], default_access_mode="READ") as session:
        types = {r["t"] for r in session.run("MATCH (c:Contact) RETURN DISTINCT c.contactType AS t")}
        check("every contact type in the graph has an affiliation type", types <= set(tmap), f"unmapped {sorted(types - set(tmap))}")
        with psycopg.connect(os.environ["JUSTFIX_DATABASE_URL"]) as pg:
            pg.read_only = True
            with pg.cursor() as cur:
                for e in fx["entities"]:
                    key = n3(e["name"])
                    cur.execute(expected, {"key": key})
                    own, oth, regs = Counter(), Counter(), set()
                    for rid, typ, is_own, n in cur.fetchall():
                        regs.add(rid)
                        (own if is_own else oth)[typ] += n
                    rows = session.run(lookup, nameKey=key).data()
                    g_own, g_oth = Counter(), Counter()
                    for r in rows:
                        for t in r["givenTypes"]:
                            g_own[t] += 1
                        for o in r["others"]:
                            g_oth[o["contactType"]] += 1
                    check(f"{e['name']}: registrations match source and fixture", len(rows) == len(regs) == e["registrations"],
                          f"graph {len(rows)}, source {len(regs)}, fixture {e['registrations']}")
                    check(f"{e['name']}: own roles match source and fixture", dict(g_own) == dict(own) == e["own"], f"graph {dict(g_own)}")
                    check(f"{e['name']}: other roles match source and fixture", dict(g_oth) == dict(oth) == e["others"], f"graph {dict(g_oth)}")
                    by = Counter({"ownership": 0, "management": 0, "other": 0})
                    for t, n in g_oth.items():
                        by[tmap[t]] += n
                    check(f"{e['name']}: affiliation counts match fixture", dict(by) == e["by_affiliation"], f"graph {dict(by)}")
    failed = results.count(False)
    print(f"{len(results) - failed}/{len(results)} checks passed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
