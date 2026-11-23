"""Check Q27.3 (pest complaint problems of a building in a period, by pest and status) against the frozen source. Read-only on both databases.

Each fixture building is re-derived from the source (tests/q27_3/expected.sql), looked up with lookup.cypher and compared by problem code and status, with
duplicate and distinct-complaint counts and dates. Then graph totals per pest equal the source and the fixture, every Problem has a minor category and a
problem code, and no apartment, unit, anonymity or coordinate property exists. Counting unit: problem records. Any failure or error is a failure.
Run: uv run python tests/q27_3/check_pest_problems.py
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


def statements() -> list[str]:
    body = [ln for ln in SQL.splitlines() if not ln.startswith("--")]
    return [p.strip() for p in "\n".join(body).split(";") if p.strip()]


def main() -> int:
    load_dotenv(ROOT / ".env")
    missing = [k for k in REQUIRED_ENV if not os.environ.get(k)]
    if missing:
        print(f"missing in .env: {', '.join(missing)}", file=sys.stderr)
        return 1
    fx = yaml.safe_load((HERE / "fixtures.yaml").read_text())
    lookup = (HERE / "lookup.cypher").read_text()
    by_bin_sql, totals_sql, missing_sql = statements()
    driver = GraphDatabase.driver(os.environ["NEO4J_URI"], auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]))
    with driver, psycopg.connect(os.environ["JUSTFIX_DATABASE_URL"]) as pg, driver.session(database=os.environ["NEO4J_DATABASE"], default_access_mode="READ") as s:
        pg.read_only = True
        with pg.cursor() as cur:
            for f in fx["buildings"]:
                cur.execute(by_bin_sql, {"bin": f["bin"], "start": f["start"], "end": f["end"]})
                src = {(c, st): (int(n), int(d), int(k), str(a), str(z)) for c, st, n, d, k, a, z in cur.fetchall()}
                rows = [r for r in s.run(lookup, bin=f["bin"], start=f["start"], end=f["end"]).data() if r["problemCode"] is not None]
                got = {(r["problemCode"], r["status"]): (r["problems"], r["duplicates"], r["complaints"], str(r["firstReceived"]), str(r["lastReceived"])) for r in rows}
                check(f"{f['bin']} {f['start']}..{f['end']}: pest, status, duplicates, complaints and dates equal the source", got == src, f"graph {got} vs source {src}")
                if not f.get("derived"):
                    by_code: dict[str, int] = {}
                    for (c, _), v in src.items():
                        by_code[c] = by_code.get(c, 0) + v[0]
                    check(f"{f['bin']}: counts by pest equal the fixture", by_code == f["by_code"], str(by_code))
                    check(f"{f['bin']}: open count equals the fixture", sum(v[0] for (_, st), v in src.items() if st == "OPEN") == f["open"])
            cur.execute(totals_sql)
            src_tot = {c: (int(n), int(o), int(d)) for c, n, o, d in cur.fetchall()}
            cur.execute(missing_sql)
            loaded, missing_n, minors = (int(x) for x in cur.fetchone())
        t = fx["totals"]
        check("source loaded, open and duplicate pest problems per problem code equal the fixture",
              src_tot == {c: (t["loaded"][c], t["loaded_open"][c], t["loaded_duplicates"][c]) for c in t["loaded"]}, str(src_tot))
        check("source: no loaded problem lacks a minor category or problem code; the loaded total and minor categories equal the fixture",
              missing_n == 0 and loaded == t["all_loaded"] and minors == t["minor_categories"], f"{loaded} {missing_n} {minors}")
        g = {r["c"]: (r["n"], r["open"], r["dup"]) for r in s.run(
            "MATCH (p:Problem) WHERE p.minorCategory = 'PESTS' RETURN p.problemCode AS c, count(p) AS n, "
            "count(CASE WHEN p.status = 'OPEN' THEN 1 END) AS open, count(CASE WHEN p.duplicate THEN 1 END) AS dup")}
        check("graph pest problems, open and duplicates per problem code equal the source", g == src_tot, f"graph {g} vs source {src_tot}")
        bad = s.run("MATCH (p:Problem) WHERE p.minorCategory IS NULL OR p.problemCode IS NULL OR trim(p.minorCategory) = '' OR trim(p.problemCode) = '' "
                    "RETURN count(p) AS n").single()["n"]
        check("every Problem has a minor category and a problem code", bad == 0, str(bad))
        n_all = s.run("MATCH (p:Problem) RETURN count(p) AS n").single()["n"]
        check("graph problems equal the loaded total", n_all == loaded, f"{n_all} vs {loaded}")
        stray = s.run("MATCH (p:Problem) WHERE p.minorCategory = 'PESTS' AND NOT p.problemCode IN $codes RETURN count(p) AS n", codes=list(t["loaded"])).single()["n"]
        check("every pest problem carries one of the seven pest problem codes", stray == 0, str(stray))
        banned = ["apartment", "unitType", "spaceType", "anonymous", "latitude", "longitude", "pestKind"]
        extra = s.run("MATCH (p:Problem) WHERE any(k IN keys(p) WHERE k IN $banned) RETURN count(p) AS n", banned=banned).single()["n"]
        check("no apartment, unit, space, anonymity, coordinate or derived pest-kind property is stored", extra == 0, str(extra))
    failed = results.count(False)
    print(f"{len(results) - failed}/{len(results)} checks passed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
