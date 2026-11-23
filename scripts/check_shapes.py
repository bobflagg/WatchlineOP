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
from concurrent.futures import ThreadPoolExecutor
import os
import time
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


VERBOSE = os.environ.get("VERBOSE") == "1"
_last = [time.monotonic()]


def check(label: str, ok: bool, detail: str = "") -> None:
    now = time.monotonic()
    took, _last[0] = now - _last[0], now
    # quiet by default: failures and checks that took 5 seconds or more; VERBOSE=1 prints every check
    if VERBOSE or not ok or took >= 5:
        print(("PASS  " if ok else "FAIL  ") + label + (f"  [{detail}]" if detail and not ok else "") + (f"  ({took:.0f}s)" if took >= 5 else ""), flush=True)
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

    driver = GraphDatabase.driver(os.environ["NEO4J_URI"], auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]),
                                  notifications_min_severity="OFF")
    with driver, driver.session(database=POC_DATABASE) as session:
        nodes = lambda: session.run("MATCH (n) RETURN count(n) AS c").single()["c"]
        rels = lambda: session.run("MATCH ()-[r]->() RETURN count(r) AS c").single()["c"]
        comp_rec = session.run("CALL dbms.components() YIELD name, versions, edition").single()
        neo4j_version = f"{comp_rec['name']} {comp_rec['versions'][0]} {comp_rec['edition']}"
        print(f"Neo4j: {neo4j_version}; shacl2cypher {shacl2cypher.__version__}")
        before = (nodes(), rels())
        check("the graph is loaded", before[0] > 0, f"{before}")

        # 2. the loaded graph conforms
        print("== compiled rules on the graph", flush=True)
        for name, q in sorted(summaries.items()):
            n = violations(session, q)
            check(f"graph conforms to {name}", n == 0, f"{n} violations")

        # 3. coverage
        print("== supplemental checks", flush=True)
        cov = yaml.safe_load((ROOT / "shapes/coverage.yaml").read_text())["rules"]
        extra = {}
        for r in cov:
            if r["covered_by"] == "check":
                for path in r["names"]:
                    if path in extra:  # several coverage rows can name one check; run it once
                        continue
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
        print("== negative cases", flush=True)
        cases = [c for f in sorted((ROOT / "tests/negative").glob("q[0-9][0-9]/cases.yaml"))
                 for c in yaml.safe_load(f.read_text())["cases"]]
        def run_case(sess, case):
            """One seeded bad case in a transaction that is always rolled back. Returns (label, ok, detail)."""
            tx = sess.begin_transaction()
            try:
                if case.get("error") == "constraint":
                    label = f"negative: {case['name']} is refused by a native constraint"
                    try:
                        tx.run(case["create"]).consume()
                        return label, False, "write was accepted"
                    except ConstraintError:
                        return label, True, ""
                tx.run(case["create"]).consume()
                rule = case.get("rule") or case["check"]
                q = summaries[case["rule"]] if "rule" in case else extra[case["check"]]
                return f"negative: {case['name']} is flagged by {rule}", violations(tx, q) > 0, ""
            finally:
                tx.rollback()

        # Cases that rerun a whole-graph supplemental check cost one full scan each. Cases of different checks are independent
        # (each rolls back), so the checks run in parallel, one session each; the cases of one check stay in order.
        quick = [c for c in cases if "check" not in c or c.get("error") == "constraint"]
        heavy: dict = {}
        for c in cases:
            if c not in quick:
                heavy.setdefault(c["check"], []).append(c)
        for case in quick:
            check(*run_case(session, case))

        def run_group(group):
            with driver.session(database=POC_DATABASE) as s:
                out = []
                for case in group:
                    t0 = time.monotonic()
                    try:
                        res = run_case(s, case)
                    except Exception as exc:  # a lock wait or deadlock between groups: record it, retry once
                        res = run_case(s, case)
                        res = (res[0], res[1], f"retried after {type(exc).__name__}")
                    out.append((res, time.monotonic() - t0))
                return out

        with ThreadPoolExecutor(max_workers=min(6, max(1, len(heavy)))) as pool:
            for out in pool.map(run_group, heavy.values()):
                for (label, ok, detail), took in out:
                    if VERBOSE or not ok or took >= 5:
                        print(("PASS  " if ok else "FAIL  ") + label + (f"  [{detail}]" if detail and not ok else "") + (f"  ({took:.0f}s)" if took >= 5 else ""), flush=True)
                    results.append({"check": label, "passed": ok, "detail": detail})
                    if not ok:
                        failures.append(label)
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
