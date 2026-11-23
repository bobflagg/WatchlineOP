"""Check the curated mail-drop and registered-agent list (Q6.4) against the list file. Read-only on the graph and the file.

1. Each fixture is re-derived from data/mail_drop_addresses.csv (checksum verified against data/sources.yaml), so a stale fixture fails.
2. Each fixture is looked up in the graph with tests/q6_4/lookup.cypher.
3. The graph's list nodes equal the file's rows (address, ZIP, kind, basis, review status).
Any failure or error is a failure. Run: uv run python tests/q6_4/check_list.py
"""

import csv
import hashlib
import os
import sys
from collections import Counter
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


def file_matches(rows, address, zip5):
    return sorted(((r["zip5"] or None, r["kind"]) for r in rows if r["address_key"] == address and (not r["zip5"] or r["zip5"] == zip5)), key=str)


def main() -> int:
    load_dotenv(ROOT / ".env")
    missing = [k for k in REQUIRED_ENV if not os.environ.get(k)]
    if missing:
        print(f"missing in .env: {', '.join(missing)}", file=sys.stderr)
        return 1
    fx = yaml.safe_load((HERE / "fixtures.yaml").read_text())
    lookup = (HERE / "lookup.cypher").read_text()
    src = yaml.safe_load((ROOT / "data/sources.yaml").read_text())
    src = src.get("sources", src)["mail_drop_list"]
    path = ROOT / "data/mail_drop_addresses.csv"
    check("list file matches the sha256 in data/sources.yaml", hashlib.sha256(path.read_bytes()).hexdigest() == src["sha256"])
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    t = fx["totals"]
    check("list totals match fixture", (len(rows), dict(Counter(r["kind"] for r in rows)), dict(Counter(r["review_status"] for r in rows)), sum(1 for r in rows if not r["zip5"]))
          == (t["rows"], t["by_kind"], t["review_status"], t["rows_without_zip"]))
    driver = GraphDatabase.driver(os.environ["NEO4J_URI"], auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]))
    with driver, driver.session(database=os.environ["NEO4J_DATABASE"], default_access_mode="READ") as session:
        for f in fx["listed"]:
            want = sorted(((z, k) for z, k in f["rows"]), key=str)
            check(f"{f['address']} {f['zip5']} fixture matches the file", file_matches(rows, f["address"], f["zip5"]) == want, f"file gives {file_matches(rows, f['address'], f['zip5'])}")
            got = sorted(((r["listZip"], r["kind"]) for r in session.run(lookup, address=f["address"], zip5=f["zip5"])), key=str)
            check(f"{f['address']} {f['zip5']} graph matches fixture", got == want, f"graph has {got}")
        for f in fx["not_listed"]:
            check(f"{f['address']} {f['zip5']} is not in the file", file_matches(rows, f["address"], f["zip5"]) == [])
            check(f"{f['address']} {f['zip5']} is not found in the graph", session.run(lookup, address=f["address"], zip5=f["zip5"]).data() == [])
        graph = sorted(((r["a"], r["z"], r["k"], r["b"], r["s"]) for r in session.run(
            "MATCH (a:MailDropAddress) RETURN a.address AS a, a.zip5 AS z, a.kind AS k, a.basis AS b, a.reviewStatus AS s")), key=str)
        file_rows = sorted(((r["address_key"], r["zip5"] or None, r["kind"], r["basis"], r["review_status"]) for r in rows), key=str)
        check("graph list nodes equal the file rows", graph == file_rows, f"{len(graph)} vs {len(file_rows)}")
    failed = results.count(False)
    print(f"{len(results) - failed}/{len(results)} checks passed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
