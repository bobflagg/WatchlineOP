"""Check the contact, registration and building counts per business address (Q6.1) against the frozen source. Read-only on both databases.

1. Each fixture is re-derived from the source with tests/q6_1/expected.sql, so a stale fixture fails.
2. Each fixture is looked up in the graph with tests/q6_1/lookup.cypher.
3. Graph totals must equal the totals computed from the source.
Any error counts as a failure. Run: uv run python tests/q6_1/check_address_counts.py
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
KEYS = ("contacts", "ownerContacts", "roleContacts", "registrations", "buildings")
GRAPH_TOTALS = """
MATCH (c:Contact) WHERE c.mailingAddress IS NOT NULL AND c.zip IS NOT NULL
RETURN count(c) AS contacts, count(DISTINCT [toUpper(c.mailingAddress), left(c.zip, 5)]) AS addresses
"""
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
    expected = (HERE / "expected.sql").read_text()
    lookup = (HERE / "lookup.cypher").read_text()
    driver = GraphDatabase.driver(os.environ["NEO4J_URI"], auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]))
    with driver, driver.session(database=os.environ["NEO4J_DATABASE"], default_access_mode="READ") as session:
        with psycopg.connect(os.environ["JUSTFIX_DATABASE_URL"]) as pg:
            pg.read_only = True
            with pg.cursor() as cur:
                for f in fx["addresses"]:
                    label = f"{f['street']} {f['zip5']}"
                    cur.execute(expected, {"street": f["street"].upper(), "zip5": f["zip5"]})
                    src = cur.fetchone()
                    want = tuple(f[k] for k in KEYS)
                    check(f"{label} fixture matches source", tuple(src) == want, f"source gives {src}")
                    g = session.run(lookup, street=f["street"].upper(), zip5=f["zip5"]).single()
                    check(f"{label} graph matches fixture", tuple(g[k] for k in KEYS) == want, f"graph has {tuple(g[k] for k in KEYS)}")
                cur.execute(expected.replace("WHERE upper(street) = %(street)s AND left(zp, 5) = %(zip5)s", "WHERE street IS NOT NULL AND zp IS NOT NULL"))
                src_total = cur.fetchone()[0]
        t = fx["totals"]
        check("source total matches fixture", src_total == t["contacts_with_street_and_zip"], f"source gives {src_total}")
        g = session.run(GRAPH_TOTALS).single()
        check("graph contacts with a street line and ZIP equal the source", g["contacts"] == src_total, f"graph {g['contacts']} vs source {src_total}")
        check("graph distinct addresses match fixture", g["addresses"] == t["distinct_addresses"], f"graph {g['addresses']}")
    failed = results.count(False)
    print(f"{len(results) - failed}/{len(results)} checks passed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
