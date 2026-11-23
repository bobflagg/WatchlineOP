"""Check Q12.1 (deeds recorded for a lot in a period, with grantors, grantees and the not-a-sale count) against the frozen source.

1. Grantor totals and name keys: the graph's Grantor count equals the fixture total, every named Grantee and Grantor carries nameKey.
2. Each fixture lot and period is re-derived from the source (tests/q12_1/expected.sql), looked up with tests/q12_1/lookup.cypher and compared:
   the documents, dates, amount, type-based not-a-sale flag, other-lot count, and every grantor and grantee as recorded.
3. The deed and not-a-sale counts equal the fixture. Count deeds, not lots.
Person names are never printed. Any failure or error is a failure. Run: uv run python tests/q12_1/check_deeds.py
"""

import os
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from q12_support import check, connect, finish, n3, party_tuples, source_deeds  # noqa: E402


def main() -> int:
    fx = yaml.safe_load((HERE / "fixtures.yaml").read_text())
    lookup = (HERE / "lookup.cypher").read_text()
    driver, pg = connect()
    with driver, pg, driver.session(database=os.environ["NEO4J_DATABASE"], default_access_mode="READ") as s, pg.cursor() as cur:
        # A name of periods, commas and apostrophes only ("," or ".") is a placeholder: rule N3 leaves nothing, so it has no key.
        q = "MATCH (g:%s) RETURN count(g) AS n, " \
            "count(CASE WHEN g.name =~ '.*[A-Za-z0-9].*' THEN 1 END) AS named, " \
            "count(CASE WHEN g.name =~ '.*[A-Za-z0-9].*' AND g.nameKey IS NOT NULL THEN 1 END) AS keyed, " \
            "count(CASE WHEN g.name IS NOT NULL AND g.name =~ '[.,\\' ]*' AND g.nameKey IS NOT NULL THEN 1 END) AS wrongKey"
        g = s.run(q % "Grantor").single()
        check("grantor count equals the fixture total", g["n"] == fx["totals"]["grantors"], f"graph {g['n']} vs fixture {fx['totals']['grantors']}")
        check("every grantor name with a letter or digit carries a name key", g["named"] == g["keyed"], f"named {g['named']}, keyed {g['keyed']}")
        e = s.run(q % "Grantee").single()
        check("every grantee name with a letter or digit carries a name key", e["named"] == e["keyed"], f"named {e['named']}, keyed {e['keyed']}")
        check("punctuation-only names carry no name key", g["wrongKey"] == 0 and e["wrongKey"] == 0, f"{g['wrongKey']}, {e['wrongKey']}")
        for f in fx["lots"]:
            label = f"{f['bbl']} [{f.get('start')}..{f.get('end')}]"
            src = source_deeds(cur, [f["bbl"]], f.get("start"), f.get("end"))
            rows = s.run(lookup, bbl=f["bbl"], start=f.get("start"), end=f.get("end")).data()
            got = {r["documentId"]: r for r in rows}
            check(f"{label}: documents equal the source", sorted(got) == sorted(src), f"graph {len(got)} vs source {len(src)}")
            if "deeds" in f:
                check(f"{label}: deed count equals the fixture", len(rows) == f["deeds"] == len(src), f"graph {len(rows)}")
                check(f"{label}: not-a-sale count equals the fixture", sum(1 for r in rows if r["notSale"]) == f["not_sales"]
                      == sum(1 for d in src.values() if d["notSale"]))
            for doc, r in got.items():
                d = src.get(doc)
                if d is None:
                    continue
                check(f"{doc}: type, dates, amount and flag equal the source",
                      r["docType"] == d["type"] and str(r["recordedDate"]) == d["recorded"] and r["amount"] == d["amount"]
                      and (str(r["docDate"]) if r["docDate"] else None) == d["docdate"] and r["notSale"] == d["notSale"])
                check(f"{doc}: grantors and grantees equal the source",
                      party_tuples(r["grantors"]) == d["grantors"] and party_tuples(r["grantees"]) == d["grantees"],
                      f"graph {len(r['grantors'])}/{len(r['grantees'])} vs source {len(d['grantors'])}/{len(d['grantees'])}")
            for w in f.get("documents", []):
                r, d = got.get(w["id"]), src.get(w["id"])
                if r is None or d is None:
                    check(f"{w['id']}: present in graph and source", False)
                    continue
                check(f"{w['id']}: fixture matches (amount, flag, party names, other lots)",
                      r["amount"] == w["amount"] and r["notSale"] == w["not_sale"] and r["otherLots"] == w["other_lots"]
                      and (w["recorded"] is None or str(r["recordedDate"]) == w["recorded"])
                      and sorted(p["name"] for p in r["grantors"]) == sorted(w["grantors"])
                      and sorted(p["name"] for p in r["grantees"]) == sorted(w["grantees"]),
                      f"graph amount {r['amount']}, flag {r['notSale']}, other {r['otherLots']}")
        check("the same name on both sides is kept as recorded (anchor A, 2025 deed)",
              (lambda rows: any(sorted(p["nameKey"] for p in r["grantors"]) == sorted(p["nameKey"] for p in r["grantees"])
                                and r["documentId"] == "2025032100031001" for r in rows))(
                  s.run(lookup, bbl="3008260002", start="2025-01-01", end=None).data()))
    return finish()


if __name__ == "__main__":
    sys.exit(main())
