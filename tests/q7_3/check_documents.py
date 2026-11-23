"""Check Document, DocumentParty and HAS_PARTY against the frozen source. Read-only on both databases.

1. Totals recomputed from the source for the loaded documents must equal the graph, and the document count must equal the fixture.
2. A deterministic sample of loaded documents is re-derived from the source (current version, all parties with their roles).
3. Each fixture pair is looked up with tests/q7_3/lookup.cypher; the pair's documents must equal the fixture (anchor pair: none, an expected gap).
4. Every loaded document is scope C (two or more distinct CorporateOwner names) or scope M (an MTGE naming one, Q11.1), and a sample of stored hub counts equals the source.
Person names are never printed. Any failure or error is a failure. Run: uv run python tests/q7_3/check_documents.py
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
sys.path.insert(0, str(ROOT / "src"))
from watchline.compare import n3  # noqa: E402

REQUIRED_ENV = ("JUSTFIX_DATABASE_URL", "NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD", "NEO4J_DATABASE")
SQL_N3 = ("btrim(regexp_replace(replace(replace(replace(replace(upper(btrim({c})), '.', ''), ',', ' '), '''', ''), "
          "E'\\t', ' '), '\\s+', ' ', 'g'))")
SOURCE_TOTALS = """
WITH p AS (SELECT DISTINCT documentid, partytype, nullif(btrim(name), '') n, nullif(btrim(address1), '') a,
                  nullif(btrim(address2), '') l, nullif(btrim(zip), '') z
           FROM real_property_parties WHERE documentid = ANY(%(docs)s))
