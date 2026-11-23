"""Check Q13.3 (financing documents by kind: mortgage, assignment, satisfaction, termination, agreement) against the frozen source.

Re-derives each fixture lot's documents from the source (tests/q13_1/expected.sql), groups them by the answer contract's KINDS (tests/q13_support.py),
and compares with the graph's per-type counts grouped the same way and with the fixture. Every loaded document type has a kind and a description.
No satisfaction after the latest mortgage is reported as a recorded fact, never as an outstanding loan. Run: uv run python tests/q13_3/check_kinds.py
"""

import os
import sys
from collections import Counter
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from q13_support import FINANCING_TYPES, KINDS, check, connect, finish, source_documents  # noqa: E402


def main() -> int:
    fx = yaml.safe_load((HERE / "fixtures.yaml").read_text())
    lookup = (HERE / "lookup.cypher").read_text()
    driver, pg = connect()
    with driver, pg, driver.session(database=os.environ["NEO4J_DATABASE"], default_access_mode="READ") as s, pg.cursor() as cur:
        check("every financing type has a kind and a description", all(t in KINDS and all(KINDS[t]) for t in FINANCING_TYPES))
        loaded = {r["t"] for r in s.run("MATCH (:Lot)-[:HAS_FINANCING_DOCUMENT]->(d:Document) RETURN DISTINCT d.docType AS t")}
        check("every loaded document type has a kind", loaded <= set(KINDS), str(sorted(loaded - set(KINDS))))
        for f in fx["lots"]:
            src = source_documents(cur, f["bbl"])
            src_kinds = Counter(KINDS[d["type"]][0] for d in src.values())
            graph_kinds = Counter()
            for r in s.run(lookup, bbl=f["bbl"]).data():
                graph_kinds[KINDS[r["docType"]][0]] += r["documents"]
            want = {k: v for k, v in f["by_kind"].items() if v}
            check(f"{f['bbl']}: counts by kind equal the source", dict(graph_kinds) == dict(src_kinds), f"graph {dict(graph_kinds)} vs source {dict(src_kinds)}")
            check(f"{f['bbl']}: counts by kind equal the fixture", dict(graph_kinds) == want, str(dict(graph_kinds)))
            check(f"{f['bbl']}: satisfaction dates equal the fixture",
                  sorted(d["recorded"] for d in src.values() if d["type"] == "SAT") == f["satisfaction_dates"])
            if "termination_dates" in f:
                check(f"{f['bbl']}: termination dates equal the fixture",
                      sorted(d["recorded"] for d in src.values() if d["type"] == "TL&R") == f["termination_dates"])
            latest_mtge = max((d["recorded"] for d in src.values() if d["type"] == "MTGE"), default=None)
            later_sat = [d for d in src.values() if d["type"] == "SAT" and latest_mtge and d["recorded"] > latest_mtge]
            check(f"{f['bbl']}: no satisfaction is recorded after the latest mortgage (a record fact, not an outstanding loan)", not later_sat)
    return finish()


if __name__ == "__main__":
    sys.exit(main())
