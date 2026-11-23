"""Check Q15.2 (open violations per residential unit) against the frozen source. Read-only on both databases.

Each fixture building is re-derived from the source (tests/q15_2/expected.sql): lots, PLUTO residential units, open count. The graph lookup must return
the same rows, with rate null when units are 0 or absent, and the rate equal to open / units otherwise. A BIN on several lots returns one row per lot.
Any failure or error is a failure. Run: uv run python tests/q15_2/check_rate.py
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
REQUIRED_ENV = ("JUSTFIX_DATABASE_URL", "NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD", "NEO4J_DATABASE")
SQL = "\n".join(ln for ln in (HERE / "expected.sql").read_text().splitlines() if not ln.startswith("--")).strip().rstrip(";")
results: list[bool] = []


def check(name: str, ok: bool, detail: str = "") -> None:
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
    driver = GraphDatabase.driver(os.environ["NEO4J_URI"], auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]))
    with driver, psycopg.connect(os.environ["JUSTFIX_DATABASE_URL"]) as pg, driver.session(database=os.environ["NEO4J_DATABASE"], default_access_mode="READ") as s:
        pg.read_only = True
        with pg.cursor() as cur:
            for f in fx["buildings"]:
                cur.execute(SQL, {"bin": f["bin"]})
                src = [(b, u, int(o)) for b, u, o in cur.fetchall()]
                rows = s.run(lookup, bin=f["bin"]).data()
                got = [(r["bbl"], r["unitsRes"], r["openViolations"]) for r in rows]
                check(f"{f['bin']}: lots, units and open count equal the source", got == src, f"graph {got} vs source {src}")
                ok = all((r["rate"] is None) if not r["unitsRes"] else abs(r["rate"] - r["openViolations"] / r["unitsRes"]) < 1e-9 for r in rows)
                check(f"{f['bin']}: rate is null for 0 or absent units, else open / units", ok)
                if "lots" in f:
                    check(f"{f['bin']}: one row per lot", len(rows) == f["lots"] == len(src), str(len(rows)))
                for w in f.get("rows", []):
                    r = next((x for x in rows if x["bbl"] == w["bbl"]), None)
                    check(f"{f['bin']}/{w['bbl']}: fixture row matches", r is not None and r["unitsRes"] == w["units"] and r["openViolations"] == w["open"]
                          and (r["rate"] == w["rate"] if w["rate"] is None else abs(r["rate"] - w["rate"]) < 1e-9), str(r))
    failed = results.count(False)
    print(f"{len(results) - failed}/{len(results)} checks passed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
