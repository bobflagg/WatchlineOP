"""Check Q11.1 (recorded mortgages naming an entity, with each party's role) against the frozen source. Read-only on both databases.

1. The graph's scope M mortgage count (MTGE documents naming an HPD corporate owner, whether or not scope F also loaded them) equals the fixture total
   (scripts/profile_q11_scope.py) and every MTGE party type is 1 or 2.
2. Each fixture entity is re-derived from the source with tests/q11_1/expected.sql, then looked up with tests/q11_1/lookup.cypher: the
   documents, dates, amounts, roles, borrowers and lenders must equal both. An entity with `documents: []` is a gap: the source has the
   mortgage (`source_documents`) and the graph has none.
   A gap document is now also reached through scope F (Q13); the check requires it to be lot-linked and absent from scope M.
3. A deterministic sample of MTGE documents is re-derived from the source (all parties with their roles).
Person names are never printed. Any failure or error is a failure. Run: uv run python tests/q11_1/check_mortgages.py
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
results = []


def check(name, ok, detail=""):
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  ({detail})" if detail and not ok else ""))


GRAPH_TOTALS = """
CALL () { MATCH (d:Document {docType: 'MTGE'}) WHERE EXISTS { MATCH (d)-[:HAS_PARTY]->(q:DocumentParty) WHERE q.nameKey IS NOT NULL AND q.name =~ '.*[A-Za-z].*' MATCH (:Contact {nameKey: q.nameKey, contactType: 'CorporateOwner'}) } RETURN count(d) AS mortgages }
CALL () { MATCH (d:Document {docType: 'MTGE'})-[r:HAS_PARTY]->(:DocumentParty) WHERE NOT r.partyType IN [1, 2]
          AND EXISTS { MATCH (d)-[:HAS_PARTY]->(q:DocumentParty) WHERE q.nameKey IS NOT NULL AND q.name =~ '.*[A-Za-z].*' MATCH (:Contact {nameKey: q.nameKey, contactType: 'CorporateOwner'}) }
          RETURN count(r) AS other }
