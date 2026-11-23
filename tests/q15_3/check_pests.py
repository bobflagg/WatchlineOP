"""Check Q15.3 (pest violations of a building, by order code and status) against the frozen source. Read-only on both databases.

Each fixture building is re-derived from the source (tests/q15_3/expected.sql), looked up with lookup.cypher and compared by order code and
status, with the oldest open inspection date. Then graph totals per pest order code equal the source and the fixture, every Violation has an order
code, the code list in data/hpd_pest_orders.yaml has no code in two kinds, and no description or apartment property is stored.
Counting unit: violations. Any failure or error is a failure.
Run: uv run python tests/q15_3/check_pests.py
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
    kinds = yaml.safe_load((ROOT / "data/hpd_pest_orders.yaml").read_text())["kinds"]
    codes = [c for k in kinds.values() for c in k["codes"]]
    check("no order code is listed under two pest kinds", len(codes) == len(set(codes)), str(codes))
    check("the fixture totals name exactly the listed codes", set(fx["totals"]["loaded"]) == set(codes), str(sorted(codes)))
    lookup = (HERE / "lookup.cypher").read_text()
    by_bin_sql, totals_sql, bad_sql = statements()
    driver = GraphDatabase.driver(os.environ["NEO4J_URI"], auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]))
    with driver, psycopg.connect(os.environ["JUSTFIX_DATABASE_URL"]) as pg, driver.session(database=os.environ["NEO4J_DATABASE"], default_access_mode="READ") as s:
        pg.read_only = True
        with pg.cursor() as cur:
            for f in fx["buildings"]:
                cur.execute(by_bin_sql, {"bin": f["bin"], "codes": codes})
                src = {(o, st): (int(n), str(d) if d else None) for o, st, n, d in cur.fetchall()}
                rows = [r for r in s.run(lookup, bin=f["bin"], codes=codes).data() if r["orderNumber"] is not None]
                got = {(r["orderNumber"], r["status"]): (r["violations"], str(r["oldestInspection"]) if r["oldestInspection"] else None) for r in rows}
                check(f"{f['bin']}: order code and status counts and oldest inspection equal the source", got == src, f"graph {got} vs source {src}")
                if not f.get("derived"):
                    open_ = {o: n for (o, st), (n, _) in src.items() if st == "Open"}
                    closed = {o: n for (o, st), (n, _) in src.items() if st == "Close"}
                    check(f"{f['bin']}: open and closed counts equal the fixture", open_ == f["open"] and closed == f["closed"], f"{open_} {closed}")
                    oldest = min((d for (o, st), (n, d) in src.items() if st == "Open"), default=None)
                    check(f"{f['bin']}: oldest open inspection equals the fixture", oldest == f["oldest_open"], str(oldest))
            cur.execute(totals_sql, {"codes": codes})
            src_tot = {o: (int(n), int(op)) for o, n, op in cur.fetchall()}
            cur.execute(bad_sql)
            loaded, bad_order = (int(x) for x in cur.fetchone())
        check("source loaded rows per pest order code equal the fixture", {o: n for o, (n, _) in src_tot.items()} == fx["totals"]["loaded"], str(src_tot))
        check("source open rows per pest order code equal the fixture", {o: op for o, (_, op) in src_tot.items()} == fx["totals"]["loaded_open"], str(src_tot))
        g = {r["o"]: (r["n"], r["open"]) for r in s.run(
            "MATCH (v:Violation) WHERE v.orderNumber IN $codes RETURN v.orderNumber AS o, count(v) AS n, count(CASE WHEN v.status = 'Open' THEN 1 END) AS open", codes=codes)}
        check("graph violations and open violations per pest order code equal the source", g == src_tot, f"graph {g} vs source {src_tot}")
        check("source: every loaded violation has a numeric order code", bad_order == 0 and loaded == fx["totals"]["every_violation_has_order_code"], f"{loaded} {bad_order}")
        miss = s.run("MATCH (v:Violation) WHERE v.orderNumber IS NULL OR NOT v.orderNumber =~ '[0-9]+' RETURN count(v) AS n").single()["n"]
        check("every Violation has a numeric order code", miss == 0, str(miss))
        n_all = s.run("MATCH (v:Violation) RETURN count(v) AS n").single()["n"]
        check("graph violations equal the loaded total", n_all == loaded, f"{n_all} vs {loaded}")
        extra = s.run("MATCH (v:Violation) WHERE any(k IN keys(v) WHERE k IN ['apartment', 'description', 'novDescription', 'pestKind']) RETURN count(v) AS n").single()["n"]
        check("no apartment, description or derived pest kind is stored", extra == 0, str(extra))
    failed = results.count(False)
    print(f"{len(results) - failed}/{len(results)} checks passed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
