"""Check Q15.1 (violations of a building, by class and status) against the frozen source. Read-only on both databases.

Each fixture building is re-derived from the source (tests/q15_1/expected.sql), looked up with lookup.cypher and compared by class and status,
with the oldest open inspection date. Then graph totals equal the source totals, every violation has a class, status and inspection date and a
building, and no apartment property exists. Counting unit: violations. Any failure or error is a failure.
Run: uv run python tests/q15_1/check_violations.py
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
SQL = (HERE / "expected.sql").read_text()
results: list[bool] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  ({detail})" if detail and not ok else ""))


def statements() -> tuple[str, str]:
    body = [ln for ln in SQL.splitlines() if not ln.startswith("--")]
    parts = [p.strip() for p in "\n".join(body).split(";") if p.strip()]
    return parts[0], parts[1]


def main() -> int:
    load_dotenv(ROOT / ".env")
    missing = [k for k in REQUIRED_ENV if not os.environ.get(k)]
    if missing:
        print(f"missing in .env: {', '.join(missing)}", file=sys.stderr)
        return 1
    fx = yaml.safe_load((HERE / "fixtures.yaml").read_text())
    lookup = (HERE / "lookup.cypher").read_text()
    by_bin_sql, totals_sql = statements()
    driver = GraphDatabase.driver(os.environ["NEO4J_URI"], auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]))
    with driver, psycopg.connect(os.environ["JUSTFIX_DATABASE_URL"]) as pg, driver.session(database=os.environ["NEO4J_DATABASE"], default_access_mode="READ") as s:
        pg.read_only = True
        with pg.cursor() as cur:
            for f in fx["buildings"]:
                cur.execute(by_bin_sql, {"bin": f["bin"]})
                src = {(c, st): (int(n), str(o) if o else None) for c, st, n, o in cur.fetchall()}
                rows = [r for r in s.run(lookup, bin=f["bin"]).data() if r["violationClass"] is not None]
                got = {(r["violationClass"], r["status"]): (r["violations"], str(r["oldestInspection"]) if r["oldestInspection"] else None) for r in rows}
                check(f"{f['bin']}: class and status counts and oldest inspection equal the source", got == {(c, "Open" if st == "Open" else "Close"): v for (c, st), v in src.items()},
                      f"graph {got} vs source {src}")
                if not f.get("derived"):
                    open_ = {c: n for (c, st), (n, _) in src.items() if st == "Open"}
                    closed = {c: n for (c, st), (n, _) in src.items() if st == "Close"}
                    check(f"{f['bin']}: open and closed counts equal the fixture", open_ == f["open"] and closed == f["closed"], f"{open_} {closed}")
                    oldest = min((o for (c, st), (n, o) in src.items() if st == "Open"), default=None)
                    check(f"{f['bin']}: oldest open inspection equals the fixture", oldest == f["oldest_open"], str(oldest))
            cur.execute(totals_sql)
            on_reg, loaded, loaded_open, excluded = (int(x) for x in cur.fetchone())
        check("fixture excluded count equals the source", excluded == fx["excluded"]["rows"], str(excluded))
        check("fixture loaded total equals the source", loaded == fx["totals"]["loaded"], str(loaded))
        g = s.run("MATCH (v:Violation) RETURN count(v) AS n, count(CASE WHEN v.status = 'Open' THEN 1 END) AS open").single()
        check("graph violations equal the source loaded total", g["n"] == loaded, f"graph {g['n']} vs {loaded}")
        check("graph open violations equal the source", g["open"] == loaded_open, f"graph {g['open']} vs {loaded_open}")
        bad = s.run("MATCH (v:Violation) WHERE v.violationClass IS NULL OR v.status IS NULL OR v.inspectionDate IS NULL "
                    "OR NOT v.violationClass IN ['A','B','C','I'] OR NOT v.status IN ['Open','Close'] RETURN count(v) AS n").single()["n"]
        check("every violation has a class, a status and an inspection date", bad == 0, str(bad))
        orphans = s.run("MATCH (v:Violation) WHERE NOT (:Building)-[:HAS_VIOLATION]->(v) RETURN count(v) AS n").single()["n"]
        check("every violation belongs to exactly the buildings of its BIN", orphans == 0, str(orphans))
        multi = s.run("MATCH (v:Violation)<-[r:HAS_VIOLATION]-(:Building) WITH v, count(r) AS k WHERE k > 1 RETURN count(v) AS n").single()["n"]
        check("no violation is linked to two buildings", multi == 0, str(multi))
        apt = s.run("MATCH (v:Violation) WHERE any(k IN keys(v) WHERE k = 'apartment') RETURN count(v) AS n").single()["n"]
        check("no apartment property is stored", apt == 0, str(apt))
    failed = results.count(False)
    print(f"{len(results) - failed}/{len(results)} checks passed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
