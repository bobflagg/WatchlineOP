"""Check Q18.2 (independent signals for zero-transfer deeds) against the frozen source.

Signals are re-derived from the source (deeds, PLUTO address, HPD corporate owners, rule N3) and compared with tests/q18_2/lookup.cypher per
deed: granteeNamedForLot, sameName, follow-on documents, granteeRegisteredOwner and the signal count. Only zero-transfer deeds appear. Any failure
or error is a failure. Run: uv run python tests/q18_2/check_signals.py
"""

import os
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from q18_support import check, connect, finish, signals  # noqa: E402


def main() -> int:
    fx = yaml.safe_load((HERE / "fixtures.yaml").read_text())
    lookup = (HERE / "lookup.cypher").read_text()
    driver, pg = connect()
    with driver, pg, driver.session(database=os.environ["NEO4J_DATABASE"], default_access_mode="READ") as s, pg.cursor() as cur:
        for f in fx["lots"]:
            label = f"{','.join(f['bbls'])} [{f.get('start')}..{f.get('end')}]"
            src = signals(cur, f["bbls"], f.get("start"), f.get("end"))
            rows = s.run(lookup, bbls=f["bbls"], start=f.get("start"), end=f.get("end")).data()
            got = {r["documentId"]: r for r in rows}
            check(f"{label}: zero-transfer deeds equal the source and the fixture", len(rows) == len(got) and sorted(got) == sorted(src) and len(got) == f["zero_transfers"],
                  f"graph {len(got)}, source {len(src)}, fixture {f['zero_transfers']}")
            for doc, e in src.items():
                r = got.get(doc)
                if r is None:
                    continue
                check(f"{doc}: signals equal the source",
                      r["granteeNamedForLot"] == e["named"] and r["sameName"] == e["same"] and r["granteeRegisteredOwner"] == e["owner"]
                      and {d["documentId"] for d in r["followOn"]} == e["followOn"]
                      and r["signals"] == sum([e["named"], e["same"], bool(e["followOn"]), e["owner"]]),
                      f"graph {r['granteeNamedForLot']}/{r['sameName']}/{len(r['followOn'])}/{r['granteeRegisteredOwner']}")
            for w in f.get("documents", []):
                r = got.get(w["id"])
                check(f"{w['id']}: fixture signals hold",
                      r is not None and r["granteeNamedForLot"] == w["named"] and r["sameName"] == w["same"] and r["granteeRegisteredOwner"] == w["owner"]
                      and sorted(d["documentId"] for d in r["followOn"]) == sorted(w["follow_on"]))
    return finish()


if __name__ == "__main__":
    sys.exit(main())
