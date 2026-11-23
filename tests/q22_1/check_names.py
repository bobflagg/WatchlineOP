"""Check Q22.1 name comparisons. Read-only on the source. Pure rule check plus source-spelling check; no graph needed.

1. Each fixture pair gives the expected outcome and rule from compare.entity_name_comparison, in both argument orders.
2. Each recorded spelling in a pair exists in its source table (so a stale fixture fails).
3. Regression: Q3 name_agreement and Q5 dos_name_agreement still treat KS / K S as different.
Run: uv run python tests/q22_1/check_names.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from q5_support import check, connect, finish, load_fixtures  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from watchline.compare import dos_name_agreement, entity_name_comparison, n1, name_agreement  # noqa: E402

HERE = Path(__file__).resolve().parent
SOURCES = {
    "hpd_contacts": "SELECT 1 FROM hpd_contacts WHERE upper(btrim(corporationname)) = %(n)s LIMIT 1",
    "real_property_parties": "SELECT 1 FROM real_property_parties WHERE upper(btrim(name)) = %(n)s LIMIT 1",
    "dos_active_corporations": "SELECT 1 FROM dos_active_corporations WHERE upper(btrim(currententityname)) = %(n)s LIMIT 1",
}


def main() -> int:
    fx = load_fixtures(HERE)
    driver, pg = connect()
    with driver, pg, pg.cursor() as cur:
        for f in fx["pairs"] + fx["synthetic"]:
            for x, y in ((f["a"], f["b"]), (f["b"], f["a"])):
                got = entity_name_comparison(x, y)
                check(f"{x} / {y}", (got["outcome"], got["rule"]) == (f["outcome"], f["rule"]), f"got {got}")
        for f in fx["pairs"]:
            for side in ("a", "b"):
                src = f.get(f"{side}_source")
                if src:
                    cur.execute(SOURCES[src], {"n": n1(f[side])})
                    check(f"{f[side]} recorded in {src}", cur.fetchone() is not None)
    check("Q3 keeps a space a difference", name_agreement("KS TURNPIKE LLC", "K S TURNPIKE LLC")["outcome"] == "different")
    check("Q5 keeps a space a difference", dos_name_agreement("KS TURNPIKE LLC", "K S TURNPIKE LLC")["outcome"] == "different")
    return finish()


if __name__ == "__main__":
    sys.exit(main())
