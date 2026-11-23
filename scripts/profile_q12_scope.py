"""Q12.1 scope profile (read-only): grantor rows (partytype 1) on the deeds already in the graph (Q3 scope).

Prints counts only, never a name. Writes nothing. Run: uv run python scripts/profile_q12_scope.py
"""

import os
import sys
import time
from collections import Counter
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from neo4j import GraphDatabase

ROOT = Path(__file__).resolve().parent.parent
REQUIRED_ENV = ("JUSTFIX_DATABASE_URL", "NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD", "NEO4J_DATABASE")
SQL = """
SELECT count(*) AS rows, count(DISTINCT (documentid, nullif(btrim(name), ''), nullif(btrim(address1), ''), nullif(btrim(address2), ''), nullif(btrim(zip), ''))) AS distinct_rows,
       count(DISTINCT documentid) AS documents, count(*) FILTER (WHERE nullif(btrim(name), '') IS NULL) AS no_name
FROM real_property_parties WHERE partytype = 1 AND documentid = ANY(%(docs)s)
"""


def main() -> int:
    load_dotenv(ROOT / ".env")
    missing = [k for k in REQUIRED_ENV if not os.environ.get(k)]
    if missing:
        print(f"missing in .env: {', '.join(missing)}", file=sys.stderr)
        return 1
    driver = GraphDatabase.driver(os.environ["NEO4J_URI"], auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]))
    with driver, driver.session(database=os.environ["NEO4J_DATABASE"], default_access_mode="READ") as s:
        docs = [r["id"] for r in s.run("MATCH (d:Deed) RETURN d.documentId AS id ORDER BY id")]
    print(f"deeds in the graph: {len(docs):,}")
    tot, t0 = Counter(), time.time()
    with psycopg.connect(os.environ["JUSTFIX_DATABASE_URL"]) as pg:
        pg.read_only = True
        with pg.cursor() as cur:
            cur.execute("SET statement_timeout = 0")
            with_g = 0
            for i in range(0, len(docs), 20000):
                cur.execute(SQL, {"docs": docs[i:i + 20000]})
                r = cur.fetchone()
                tot.update(dict(zip(("rows", "distinct_rows", "documents", "no_name"), r)))
    print(f"grantor rows {tot['rows']:,}, distinct party rows {tot['distinct_rows']:,}, deeds with a grantor {tot['documents']:,}, no name {tot['no_name']:,} ({time.time() - t0:.0f}s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
