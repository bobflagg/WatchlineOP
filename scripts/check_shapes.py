"""Stage 6 shape check for the POC graph.

1. Compile every shapes/qNN.ttl together with shacl2cypher in strict mode; every rule must compile.
2. Run each compiled rule's summary query (read-only) on the graph; every rule must report 0 violations.
3. Run each supplemental Cypher check named in shapes/coverage.yaml (queries/checks/, returns violationCount);
   each must report 0. Check coverage.yaml against the compiled rules, native constraints, checks and tests.
4. Run every tests/negative/qNN/cases.yaml: bad data is created in a transaction that is always rolled back, and the
   responsible rule (or native constraint) must reject it. The graph is counted before and after.
Writes tests/results/shapes.json. Refuses unless NEO4J_DATABASE is 'watchline'.
"""
import json
import os
import sys
from pathlib import Path

import shacl2cypher
import yaml
from dotenv import load_dotenv
from neo4j import GraphDatabase
from neo4j.exceptions import ConstraintError

ROOT = Path(__file__).resolve().parent.parent
POC_DATABASE = "watchline"
PARAMS = {"limit": 5, "sampleSize": 5}
results, failures = [], []


def check(label: str, ok: bool, detail: str = "") -> None:
    print(("PASS  " if ok else "FAIL  ") + label + (f"  [{detail}]" if detail and not ok else ""))
    results.append({"check": label, "passed": ok, "detail": detail})
    if not ok:
        failures.append(label)


def violations(session_or_tx, query: str) -> int:
    # a summary query can return more than one record; count them all
    return sum(int(r["violationCount"]) for r in session_or_tx.run(query, PARAMS).data())


def main() -> int:
    load_dotenv(ROOT / ".env")
    if os.environ.get("NEO4J_DATABASE") != POC_DATABASE:
        print(f"refusing: NEO4J_DATABASE is not the POC database '{POC_DATABASE}'", file=sys.stderr)
        return 1

    # 1. compile
    shape_files = sorted((ROOT / "shapes").glob("q[0-9][0-9].ttl"))
    comp = shacl2cypher.compile([str(f) for f in shape_files], dialect="neo4j", strict=True)
    rules = comp.manifest["rules"]
    bad = [r["name"] for r in rules if r["status"] != "compiled"]
    check(f"all {len(rules)} rules compile in strict mode", not bad and not comp.static_diagnostics, f"{bad} {comp.static_diagnostics}")
    summaries = {r["name"]: r["queries"]["summary"] for r in rules if r.get("queries")}

    driver = GraphDatabase.driver(os.environ["NEO4J_URI"], auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]))
    with driver, driver.session(database=POC_DATABASE) as session:
        nodes = lambda: session.run("MATCH (n) RETURN count(n) AS c").single()["c"]
        rels = lambda: session.run("MATCH ()-[r]->() RETURN count(r) AS c").single()["c"]
        comp_rec = session.run("CALL dbms.components() YIELD name, versions, edition").single()
        neo4j_version = f"{comp_rec['name']} {comp_rec['versions'][0]} {comp_rec['edition']}"
        print(f"Neo4j: {neo4j_version}; shacl2cypher {shacl2cypher.__version__}")
        before = (nodes(), rels())
        check("the graph is loaded", before[0] > 0, f"{before}")

        # 2. the loaded graph conforms
        for name, q in sorted(summaries.items()):
            n = violations(session, q)
            check(f"graph conforms to {name}", n == 0, f"{n} violations")

        # 3. coverage
        cov = yaml.safe_load((ROOT / "shapes/coverage.yaml").read_text())["rules"]
        extra = {}
        for r in cov:
            if r["covered_by"] == "check":
                for path in r["names"]:
                    extra[path] = (ROOT / path).read_text()
                    n = violations(session, extra[path])
                    check(f"graph conforms to {path}", n == 0, f"{n} violations")
        listed = {n for r in cov if r["covered_by"] == "compiled" for n in r["names"]}
        check("every compiled rule is listed in coverage.yaml", set(summaries) <= listed, f"missing {sorted(set(summaries) - listed)}")
        check("every listed rule name exists", listed <= set(summaries), f"unknown {sorted(listed - set(summaries))}")
        constraints = {r["name"] for r in session.run("SHOW CONSTRAINTS YIELD name")}
        native = {n for r in cov if r["covered_by"] == "native" for n in r["names"]}
        check("native constraints named in coverage.yaml are installed", native <= constraints, f"missing {sorted(native - constraints)}")
        tests = [t for r in cov if r["covered_by"] in ("test", "check") for t in r["names"]]
        check("tests and checks named in coverage.yaml exist", all((ROOT / t).exists() for t in tests))

        # 4. negative cases
        cases = [c for f in sorted((ROOT / "tests/negative").glob("q[0-9][0-9]/cases.yaml"))
                 for c in yaml.safe_load(f.read_text())["cases"]]
        for case in cases:
            tx = session.begin_transaction()
            try:
                if case.get("error") == "constraint":
                    try:
                        tx.run(case["create"]).consume()
                        check(f"negative: {case['name']} is refused by a native constraint", False, "write was accepted")
                    except ConstraintError:
                        check(f"negative: {case['name']} is refused by a native constraint", True)
                else:
                    tx.run(case["create"]).consume()
                    rule = case.get("rule") or case["check"]
                    q = summaries[case["rule"]] if "rule" in case else extra[case["check"]]
                    n = violations(tx, q)
                    check(f"negative: {case['name']} is flagged by {rule}", n > 0)
            finally:
                tx.rollback()
        after = (nodes(), rels())
        check("seeded bad data left no trace (rolled back)", after == before, f"{before} -> {after}")

    out = ROOT / "tests/results"
    out.mkdir(exist_ok=True)
    (out / "shapes.json").write_text(json.dumps({
        "neo4j": neo4j_version, "shacl2cypher": shacl2cypher.__version__, "rules": len(rules), "checks": results}, indent=2))
    total = len(results)
    print(f"\n{total - len(failures)}/{total} checks passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
