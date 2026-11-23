"""Check Q7.5 (did either BOR layer group the two, and which links connect their landlord records) against fixtures. Read-only on Neo4j.

Each fixture pair is looked up with tests/q7_5/lookup.cypher (an entity first resolves to lots with lookup_lots.cypher) and compared:
the lots, the shared network and portfolio (or the BOR absence reasons), the landlords and every link with its weight and evidence.
The fixtures are derived from the release by tests/q8_3 and tests/q8_4; this check shows the Q7.5 lookup reads them the same way.
Any failure or error is a failure. Run: uv run python tests/q7_5/check_grouping.py
"""

import os
import sys
from pathlib import Path

import yaml
from dotenv import load_dotenv
from neo4j import GraphDatabase

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "src"))
from watchline.compare import n3  # noqa: E402

REQUIRED_ENV = ("NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD", "NEO4J_DATABASE")
results = []


def check(name, ok, detail=""):
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  ({detail})" if detail and not ok else ""))


def link_key(k):
    return (k["type"], k["nodeA"], k["nodeB"], k.get("weight"), k.get("stage"), k.get("evidenceType"), k.get("evidenceId"),
            k.get("networkGroupId"), k.get("portfolioGroupId"))


def shared(lots_a, lots_b, key):
    a = {l[key] for l in lots_a if l[key]}
    b = {l[key] for l in lots_b if l[key]}
    both = sorted(a & b)
    return both[0] if both else None


def main() -> int:
    load_dotenv(ROOT / ".env")
    missing = [k for k in REQUIRED_ENV if not os.environ.get(k)]
    if missing:
        print(f"missing in .env: {', '.join(missing)}", file=sys.stderr)
        return 1
    fx = yaml.safe_load((HERE / "fixtures.yaml").read_text())
    lookup = (HERE / "lookup.cypher").read_text()
    lookup_lots = (HERE / "lookup_lots.cypher").read_text()
    driver = GraphDatabase.driver(os.environ["NEO4J_URI"], auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]))
    with driver, driver.session(database=os.environ["NEO4J_DATABASE"], default_access_mode="READ") as session:
        for f in fx["pairs"]:
            label = f["label"]
            if "nameA" in f:
                a = sorted(session.run(lookup_lots, nameKey=n3(f["nameA"])).single()["bbls"])
                b = sorted(session.run(lookup_lots, nameKey=n3(f["nameB"])).single()["bbls"])
                check(f"{label}: lots found by name", (a, b) == (sorted(f["lotsA"]), sorted(f["lotsB"])), f"graph {a} and {b}")
            else:
                a, b = f["bblsA"], f["bblsB"]
            rec = session.run(lookup, bblsA=a, bblsB=b).single()
            check(f"{label}: network shared is {f['network_shared']}", shared(rec["lotsA"], rec["lotsB"], "networkGroupId") == f["network_shared"])
            check(f"{label}: portfolio shared is {f['portfolio_shared']}", shared(rec["lotsA"], rec["lotsB"], "portfolioGroupId") == f["portfolio_shared"])
            if "absence" in f:
                lots = rec["lotsA"] + rec["lotsB"]
                check(f"{label}: BOR absence reasons",
                      all(l["networkAbsenceDetail"] == f["absence"]["network"] and l["portfolioAbsenceDetail"] == f["absence"]["portfolio"]
                          and l["networkGroupId"] is None and l["portfolioGroupId"] is None for l in lots))
            check(f"{label}: landlords", (sorted(rec["landlordsA"]), sorted(rec["landlordsB"])) == (sorted(f["landlordsA"]), sorted(f["landlordsB"])))
            got = sorted(map(link_key, rec["links"]), key=str)
            want = sorted((link_key(k) for k in f["links"]), key=str)
            check(f"{label}: links with weight and evidence", got == want, f"graph {len(got)} vs fixture {len(want)}")
    failed = results.count(False)
    print(f"{len(results) - failed}/{len(results)} checks passed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
