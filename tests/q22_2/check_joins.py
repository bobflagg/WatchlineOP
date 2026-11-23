"""Check Q22.2: lots on which both names are deed parties, from the source (ACRIS) and from the graph. Read-only.
Run: uv run python tests/q22_2/check_joins.py
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from q5_support import check, connect, finish, load_fixtures, n3  # noqa: E402

HERE = Path(__file__).resolve().parent
SQL = """
SELECT DISTINCT l.bbl::text FROM real_property_parties p JOIN real_property_legals l USING (documentid)
WHERE upper(btrim(p.name)) = %(n)s
"""


def main() -> int:
    fx = load_fixtures(HERE)
    lookup = (HERE / "lookup.cypher").read_text()
    driver, pg = connect()
    with driver, driver.session(database=os.environ["NEO4J_DATABASE"], default_access_mode="READ") as session, pg, pg.cursor() as cur:
        for f in fx["pairs"]:
            src, gr = [], []
            for name in (f["a"], f["b"]):
                cur.execute(SQL, {"n": name.upper()})
                src.append({r[0] for r in cur.fetchall()})
                rows = session.run(lookup, key=n3(name)).data()
                gr.append({r["ref"] for r in rows if r["kind"] == "deed-party"})
            check(f"{f['a']} / {f['b']}: shared lots from source equal fixture", sorted(src[0] & src[1]) == f["shared_lots"], f"source gives {sorted(src[0] & src[1])}")
            check(f"{f['a']} / {f['b']}: shared deed lots from graph equal fixture", sorted(gr[0] & gr[1]) == f["shared_lots"], f"graph gives {sorted(gr[0] & gr[1])}")
    return finish()


if __name__ == "__main__":
    sys.exit(main())
