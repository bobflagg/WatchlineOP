"""Check Q28.1 (Housing Court cases of a building) against the frozen source. Read-only on both databases.

Each fixture building is re-derived from the source (tests/q28_1/expected.sql), looked up with lookup.cypher and compared case by case. Fixture
values are compared with the source too, so a stale fixture fails. Then graph totals equal the source totals, the odd-value counts match, no case
lacks a building, and nothing beyond the nine properties is stored. Counting unit: cases. Any failure or error is a failure.
Run: uv run python tests/q28_1/check_litigation.py
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
ALLOWED = {"litigationId", "caseType", "caseOpenDate", "caseStatus", "openJudgement", "harassmentFinding", "findingDate", "penalty", "respondent", "respondentKeys"}
results: list[bool] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  ({detail})" if detail and not ok else ""))


def statements() -> tuple[str, str]:
    body = [ln for ln in SQL.splitlines() if not ln.startswith("--")]
    parts = [p.strip() for p in "\n".join(body).split(";") if p.strip()]
    return parts[0], parts[1]


def iso(d) -> str | None:
    return str(d) if d is not None else None


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
                src = {int(r[0]): (r[1], iso(r[2]), r[3], r[4], r[5], iso(r[6]), r[7], r[8]) for r in cur.fetchall()}
                rows = s.run(lookup, bin=f["bin"]).data()
                got = {r["litigationId"]: (r["caseType"], iso(r["caseOpenDate"]), r["caseStatus"], r["openJudgement"], r["harassmentFinding"],
                                          iso(r["findingDate"]), r["penalty"], r["respondent"]) for r in rows}
                check(f"{f['bin']}: cases equal the source (all fields)", got == src, f"graph {len(got)} vs source {len(src)}")
                if "cases" in f:
                    check(f"{f['bin']}: case count equals the fixture", len(src) == f["cases"], str(len(src)))
                if "expect" in f:
                    e = f["expect"]
                    row = src.get(e["litigationId"])
                    names = ("caseType", "opened", "status", "judgement", "finding", "found", "penalty", "respondent")
                    ok = row is not None and all(dict(zip(names, row))[k] == v for k, v in e.items() if k != "litigationId")
                    check(f"{f['bin']}: case {e['litigationId']} equals the fixture", ok, str(row))
            cur.execute(totals_sql)
            t = dict(zip(("on_reg", "loaded", "excluded", "no_open", "old", "future", "findings", "no_harass", "no_resp"), (int(x) for x in cur.fetchone())))
        check("fixture excluded count equals the source", t["excluded"] == fx["out_of_scope"]["rows"], str(t["excluded"]))
        for key, fkey in (("loaded", "loaded"), ("no_open", "no_open_date"), ("old", "before_1990"), ("future", "after_snapshot"),
                          ("findings", "findings"), ("no_harass", "no_harassment"), ("no_resp", "no_respondent")):
            check(f"fixture {fkey} equals the source", t[key] == fx["totals"][fkey], str(t[key]))
        g = s.run("""MATCH (c:Litigation) RETURN count(c) AS n,
                     count(CASE WHEN c.caseOpenDate IS NULL THEN 1 END) AS noOpen, count(CASE WHEN c.caseOpenDate < date('1990-01-01') THEN 1 END) AS old,
                     count(CASE WHEN c.caseOpenDate > date('2026-07-31') THEN 1 END) AS future,
                     count(CASE WHEN c.harassmentFinding IN ['After Inquest','After Trial'] THEN 1 END) AS findings,
                     count(CASE WHEN c.harassmentFinding = 'No Harassment' THEN 1 END) AS noHarass,
                     count(CASE WHEN c.respondent IS NULL THEN 1 END) AS noResp""").single()
        for gk, tk in (("n", "loaded"), ("noOpen", "no_open"), ("old", "old"), ("future", "future"), ("findings", "findings"), ("noHarass", "no_harass"), ("noResp", "no_resp")):
            check(f"graph {gk} equals the source", g[gk] == t[tk], f"graph {g[gk]} vs {t[tk]}")
        orphans = s.run("MATCH (c:Litigation) WHERE NOT (:Building)-[:HAS_LITIGATION]->(c) RETURN count(c) AS n").single()["n"]
        check("every case belongs to a building", orphans == 0, str(orphans))
        multi = s.run("MATCH (c:Litigation)<-[r:HAS_LITIGATION]-(:Building) WITH c, count(r) AS k WHERE k > 1 RETURN count(c) AS n").single()["n"]
        check("no case is linked to two buildings", multi == 0, str(multi))
        bad = s.run("MATCH (c:Litigation) WHERE c.respondent IS NULL AND c.respondentKeys IS NOT NULL OR c.respondent IS NOT NULL AND c.respondent = '' RETURN count(c) AS n").single()["n"]
        check("a missing respondent is absent with no keys, never an empty string", bad == 0, str(bad))
        extra = s.run("MATCH (c:Litigation) UNWIND keys(c) AS k WITH k WHERE NOT k IN $allowed RETURN count(*) AS n", allowed=sorted(ALLOWED)).single()["n"]
        check("no property beyond the ten loaded ones is stored", extra == 0, str(extra))
    failed = results.count(False)
    print(f"{len(results) - failed}/{len(results)} checks passed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
