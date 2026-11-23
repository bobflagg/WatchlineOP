"""Check Q27.1 (complaint problems of a building in a period, by type, category and status) against the frozen source. Read-only on both databases.

Each fixture building is re-derived from the source (tests/q27_1/expected.sql), looked up with lookup.cypher and compared by type, category and status,
with duplicate and distinct-complaint counts. Then graph totals equal the source totals, every problem has the required properties and a building, and no
apartment, unit, anonymity or coordinate property exists. Counting unit: problem records. Any failure or error is a failure.
Run: uv run python tests/q27_1/check_problems.py
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
TYPES = ["EMERGENCY", "NON EMERGENCY", "IMMEDIATE EMERGENCY", "HAZARDOUS", "REFERRAL"]
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
                cur.execute(by_bin_sql, {"bin": f["bin"], "start": f["start"], "end": f["end"]})
                src = {(t, m, st): (int(n), int(d), int(c), str(a), str(z)) for t, m, st, n, d, c, a, z in cur.fetchall()}
                rows = [r for r in s.run(lookup, bin=f["bin"], start=f["start"], end=f["end"]).data() if r["problemType"] is not None]
                got = {(r["problemType"], r["majorCategory"], r["status"]): (r["problems"], r["duplicates"], r["complaints"], str(r["firstReceived"]), str(r["lastReceived"])) for r in rows}
                check(f"{f['bin']} {f['start']}..{f['end']}: type, category and status counts, duplicates, complaints and dates equal the source", got == src,
                      f"graph {got} vs source {src}")
                if not f.get("derived"):
                    by_type: dict[str, int] = {}
                    for (t, _, _), v in src.items():
                        by_type[t] = by_type.get(t, 0) + v[0]
                    check(f"{f['bin']}: counts by type equal the fixture", by_type == f["by_type"], str(by_type))
                    check(f"{f['bin']}: open count equals the fixture", sum(v[0] for (_, _, st), v in src.items() if st == "OPEN") == f["open"])
                    check(f"{f['bin']}: duplicate count equals the fixture", sum(v[1] for v in src.values()) == f["duplicates"])
            cur.execute(totals_sql)
            on_reg, loaded, loaded_open, loaded_dup, excluded = (int(x) for x in cur.fetchone())
        check("fixture excluded count equals the source", excluded == fx["excluded"]["rows"], str(excluded))
        check("fixture loaded, open and duplicate totals equal the source",
              (loaded, loaded_open, loaded_dup) == (fx["totals"]["loaded"], fx["totals"]["open"], fx["totals"]["duplicates"]), str((loaded, loaded_open, loaded_dup)))
        g = s.run("MATCH (p:Problem) RETURN count(p) AS n, count(CASE WHEN p.status = 'OPEN' THEN 1 END) AS open, count(CASE WHEN p.duplicate THEN 1 END) AS dup").single()
        check("graph problems equal the source loaded total", g["n"] == loaded, f"graph {g['n']} vs {loaded}")
        check("graph open problems equal the source", g["open"] == loaded_open, f"graph {g['open']} vs {loaded_open}")
        check("graph duplicate-flagged problems equal the source", g["dup"] == loaded_dup, f"graph {g['dup']} vs {loaded_dup}")
        bad = s.run("MATCH (p:Problem) WHERE p.problemType IS NULL OR p.majorCategory IS NULL OR p.status IS NULL OR p.receivedDate IS NULL OR p.complaintId IS NULL "
                    "OR p.duplicate IS NULL OR NOT p.problemType IN $types OR NOT p.status IN ['OPEN','CLOSE'] OR p.receivedDate < date('2021-01-01') "
                    "RETURN count(p) AS n", types=TYPES).single()["n"]
        check("every problem has a type, category, status, received date (2021 onward), complaint id and duplicate flag", bad == 0, str(bad))
        orphans = s.run("MATCH (p:Problem) WHERE NOT (:Building)-[:HAS_PROBLEM]->(p) RETURN count(p) AS n").single()["n"]
        check("every problem belongs to a building", orphans == 0, str(orphans))
        multi = s.run("MATCH (p:Problem)<-[r:HAS_PROBLEM]-(:Building) WITH p, count(r) AS k WHERE k > 1 RETURN count(p) AS n").single()["n"]
        check("no problem is linked to two buildings", multi == 0, str(multi))
        banned = ["apartment", "unitType", "spaceType", "anonymous", "latitude", "longitude"]
        extra = s.run("MATCH (p:Problem) WHERE any(k IN keys(p) WHERE k IN $banned) RETURN count(p) AS n", banned=banned).single()["n"]
        check("no apartment, unit, space, anonymity or coordinate property is stored", extra == 0, str(extra))
    failed = results.count(False)
    print(f"{len(results) - failed}/{len(results)} checks passed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
