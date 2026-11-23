"""Check Q7.4 (is a shared address set aside, and why) against fixtures. Read-only on Neo4j.

Each fixture address is looked up with tests/q7_4/lookup.cypher. The lookup must report the network mask, the portfolio mask and the mail-drop
rows exactly as the fixture says, set an address aside when any marks it, use it when none does, and say when the list was not consulted.
The fixtures come from the Q6.2 to Q6.4 fixtures, which tests/q6_2, q6_3 and q6_4 re-derive from the release and the list file.
Any failure or error is a failure. Run: uv run python tests/q7_4/check_set_aside.py
"""

import os
import sys
from pathlib import Path

import yaml
from dotenv import load_dotenv
from neo4j import GraphDatabase

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
REQUIRED_ENV = ("NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD", "NEO4J_DATABASE")
results = []


def check(name, ok, detail=""):
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
    with driver, driver.session(database=os.environ["NEO4J_DATABASE"], default_access_mode="READ") as session:
        for f in fx["addresses"]:
            label = f"{f['street']}{' ' + f['line2'] if f['line2'] else ''} {f['zip5']}"
            rec = session.run(lookup, street=f["street"], line2=f["line2"], zip5=f["zip5"], listAddress=f["listAddress"]).single()
            check(f"{label}: network mask is {f['network']}", (rec["networkMask"] is not None) == f["network"])
            check(f"{label}: portfolio mask is {f['portfolio']}", (rec["portfolioMask"] is not None) == f["portfolio"])
            got = sorted((m["listZip"], m["kind"]) for m in rec["mailDrop"])
            want = sorted((m["listZip"], m["kind"]) for m in f["mailDrop"])
            check(f"{label}: mail-drop rows", got == want, f"graph {got} vs fixture {want}")
            check(f"{label}: set aside is {f['setAside']}", rec["setAside"] == f["setAside"])
            check(f"{label}: list consulted flag", rec["listNotConsulted"] == f["listNotConsulted"])
    failed = results.count(False)
    print(f"{len(results) - failed}/{len(results)} checks passed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