RETURN mortgages, other
"""
SINGLE = """
MATCH (d:Document {docType: 'MTGE'}) WHERE EXISTS { MATCH (d)-[:HAS_PARTY]->(q:DocumentParty) WHERE q.nameKey IS NOT NULL AND q.name =~ '.*[A-Za-z].*' MATCH (:Contact {nameKey: q.nameKey, contactType: 'CorporateOwner'}) } MATCH (d)-[:HAS_PARTY]->(p:DocumentParty) WITH d, count(DISTINCT p) AS n WHERE n < 2 RETURN d.documentId AS id ORDER BY id
"""
SOURCE_DISTINCT = """SELECT count(*) FROM (SELECT DISTINCT nullif(btrim(name), ''), nullif(btrim(address1), ''), nullif(btrim(address2), ''),
nullif(btrim(zip), '') FROM real_property_parties WHERE documentid = %(doc)s) t"""
SAMPLE_IDS = "MATCH (d:Document {docType: 'MTGE'}) WHERE EXISTS { MATCH (d)-[:HAS_PARTY]->(q:DocumentParty) WHERE q.nameKey IS NOT NULL AND q.name =~ '.*[A-Za-z].*' MATCH (:Contact {nameKey: q.nameKey, contactType: 'CorporateOwner'}) } RETURN d.documentId AS id ORDER BY id"
GRAPH_DOC = """
MATCH (d:Document {documentId: $id})-[r:HAS_PARTY]->(p:DocumentParty)
RETURN collect([r.partyType, p.name]) AS parties
"""
SOURCE_DOC = "SELECT DISTINCT partytype, nullif(btrim(name), '') FROM real_property_parties WHERE documentid = %(doc)s"
SOURCE_TYPE = """SELECT doctype FROM real_property_master WHERE documentid = %(doc)s
ORDER BY modifieddate DESC NULLS LAST, goodthroughdate DESC NULLS LAST LIMIT 1"""


def main() -> int:
    load_dotenv(ROOT / ".env")
    missing = [k for k in REQUIRED_ENV if not os.environ.get(k)]
    if missing:
        print(f"missing in .env: {', '.join(missing)}", file=sys.stderr)
        return 1
    fx = yaml.safe_load((HERE / "fixtures.yaml").read_text())
    lookup = (HERE / "lookup.cypher").read_text()
    expected = (HERE / "expected.sql").read_text()
    driver = GraphDatabase.driver(os.environ["NEO4J_URI"], auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]))
    with driver, driver.session(database=os.environ["NEO4J_DATABASE"], default_access_mode="READ") as session:
        g = session.run(GRAPH_TOTALS).single()
        check("mortgage count equals the fixture total", g["mortgages"] == fx["totals"]["mortgages"],
              f"graph {g['mortgages']} vs fixture {fx['totals']['mortgages']}")
        check("every mortgage party type is 1 (borrower) or 2 (lender)", g["other"] == 0, f"{g['other']} other")
        with psycopg.connect(os.environ["JUSTFIX_DATABASE_URL"]) as pg:
            pg.read_only = True
            with pg.cursor() as cur:
                for e in fx["entities"]:
                    cur.execute(expected, {"name": " ".join(e["name"].upper().split())})
                    src = {}
                    for doc, rec, _dd, amt, ptype, name, _a, _z in cur.fetchall():
                        d = src.setdefault(doc, {"recorded": str(rec), "amount": int(amt) if amt is not None else None, "b": [], "l": []})
                        d["b" if ptype == 1 else "l"].append(name)
                    want = {d["id"]: d for d in e["documents"]}
                    gap = e["documents"] == []
                    if gap:
                        check(f"{e['name']}: source has the gap documents", sorted(src) == sorted(e["source_documents"]), f"source {sorted(src)}")
                    rows = session.run(lookup, nameKey=n3(e["name"])).data()
                    got = {r["documentId"]: r for r in rows}
                    if gap:
                        # Scope F (Q13) loads the mortgage by lot, so a name lookup now finds it; it is still not a scope M mortgage (no HPD owner name).
                        fin = {r["id"] for r in session.run("MATCH (:Lot)-[:HAS_FINANCING_DOCUMENT]->(d:Document) WHERE d.documentId IN $ids RETURN DISTINCT d.documentId AS id", ids=e["source_documents"])}
                        check(f"{e['name']}: the gap document is in the graph only through scope F (a lot link, no HPD owner name)",
                              sorted(got) == sorted(e["source_documents"]) == sorted(fin), f"graph {sorted(got)} lot-linked {sorted(fin)}")
                    else:
                        check(f"{e['name']}: documents match fixture", sorted(got) == sorted(want), f"graph {sorted(got)} vs fixture {sorted(want)}")
                    for doc, w in want.items():
                        r, s = got.get(doc), src.get(doc)
                        if r is None or s is None:
                            check(f"{doc}: present in graph and source", False)
                            continue
                        b = sorted(p["name"] for p in r["parties"] if p["partyType"] == 1)
                        l = sorted(p["name"] for p in r["parties"] if p["partyType"] == 2)
                        check(f"{doc}: roles equal fixture and source", b == sorted(w["borrowers"]) == sorted(s["b"])
                              and l == sorted(w["lenders"]) == sorted(s["l"]) and w["given_role"] in r["givenRoles"],
                              f"graph b={len(b)} l={len(l)}")
                        check(f"{doc}: date and amount equal fixture and source",
                              str(r["recordedDate"]) == w["recorded"] == s["recorded"] and r["amount"] == w["amount"] == s["amount"])
                single = [r["id"] for r in session.run(SINGLE)]
                check("single-party mortgages equal the fixture", len(single) == fx["totals"]["single_party_mortgages"], f"graph {len(single)}")
                counts = []
                for doc in single:
                    cur.execute(SOURCE_DISTINCT, {"doc": doc})
                    counts.append(cur.fetchone()[0])
                check("each single-party mortgage has one distinct party row in the source", all(c == 1 for c in counts), f"{counts}")
                ids = [r["id"] for r in session.run(SAMPLE_IDS)]
                for doc in ids[:: max(1, len(ids) // 40)]:
                    cur.execute(SOURCE_DOC, {"doc": doc})
                    src = sorted((int(a), b or "") for a, b in cur.fetchall())
                    cur.execute(SOURCE_TYPE, {"doc": doc})
                    t = cur.fetchone()
                    got = sorted((int(a), b or "") for a, b in session.run(GRAPH_DOC, id=doc).single()["parties"])
                    check(f"{doc} parties and type match source", got == src and t is not None and t[0] == "MTGE", f"graph {len(got)} vs source {len(src)}")
    failed = results.count(False)
    print(f"{len(results) - failed}/{len(results)} checks passed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
