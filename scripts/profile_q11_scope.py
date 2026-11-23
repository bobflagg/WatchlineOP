"""Q11.1 scope profile (read-only): ACRIS financing documents that name at least one HPD corporate owner (N3), by document type.

Prints counts only, never a name. Writes nothing. Reads all of real_property_parties (about 47M rows); allow several minutes.
Run: uv run python scripts/profile_q11_scope.py
"""

import os
import sys
import time
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from neo4j import GraphDatabase

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from watchline.compare import n3  # noqa: E402

REQUIRED_ENV = ("JUSTFIX_DATABASE_URL", "NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD", "NEO4J_DATABASE")
NAMES = "MATCH (c:Contact {contactType: 'CorporateOwner'}) WHERE c.corporationName IS NOT NULL RETURN collect(DISTINCT c.corporationName) AS a"
SQL_N3 = ("btrim(regexp_replace(replace(replace(replace(replace(upper(btrim(p.name)), '.', ''), ',', ' '), '''', ''), "
          "E'\\t', ' '), '\\s+', ' ', 'g'))")
SCOPE = f"""
WITH g AS (SELECT unnest(%(keys)s::text[]) AS k),
cur AS (SELECT DISTINCT ON (documentid) documentid, doctype FROM real_property_master
        ORDER BY documentid, modifieddate DESC NULLS LAST, goodthroughdate DESC NULLS LAST),
hits AS (SELECT DISTINCT p.documentid FROM real_property_parties p JOIN g ON g.k = {SQL_N3} WHERE p.name ~ '[A-Za-z]')
SELECT c.doctype, count(*) FROM hits h JOIN cur c USING (documentid) GROUP BY 1 ORDER BY 2 DESC
"""


def main() -> int:
    load_dotenv(ROOT / ".env")
    missing = [k for k in REQUIRED_ENV if not os.environ.get(k)]
    if missing:
        print(f"missing in .env: {', '.join(missing)}", file=sys.stderr)
        return 1
    driver = GraphDatabase.driver(os.environ["NEO4J_URI"], auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]))
    with driver, driver.session(database=os.environ["NEO4J_DATABASE"], default_access_mode="READ") as s:
        keys = sorted({k for v in s.run(NAMES).single()["a"] if (k := n3(v))})
    print(f"owner name keys (N3): {len(keys):,}")
    t0 = time.time()
    with psycopg.connect(os.environ["JUSTFIX_DATABASE_URL"]) as pg:
        pg.read_only = True
        with pg.cursor() as cur:
            cur.execute("SET statement_timeout = 0")
            cur.execute(SCOPE, {"keys": keys})
            rows = cur.fetchall()
    print(f"scan finished in {time.time() - t0:.0f}s; documents naming at least one owner: {sum(n for _, n in rows):,}")
    for doctype, n in rows[:25]:
        print(f"  {doctype}: {n:,}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
