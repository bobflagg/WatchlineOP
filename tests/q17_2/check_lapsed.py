"""Check Q17.2 (has every registration of the lot ended before the as-of date?) against the frozen source.

Each fixture case is re-derived from the source (tests/q17_2/expected.sql): the registrations with their dates per (BIN, registrationid), and lapsed
derived from the end dates against the as-of date. The graph lookup (tests/q17_2/lookup.cypher) must give the same registrations, dates and answer,
and the answer must equal the fixture. Any failure or error is a failure. Run: uv run python tests/q17_2/check_lapsed.py
"""

import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from q17_support import check, connect, finish, graph_session, lapsed, source_registrations  # noqa: E402


def main() -> int:
    fx = yaml.safe_load((HERE / "fixtures.yaml").read_text())
    lookup = (HERE / "lookup.cypher").read_text()
    driver, pg = connect()
    with driver, pg, graph_session(driver) as s, pg.cursor() as cur:
        for f in fx["cases"]:
            label = f["bbl"]
            src = source_registrations(cur, f["bbl"])
            r = s.run(lookup, bbl=f["bbl"], asOf=fx["as_of"]).single()
            check(f"{label}: the lot is in the graph", r is not None)
            if r is None:
                continue
            got = {(x["bin"], x["registrationId"]): x for x in r["registrations"]}
            check(f"{label}: registrations equal the source", sorted(got) == sorted(src), f"graph {len(got)} vs source {len(src)}")
            check(f"{label}: registration count equals the fixture", len(got) == f["registrations"], f"graph {len(got)}")
            for key, d in src.items():
                x = got.get(key)
                if x is not None:
                    check(f"{label} {key}: dates equal the source",
                          (str(x["lastRegistered"]) if x["lastRegistered"] else None, str(x["registrationEnd"]) if x["registrationEnd"] else None)
                          == (d["lastRegistered"], d["registrationEnd"]))
            check(f"{label}: lapsed equals the source", r["lapsed"] == lapsed(src, fx["as_of"]), f"graph {r['lapsed']}")
            check(f"{label}: lapsed equals the fixture", r["lapsed"] == f["lapsed"], f"graph {r['lapsed']}")
    return finish()


if __name__ == "__main__":
    sys.exit(main())