SELECT count(*), count(DISTINCT (documentid, n, a, l, z)), count(DISTINCT (documentid, n, a, l, z)) FILTER (WHERE n IS NOT NULL) FROM p
"""
SOURCE_DOC = """
SELECT DISTINCT partytype, nullif(btrim(name), ''), nullif(btrim(address1), ''), nullif(btrim(address2), ''), nullif(btrim(zip), '')
FROM real_property_parties WHERE documentid = %(doc)s
"""
SOURCE_MASTER = """
SELECT doctype FROM real_property_master WHERE documentid = %(doc)s
ORDER BY modifieddate DESC NULLS LAST, goodthroughdate DESC NULLS LAST LIMIT 1
"""
SOURCE_HUB = f"""
SELECT count(DISTINCT {SQL_N3.format(c='name')}) FILTER (WHERE name ~ '[A-Za-z]'), count(DISTINCT documentid)
FROM real_property_parties WHERE upper(btrim(address1)) = %(street)s AND left(btrim(coalesce(zip, '')), 5) = %(zip5)s
"""
GRAPH_TOTALS = """
CALL () { MATCH (d:Document) WHERE d.documentId IN $ids MATCH (d)-[r:HAS_PARTY]->(p:DocumentParty) RETURN count(r) AS links, count(DISTINCT p) AS parties, count(DISTINCT CASE WHEN p.name IS NULL THEN null ELSE p END) AS named }
CALL () { MATCH (p:DocumentParty) OPTIONAL MATCH (d:Document)-[:HAS_PARTY]->(p) WITH p, count(DISTINCT d) AS n WHERE n <> 1 RETURN count(p) AS notone }
RETURN links, parties, named, notone
"""
HUB_SAMPLE = """
MATCH (p:DocumentParty) WHERE p.addressNames IS NOT NULL
WITH DISTINCT upper(p.mailingAddress) AS street, left(coalesce(p.zip, ''), 5) AS zip5, p.addressNames AS n, p.addressDocuments AS d
RETURN street, zip5, n, d ORDER BY street, zip5 LIMIT 60
"""
SAMPLE_IDS = "MATCH (d:Document) RETURN d.documentId AS id ORDER BY id"
GRAPH_DOC = """
MATCH (d:Document {documentId: $id})
OPTIONAL MATCH (d)-[r:HAS_PARTY]->(p:DocumentParty)
RETURN d.docType AS docType, collect(CASE WHEN p IS NULL THEN null ELSE [r.partyType, p.name, p.mailingAddress, p.addressLine2, p.zip] END) AS parties
"""
OWNER_KEYS = "MATCH (c:Contact {contactType: 'CorporateOwner'}) WHERE c.corporationName IS NOT NULL RETURN DISTINCT c.corporationName AS n"
DOC_KEYS = "MATCH (d:Document)-[:HAS_PARTY]->(p:DocumentParty) WHERE p.nameKey IS NOT NULL RETURN d.documentId AS id, collect(DISTINCT p.nameKey) AS ks"
results = []


def check(name, ok, detail=""):
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  ({detail})" if detail and not ok else ""))


def key(row):
    return tuple("" if x is None else str(x) for x in row)


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
        ids = [r["id"] for r in session.run(SAMPLE_IDS)]
        owners = {k for r in session.run(OWNER_KEYS) if (k := n3(r["n"]))}
        doc_keys = {r["id"]: r["ks"] for r in session.run(DOC_KEYS)}
        t = fx.get("totals") or {}
        scope_c = [i for i in ids if len(owners & set(doc_keys.get(i, []))) >= 2]
        check("scope C document count equals the fixture (Q11.1 mortgages are counted apart)", len(scope_c) == t.get("documents"),
              f"graph {len(scope_c)} vs fixture {t.get('documents')}")
        scope_c_set = set(scope_c)
        # Scope F (Q13) also loads financing documents on graph lots; those without owner names are outside scopes C and M and are left to Q13.
        fin = {r["id"] for r in session.run("MATCH (:Lot)-[:HAS_FINANCING_DOCUMENT]->(d:Document) RETURN DISTINCT d.documentId AS id")}
        other_types = {r["id"]: r["t"] for r in session.run("MATCH (d:Document) RETURN d.documentId AS id, d.docType AS t")}

        def is_m(i):
            return other_types.get(i) == "MTGE" and bool(owners & set(doc_keys.get(i, [])))

        others = [i for i in ids if i not in scope_c_set and i not in fin]
        check("every document outside scope C and scope F is a mortgage naming an owner (scope M, Q11.1)",
              all(is_m(i) for i in others), f"{sum(1 for i in others if not is_m(i))} do not")
        ids = [i for i in ids if i in scope_c_set or i not in fin or is_m(i)]
        g = session.run(GRAPH_TOTALS, ids=ids).single()
        check("every DocumentParty is linked to exactly one Document", g["notone"] == 0, f"{g['notone']} not linked once")
        with psycopg.connect(os.environ["JUSTFIX_DATABASE_URL"]) as pg:
            pg.read_only = True
            with pg.cursor() as cur:
                cur.execute(SOURCE_TOTALS, {"docs": ids})
                links, parties, named = cur.fetchone()
                check("graph totals match source", (g["links"], g["parties"], g["named"]) == (links, parties, named),
                      f"graph {(g['links'], g['parties'], g['named'])} vs source {(links, parties, named)}")
                step = max(1, len(ids) // 40)
                for doc in ids[::step]:
                    cur.execute(SOURCE_DOC, {"doc": doc})
                    src = sorted(key(r) for r in cur.fetchall())
                    cur.execute(SOURCE_MASTER, {"doc": doc})
                    m = cur.fetchone()
                    rec = session.run(GRAPH_DOC, id=doc).single()
                    got = sorted(key(r) for r in rec["parties"])
                    check(f"{doc} parties and type match source", got == src and m is not None and rec["docType"] == m[0],
                          f"graph {len(got)} parties vs source {len(src)}")
                for pair in fx["pairs"]:
                    rows = session.run(lookup, nameKeyA=n3(pair["a"]), nameKeyB=n3(pair["b"])).data()
                    got = sorted(r["documentId"] for r in rows)
                    check(f"{pair['a']} and {pair['b']}: documents match fixture", got == sorted(pair["documents"]),
                          f"graph {got} vs fixture {sorted(pair['documents'])}")
                    for r in rows:
                        given = [p for p in r["parties"] if p["given"]]
                        check(f"{r['documentId']} marks both given parties", len({p["name"] for p in given}) >= 1 and len(given) >= 2)
                for h in session.run(HUB_SAMPLE).data()[::6]:
                    cur.execute(SOURCE_HUB, {"street": h["street"], "zip5": h["zip5"]})
                    src_hub = cur.fetchone()
                    check(f"hub {h['street']} {h['zip5']} equals source", src_hub == (h["n"], h["d"]),
                          f"source {src_hub}, graph {(h['n'], h['d'])}")
    failed = results.count(False)
    print(f"{len(results) - failed}/{len(results)} checks passed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
