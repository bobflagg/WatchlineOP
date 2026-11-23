"""Check Q13.1 (financing documents recorded against a lot) against the frozen source.

For each fixture lot: re-derive the documents from the source (tests/q13_1/expected.sql), look them up with tests/q13_1/lookup.cypher and compare
ids, types, dates, amounts and the other-lot count; compare per-type counts and the witnesses. Then: every loaded financing document has a
financing type and a lot, no document of another type is linked, and one multi-lot document found in the graph is re-derived from the source.
Count documents, not links. Any failure or error is a failure. Run: uv run python tests/q13_1/check_documents.py
"""

import os
import sys
from collections import Counter
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from q13_support import FINANCING_TYPES, check, connect, finish, source_documents  # noqa: E402


def compare(label, rows, src):
    got = {r["documentId"]: r for r in rows}
    check(f"{label}: documents equal the source", sorted(got) == sorted(src), f"graph {len(got)} vs source {len(src)}")
    check(f"{label}: no document is returned twice", len(got) == len(rows))
    for doc, r in got.items():
        d = src.get(doc)
        if d is None:
            continue
        ok = (r["docType"] == d["type"] and (str(r["recordedDate"]) if r["recordedDate"] else None) == d["recorded"]
              and (str(r["docDate"]) if r["docDate"] else None) == d["docdate"] and r["amount"] == d["amount"])
        check(f"{doc}: type, dates and amount equal the source", ok)
    return got


def main() -> int:
    fx = yaml.safe_load((HERE / "fixtures.yaml").read_text())
    lookup = (HERE / "lookup.cypher").read_text()
    driver, pg = connect()
    with driver, pg, driver.session(database=os.environ["NEO4J_DATABASE"], default_access_mode="READ") as s, pg.cursor() as cur:
        for f in fx["lots"]:
            src = source_documents(cur, f["bbl"])
            rows = s.run(lookup, bbl=f["bbl"]).data()
            got = compare(f["bbl"], rows, src)
            if "documents" in f:
                check(f"{f['bbl']}: document count equals the fixture", len(rows) == f["documents"] == len(src), f"graph {len(rows)}")
            if "by_type" in f:
                check(f"{f['bbl']}: counts by type equal the fixture", dict(Counter(r["docType"] for r in rows)) == f["by_type"],
                      str(dict(Counter(r["docType"] for r in rows))))
            for w in f.get("witnesses", []):
                r = got.get(w["id"])
                ok = r is not None and r["docType"] == w["type"] and r["amount"] == w["amount"] \
                    and (str(r["recordedDate"]) if r["recordedDate"] else None) == w["recorded"] \
                    and (str(r["docDate"]) if r["docDate"] else None) == w["docdate"]
                if "other_lots" in w:
                    ok = ok and r["otherLots"] == w["other_lots"]
                check(f"{w['id']}: fixture witness matches", ok)
        check("only financing types are linked to a lot",
              s.run("MATCH (:Lot)-[:HAS_FINANCING_DOCUMENT]->(d:Document) WHERE NOT d.docType IN $t RETURN count(d) AS n", t=FINANCING_TYPES).single()["n"] == 0)
        check("every linked document has a recorded date and a type",
              s.run("MATCH (:Lot)-[:HAS_FINANCING_DOCUMENT]->(d:Document) WHERE d.recordedDate IS NULL OR d.docType IS NULL RETURN count(d) AS n").single()["n"] == 0)
        multi = s.run("MATCH (d:Document)<-[:HAS_FINANCING_DOCUMENT]-(l:Lot) WITH d, collect(l.bbl) AS lots WHERE size(lots) >= 2 "
                      "RETURN d.documentId AS id, lots ORDER BY id LIMIT 1").single()
        check("a multi-lot document exists in the graph", multi is not None)
        if multi is not None:
            for bbl in multi["lots"][:2]:
                rows = s.run(lookup, bbl=bbl).data()
                src = source_documents(cur, bbl)
                r = next((x for x in rows if x["documentId"] == multi["id"]), None)
                srcdoc = src.get(multi["id"])
                # expected.sql returns only the queried lot, so read every lot of the document from the source legals
                cur.execute("SELECT DISTINCT bbl::text FROM real_property_legals WHERE documentid = %(doc)s", {"doc": multi["id"]})
                src_lots = {row[0] for row in cur.fetchall()}
                graph_lots = {r2["bbl"] for r2 in s.run("MATCH (l:Lot) WHERE l.bbl IN $b RETURN l.bbl AS bbl", b=list(src_lots))}
                in_graph = len(graph_lots) - 1
                check(f"{multi['id']} on {bbl}: counted once, other lots equal the source lots in the graph",
                      r is not None and srcdoc is not None and r["otherLots"] == in_graph, f"graph {r and r['otherLots']} vs {in_graph}")
    return finish()


if __name__ == "__main__":
    sys.exit(main())
