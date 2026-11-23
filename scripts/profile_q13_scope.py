"""Q13 scope profile (read-only): financing documents (MTGE, ASST, SAT, AGMT, AL&R, TL&R, SAGE) recorded against the graph's lots.

Prints counts only, never a name. Writes nothing. Run: uv run python scripts/profile_q13_scope.py
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
TYPES = ["MTGE", "ASST", "SAT", "AGMT", "AL&R", "TL&R", "SAGE"]
DOCS = """
WITH docs AS (SELECT DISTINCT documentid FROM real_property_legals WHERE bbl = ANY(%(bbls)s)),
cur AS (SELECT DISTINCT ON (m.documentid) m.documentid, m.doctype, m.docdate, m.recordedfiled, m.docamount
        FROM real_property_master m JOIN docs d USING (documentid)
        ORDER BY m.documentid, m.modifieddate DESC NULLS LAST, m.goodthroughdate DESC NULLS LAST)
SELECT documentid, doctype, docdate IS NULL, recordedfiled IS NULL, docamount IS NULL, docamount < 0, docamount = 0,
       docdate IS NOT NULL AND recordedfiled IS NOT NULL AND docdate > recordedfiled
FROM cur WHERE doctype = ANY(%(types)s)
"""
PARTIES = """
SELECT d, count(*) FILTER (WHERE x.documentid IS NOT NULL) FROM unnest(%(docs)s::text[]) d
LEFT JOIN (SELECT DISTINCT documentid, partytype, name, address1, address2, zip FROM real_property_parties WHERE documentid = ANY(%(docs)s)) x ON x.documentid = d GROUP BY d
"""
PAIRS = "SELECT documentid, count(DISTINCT bbl) FROM real_property_legals WHERE documentid = ANY(%(docs)s) GROUP BY 1"


def main() -> int:
    load_dotenv(ROOT / ".env")
    missing = [k for k in REQUIRED_ENV if not os.environ.get(k)]
    if missing:
        print(f"missing in .env: {', '.join(missing)}", file=sys.stderr)
        return 1
    driver = GraphDatabase.driver(os.environ["NEO4J_URI"], auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]))
    with driver, driver.session(database=os.environ["NEO4J_DATABASE"], default_access_mode="READ") as s:
        bbls = [r["b"] for r in s.run("MATCH (l:Lot) RETURN l.bbl AS b ORDER BY b")]
    print(f"graph lots: {len(bbls):,}")
    seen, by_type, odd, zero_party_docs, party_rows, multi = set(), Counter(), Counter(), 0, 0, 0
    t0 = time.time()
    with psycopg.connect(os.environ["JUSTFIX_DATABASE_URL"]) as pg:
        pg.read_only = True
        with pg.cursor() as cur:
            cur.execute("SET statement_timeout = 0")
            for i in range(0, len(bbls), 1000):
                cur.execute(DOCS, {"bbls": bbls[i:i + 1000], "types": TYPES})
                new = []
                for doc, typ, nodoc, norec, noamt, neg, zero, after in cur.fetchall():
                    if doc in seen:
                        continue
                    seen.add(doc), new.append(doc)
                    by_type[typ] += 1
                    odd.update({k: 1 for k, v in (("no document date", nodoc), ("no recorded date", norec), ("null amount", noamt),
                                                  ("negative amount", neg), (f"amount 0 on {typ}", zero), ("document date after recorded date", after)) if v})
                for j in range(0, len(new), 5000):
                    cur.execute(PARTIES, {"docs": new[j:j + 5000]})
                    for _, n in cur.fetchall():
                        party_rows += n
                        zero_party_docs += n == 0
                    cur.execute(PAIRS, {"docs": new[j:j + 5000]})
                    multi += sum(1 for _, n in cur.fetchall() if n > 1)
                if (i // 1000) % 20 == 0:
                    print(f"  {i + 1000:,}/{len(bbls):,} lots, {len(seen):,} documents ({time.time() - t0:.0f}s)", flush=True)
    print(f"documents {len(seen):,}; by type {dict(by_type.most_common())}")
    print(f"party rows (distinct) {party_rows:,}; documents with no party row {zero_party_docs:,}; documents on more than one source lot {multi:,}")
    for k, v in sorted(odd.items()):
        print(f"  {k}: {v:,}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
