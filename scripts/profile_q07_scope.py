"""Q7.3 scope profile (read-only): how many ACRIS documents name two or more parties whose N3 name equals a name already in the graph.

The graph names are those the Q5 loader uses: the corporation name of every CorporateOwner Contact and the name of every Grantee. Both
sides are normalized with rule N3 (src/watchline/compare.py). Prints counts only, never a name. Writes nothing.
The scan reads all of real_property_parties (about 47M rows), so it can take several minutes.
Run: uv run python scripts/profile_q07_scope.py
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
NAMES = """
CALL () { MATCH (c:Contact {contactType: 'CorporateOwner'}) WHERE c.corporationName IS NOT NULL RETURN collect(DISTINCT c.corporationName) AS a }
CALL () { MATCH (g:Grantee) WHERE g.name IS NOT NULL RETURN collect(DISTINCT g.name) AS b }
RETURN a, b
"""
SQL_N3 = ("btrim(regexp_replace(replace(replace(replace(replace(upper(btrim(p.name)), '.', ''), ',', ' '), '''', ''), "
          "E'\\t', ' '), '\\s+', ' ', 'g'))")
SCOPE = f"""
WITH g AS (SELECT unnest(%(keys)s::text[]) AS k, unnest(%(owner)s::boolean[]) AS own),
hits AS (SELECT p.documentid, {SQL_N3} AS k FROM real_property_parties p WHERE p.name ~ '[A-Za-z]'),
docs AS (SELECT h.documentid, count(DISTINCT h.k) AS names, count(DISTINCT h.k) FILTER (WHERE g.own) AS owner_names
         FROM hits h JOIN g ON g.k = h.k GROUP BY h.documentid HAVING count(DISTINCT h.k) >= 2)
SELECT d.documentid, d.names, d.owner_names, (SELECT m.doctype FROM real_property_master m WHERE m.documentid = d.documentid
                               ORDER BY m.modifieddate DESC NULLS LAST, m.goodthroughdate DESC NULLS LAST LIMIT 1) AS doctype
FROM docs d
"""


def main() -> int:
    load_dotenv(ROOT / ".env")
    missing = [k for k in REQUIRED_ENV if not os.environ.get(k)]
    if missing:
        print(f"missing in .env: {', '.join(missing)}", file=sys.stderr)
        return 1
    driver = GraphDatabase.driver(os.environ["NEO4J_URI"], auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]))
    with driver, driver.session(database=os.environ["NEO4J_DATABASE"], default_access_mode="READ") as s:
        rec = s.run(NAMES).single()
    owners = {k for v in rec["a"] if (k := n3(v))}
    grantees = {k for v in rec["b"] if (k := n3(v))}
    keys = sorted(owners | grantees)
    is_owner = [k in owners for k in keys]
    print(f"graph name keys (N3): {len(owners):,} owner, {len(grantees):,} grantee, {len(keys):,} distinct")
    t0 = time.time()
    with psycopg.connect(os.environ["JUSTFIX_DATABASE_URL"]) as pg:
        pg.read_only = True
        with pg.cursor() as cur:
            cur.execute("SET statement_timeout = 0")
            cur.execute(SCOPE, {"keys": keys, "owner": is_owner})
            rows = cur.fetchall()
    scopes = {
        "A: two or more graph names (owner or grantee)": lambda n, o: True,
        "B: two or more graph names, at least one an HPD corporate owner": lambda n, o: o >= 1,
        "C: two or more HPD corporate-owner names": lambda n, o: o >= 2,
    }
    print(f"scan finished in {time.time() - t0:.0f}s")
    for label, keep in scopes.items():
        sel = [r for r in rows if keep(r[1], r[2])]
        types = {}
        for _, _, _, doctype in sel:
            types[doctype] = types.get(doctype, 0) + 1
        top = ", ".join(f"{t} {n:,}" for t, n in sorted(types.items(), key=lambda kv: -kv[1])[:6])
        print(f"{label}: {len(sel):,} documents (widest {max((r[1] for r in sel), default=0)} names); {top}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
