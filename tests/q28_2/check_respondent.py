"""Check Q28.2 (case respondents against the registered owner) against the frozen source. Read-only on both databases.

For each fixture building the owner names and respondent strings are derived from the source (tests/q28_2/expected.sql) and matched with rule N3 in
Python; the same match is made from the graph lookup (tests/q28_2/lookup.cypher). The two must agree for every case, and each fixture's expected
matches must hold. A case with no respondent or a building with no owner name is not comparable. Any failure or error is a failure.
Run: uv run python tests/q28_2/check_respondent.py
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
results: list[bool] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  ({detail})" if detail and not ok else ""))


def parts(respondent: str | None) -> list[str]:
    return sorted({k for p in (respondent or "").split(",") if (k := n3(p))})


def match(keys: list[str], owner_keys: set[str]):
    """None = not comparable; else the sorted respondent keys that equal an owner key."""
    if not keys or not owner_keys:
        return None
    return sorted(k for k in keys if k in owner_keys)


def main() -> int:
    load_dotenv(ROOT / ".env")
    missing = [k for k in REQUIRED_ENV if not os.environ.get(k)]
    if missing:
        print(f"missing in .env: {', '.join(missing)}", file=sys.stderr)
        return 1
    fx = yaml.safe_load((HERE / "fixtures.yaml").read_text())
    lookup = (HERE / "lookup.cypher").read_text()
    body = [ln for ln in (HERE / "expected.sql").read_text().splitlines() if not ln.startswith("--")]
    owners_sql, cases_sql = [p.strip() for p in "\n".join(body).split(";") if p.strip()][:2]
    driver = GraphDatabase.driver(os.environ["NEO4J_URI"], auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]))
    with driver, psycopg.connect(os.environ["JUSTFIX_DATABASE_URL"]) as pg, driver.session(database=os.environ["NEO4J_DATABASE"], default_access_mode="READ") as s:
        pg.read_only = True
        with pg.cursor() as cur:
            for f in fx["buildings"]:
                cur.execute(owners_sql, {"bin": f["bin"]})
                src_owner_keys = {k for _, _, name in cur.fetchall() if (k := n3(name))}
                cur.execute(cases_sql, {"bin": f["bin"]})
                src = {int(i): match(parts(r), src_owner_keys) for i, r in cur.fetchall()}
                rec = s.run(lookup, bin=f["bin"]).single()
                cases = rec["cases"] if rec else []
                owner_keys = {k for o in (rec["owners"] if rec else []) for name in (o["corporationName"], o["personName"]) if (k := n3(name))}
                got = {c["litigationId"]: match(c["respondentKeys"] or [], owner_keys) for c in cases}
                check(f"{f['bin']}: graph matches equal the source matches for every case", got == src, f"graph {len(got)} vs source {len(src)}")
                for e in f["expect"]:
                    m = src.get(e["litigationId"], "missing")
                    ok = m is None if e.get("not_comparable") else m == sorted(n3(k) for k in e["matched_keys"])
                    check(f"{f['bin']}: case {e['litigationId']} matches the fixture", ok, str(m))
        nokeys = s.run("MATCH (c:Litigation) WHERE c.respondent IS NOT NULL AND c.respondentKeys IS NULL RETURN count(c) AS n").single()["n"]
        check("every recorded respondent yields at least one key", nokeys == 0, str(nokeys))
    failed = results.count(False)
    print(f"{len(results) - failed}/{len(results)} checks passed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
