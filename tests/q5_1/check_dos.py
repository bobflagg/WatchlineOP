"""Check Q5.1 DOS candidates. Read-only on both databases.

1. Each input name: candidates from SQL (expected.sql rule N3), from compare.py, and from the graph must equal the fixture; outcome and rule
   come from compare.dos_name_agreement.
2. Each fixture record's type, jurisdiction and filing date are re-derived from the source and read from the graph.
3. The out-of-scope record is absent; every DosEntity has a name key equal to N3 of its name.
Run: uv run python tests/q5_1/check_dos.py
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from q5_support import SOURCE_CANDIDATES, check, connect, dos_name_agreement, finish, load_fixtures, n3, source_record  # noqa: E402

HERE = Path(__file__).resolve().parent


def main() -> int:
    fx = load_fixtures(HERE)
    lookup = (HERE / "lookup.cypher").read_text()
    driver, pg = connect()
    with driver, driver.session(database=os.environ["NEO4J_DATABASE"], default_access_mode="READ") as session, pg, pg.cursor() as cur:
        for f in fx["names"]:
            exp = sorted((c[0], c[1], c[2]) for c in f["candidates"])
            cur.execute(SOURCE_CANDIDATES, {"name": f["name"]})
            ids = [r[0] for r in cur.fetchall()]
            derived = sorted((i, *[dos_name_agreement(f["name"], source_record(cur, i)["name"])[k] for k in ("outcome", "rule")]) for i in ids)
            check(f"{f['name']}: source candidates match fixture", derived == exp, f"source gives {derived}")
            rows = session.run(lookup, key=n3(f["name"])).data()
            got = sorted((r["dosId"], *[dos_name_agreement(f["name"], r["name"])[k] for k in ("outcome", "rule")]) for r in rows)
            check(f"{f['name']}: graph candidates match fixture", got == exp, f"graph has {got}")
        for r in fx["records"]:
            src = source_record(cur, r["dosId"])
            exp = (r["entityType"], r["jurisdiction"], r["filingDate"])
            check(f"{r['dosId']} fixture matches source", src is not None and (src["entityType"], src["jurisdiction"], src["filingDate"]) == exp)
            row = session.run("MATCH (e:DosEntity {dosId: $id}) RETURN e.entityType AS t, e.jurisdiction AS j, toString(e.filingDate) AS d", id=r["dosId"]).single()
            check(f"{r['dosId']} graph matches fixture", row is not None and (row["t"], row["j"], row["d"]) == exp, f"graph has {row and dict(row)}")
        for dosid in fx["absent"]:
            check(f"{dosid} out of scope and absent", session.run("MATCH (e:DosEntity {dosId: $id}) RETURN e", id=dosid).single() is None)
        rows = session.run("MATCH (e:DosEntity) RETURN e.dosId AS id, e.name AS n, e.nameKey AS k").data()
        bad = [r["id"] for r in rows if n3(r["n"]) != r["k"]]
        check("every DosEntity name key equals N3 of its name", rows and not bad, f"{len(bad)} differ")
        check("every DosEntity is unique by dosId", len({r["id"] for r in rows}) == len(rows))
    return finish()


if __name__ == "__main__":
    sys.exit(main())
