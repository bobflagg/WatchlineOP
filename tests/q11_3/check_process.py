"""Check Q11.3 (the DOS process contact of an entity and the hub count of its address) against the frozen source. Read-only on both databases.

Each fixture entity is re-derived from the source with tests/q11_3/expected.sql, looked up in the graph with lookup.cypher and compared:
record ids, filing dates, the presence of a process name (the name itself is never printed), process address and ZIP, and the hub count.
Any failure or error is a failure. Run: uv run python tests/q11_3/check_process.py
"""

import os
import sys
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
    driver = GraphDatabase.driver(os.environ["NEO4J_URI"], auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]))
    with driver, driver.session(database=os.environ["NEO4J_DATABASE"], default_access_mode="READ") as session:
        with psycopg.connect(os.environ["JUSTFIX_DATABASE_URL"]) as pg:
            pg.read_only = True
            with pg.cursor() as cur:
                for e in fx["entities"]:
                    key = n3(e["name"])
                    cur.execute(expected, {"key": key})
                    src = [{"dosId": int(r[0]), "filed": str(r[1]), "hasProcessName": bool(r[2]), "street": r[3], "zip5": r[4] or None,
                            "entities": int(r[5])} for r in cur.fetchall()]
                    check(f"{e['name']}: source matches fixture", src == e["records"], f"source {len(src)} records")
                    rows = [r for r in session.run(lookup, nameKey=key).data() if r["dosId"] is not None]
                    got = [{"dosId": int(r["dosId"]), "filed": str(r["filingDate"]), "hasProcessName": r["processName"] is not None,
                            "street": r["processAddress"], "zip5": (r["processZip"] or "")[:5] or None, "entities": r["entities"]} for r in rows]
                    check(f"{e['name']}: graph matches fixture", got == e["records"], f"graph {len(got)} records")
    failed = results.count(False)
    print(f"{len(results) - failed}/{len(results)} checks passed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
