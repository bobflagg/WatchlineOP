"""Check Q13.2 (parties of the financing documents of a lot) against the frozen source.

For each fixture document: re-derive its distinct party rows from the source (tests/q13_2/expected.sql), look them up with
tests/q13_2/lookup.cypher on the fixture lot and compare every row (type code, name, address, zip as recorded). The party-type counts equal the
fixture. A document with no party row in the source has none in the graph. Person names are never printed. Any failure is a failure.
Run: uv run python tests/q13_2/check_parties.py
"""

import os
import sys
from collections import Counter
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from q13_support import check, connect, finish, party_rows, source_documents, source_parties  # noqa: E402
sys.path.insert(0, str(HERE.parent.parent / "src"))
from watchline.compare import n3  # noqa: E402


def main() -> int:
    fx = yaml.safe_load((HERE / "fixtures.yaml").read_text())
    lookup = (HERE / "lookup.cypher").read_text()
    driver, pg = connect()
    with driver, pg, driver.session(database=os.environ["NEO4J_DATABASE"], default_access_mode="READ") as s, pg.cursor() as cur:
        for lot in sorted({d["bbl"] for d in fx["documents"]}):
            src_docs = source_documents(cur, lot)
            src_parties = source_parties(cur, list(src_docs))
            rows = {r["documentId"]: r for r in s.run(lookup, bbl=lot).data()}
            check(f"{lot}: every document's party rows equal the source",
                  all(party_rows(r["parties"]) == src_parties.get(doc) for doc, r in rows.items()) and sorted(rows) == sorted(src_docs),
                  f"{sum(1 for doc, r in rows.items() if party_rows(r['parties']) != src_parties.get(doc))} differ")
            check(f"{lot}: every named party carries the N3 name key",
                  all((p["nameKey"] == n3(p["name"])) for r in rows.values() for p in r["parties"] if p["name"] and n3(p["name"])))
            for d in (x for x in fx["documents"] if x["bbl"] == lot):
                r = rows.get(d["id"])
                if r is None:
                    check(f"{d['id']}: present in the graph", False)
                    continue
                check(f"{d['id']}: type and party-type counts equal the fixture",
                      r["docType"] == d["type"] and dict(Counter(p["partyType"] for p in r["parties"])) == d["party_types"],
                      str(dict(Counter(p["partyType"] for p in r["parties"]))))
                if "borrowers" in d:
                    check(f"{d['id']}: borrowers (party type 1) are as recorded",
                          sorted(p["name"] for p in r["parties"] if p["partyType"] == 1) == sorted(d["borrowers"]))
        # A financing document with no party row in the source has none in the graph (the profile found none on the rental lots; this guards a regression).
        check("no financing document is loaded without a party row",
              s.run("MATCH (:Lot)-[:HAS_FINANCING_DOCUMENT]->(d:Document) WHERE NOT (d)-[:HAS_PARTY]->() RETURN count(DISTINCT d) AS n").single()["n"] == 0)
    return finish()


if __name__ == "__main__":
    sys.exit(main())
