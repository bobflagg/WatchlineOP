"""Check Q18.1 (deeds on a lot set, classified correction / zero-transfer / priced) against the frozen source.

Each fixture lot set is re-derived from the source (tests/q12_1/expected.sql) and compared with tests/q18_1/lookup.cypher: the document set, the
classification, the lots each deed covers inside the set, and the counts in the fixture. Any failure or error is a failure.
Run: uv run python tests/q18_1/check_classification.py
"""

import os
import sys
from collections import Counter
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from q18_support import check, classify, connect, finish, source_deeds  # noqa: E402


def main() -> int:
    fx = yaml.safe_load((HERE / "fixtures.yaml").read_text())
    lookup = (HERE / "lookup.cypher").read_text()
    driver, pg = connect()
    with driver, pg, driver.session(database=os.environ["NEO4J_DATABASE"], default_access_mode="READ") as s, pg.cursor() as cur:
        for f in fx["lots"]:
            label = f"{','.join(f['bbls'])} [{f.get('start')}..{f.get('end')}]"
            src = source_deeds(cur, f["bbls"], f.get("start"), f.get("end"))
            rows = s.run(lookup, bbls=f["bbls"], start=f.get("start"), end=f.get("end")).data()
            got = {r["documentId"]: r for r in rows}
            check(f"{label}: deeds equal the source (each counted once)", len(rows) == len(got) and sorted(got) == sorted(src), f"graph {len(rows)}, source {len(src)}")
            check(f"{label}: classification equals the source", all(got[d]["classification"] == classify(src[d]) for d in src if d in got))
            check(f"{label}: covered lots inside the set equal the source", all(sorted(got[d]["lots"]) == sorted(set(src[d]["lots"]) & set(f["bbls"])) for d in src if d in got))
            counts = Counter(r["classification"] for r in rows)
            check(f"{label}: counts equal the fixture", dict(counts) == {k: v for k, v in f["counts"].items() if v}, f"graph {dict(counts)}")
            for w in f.get("documents", []):
                r = got.get(w["id"])
                check(f"{w['id']}: classification and amount equal the fixture", r is not None and r["classification"] == w["classification"] and r["amount"] == w["amount"])
    return finish()


if __name__ == "__main__":
    sys.exit(main())
