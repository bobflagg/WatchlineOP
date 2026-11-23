"""Check Q14.3 (do the title holder and the registered owner coincide on a date, a computed name lead) against the frozen source.

Each fixture case derives the relation from the source (Q14.1 and Q14.2 SQL, rule N3 in tests/q14_support.py), looks it up with
tests/q14_3/lookup.cypher and compares the relation and the supporting deeds; both equal the fixture. Any failure or error is a failure.
Run: uv run python tests/q14_3/check_relation.py
"""

import os
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from q14_support import check, connect, finish, relation, source_registrations, source_title  # noqa: E402


def main() -> int:
    fx = yaml.safe_load((HERE / "fixtures.yaml").read_text())
    lookup = (HERE / "lookup.cypher").read_text()
    driver, pg = connect()
    with driver, pg, driver.session(database=os.environ["NEO4J_DATABASE"], default_access_mode="READ") as s, pg.cursor() as cur:
        for f in fx["cases"]:
            label = f"{f['bbl']} {f['date']} [{f['basis']}]"
            title = source_title(cur, f["bbl"], f["date"], f["basis"])
            regs = source_registrations(cur, f["bbl"], f["date"])
            src_rel = relation(title, regs)
            check(f"{label}: the source relation equals the fixture", src_rel == f["relation"], f"source {src_rel}")
            r = s.run(lookup, bbl=f["bbl"], date=f["date"], basis=f["basis"]).single()
            check(f"{label}: the graph relation equals the source", r is not None and r["relation"] == src_rel, f"graph {r['relation'] if r else None}")
            if r is not None:
                check(f"{label}: supporting deeds equal the source", sorted(r["deeds"]) == sorted(title), f"graph {len(r['deeds'])} vs source {len(title)}")
                n_inforce = sum(1 for x in regs.values() if x["status"] == "in-force")
                check(f"{label}: registrations in force equal the source", r["registrationsInForce"] == n_inforce, f"graph {r['registrationsInForce']}")
    return finish()


if __name__ == "__main__":
    sys.exit(main())
