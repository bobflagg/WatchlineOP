"""Check the Operational Network address masks (Q6.2) against the pinned BOR release and the frozen source. Read-only everywhere.

1. The release facts (73 masks, one method, one normalizer, one threshold, degrees above the threshold) match the fixture.
2. Each fixture is re-derived from the release (id and degree) and from the source with tests/q6_2/expected.sql.
3. Each fixture is looked up in the graph with tests/q6_2/lookup.cypher; the graph's masks equal the release's.
Any failure or error is a failure. Run: uv run python tests/q6_2/check_masked.py
"""

import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from bor_support import check, connect, finish, load_fixtures  # noqa: E402


def main() -> int:
    driver, pg, release = connect()
    fx = load_fixtures(HERE / "fixtures.yaml")
    expected = (HERE / "expected.sql").read_text()
    lookup = (HERE / "lookup.cypher").read_text()
    t = fx["totals"]
    rel = {r["address"]: r for r in release.rows("masked_addresses")}
    ids = {r["address_id"] for r in rel.values()}
    degrees = [int(r["degree"]) for r in rel.values()]
    nodes = sum(1 for _ in release.rows("masked_address_nodes"))
    check("release: 73 masked addresses with distinct texts", len(rel) == t["masked_addresses"] and len(ids) == len(rel), f"{len(rel)}")
    check("release: one method, normalizer, threshold, unit, decision",
          {r["method"] for r in rel.values()} == {t["method"]} and {r["normalizer_version"] for r in rel.values()} == {t["normalizer_version"]}
          and {int(r["threshold"]) for r in rel.values()} == {t["threshold"]} and {r["degree_unit"] for r in rel.values()} == {t["degree_unit"]}
          and {r["decision"] for r in rel.values()} == {"masked"})
    check("release: degrees are above the threshold and span the fixture range",
          min(degrees) == t["degree_min"] and max(degrees) == t["degree_max"] and min(degrees) > t["threshold"], f"{min(degrees)} to {max(degrees)}")
    check("release: masked_address_nodes rows match fixture", nodes == t["masked_nodes"], f"{nodes}")
    from collections import Counter
    set_aside = Counter(r["evidence_id"] for r in release.rows("graph_edges", drop_reason="address_mask"))
    check("release: set-aside address edges cite only masked addresses and match fixture",
          set(set_aside) <= ids and sum(set_aside.values()) == t["masked_edges"] and set(set_aside) == ids, f"{sum(set_aside.values())}")

    with driver, driver.session(database=os.environ["NEO4J_DATABASE"], default_access_mode="READ") as session, pg.cursor() as cur:
        for f in fx["masked"]:
            a = f["address"]
            r = rel.get(a)
            check(f"{a}: release row matches fixture", r is not None and r["address_id"] == f["addressId"] and int(r["degree"]) == f["degree"], f"release gives {r}")
            cur.execute(expected, {"address": a})
            contacts, zips = cur.fetchone()
            check(f"{a}: source HPD contacts and ZIPs match fixture", (contacts, list(zips)) == (f["hpdContacts"], f["hpdZips"]), f"source gives {contacts} {zips}")
            g = session.run(lookup, address=a).data()
            got = [(x["addressId"], x["degree"], x["hpdContacts"], sorted(x["hpdZips"])) for x in g]
            check(f"{a}: graph matches fixture", got == [(f["addressId"], f["degree"], f["hpdContacts"], f["hpdZips"])], f"graph has {got}")
        for f in fx["not_masked"]:
            check(f"{f['address']}: not in the release", f["address"] not in rel)
            check(f"{f['address']}: not masked in the graph", session.run(lookup, address=f["address"]).data() == [])
        graph_masks = {r["address"]: (r["id"], r["degree"], r["edges"]) for r in session.run(
            "MATCH (a:NetworkMaskedAddress) RETURN a.address AS address, a.addressId AS id, a.degree AS degree, a.maskedEdges AS edges")}
        check("graph masks equal the release masks (id, degree and set-aside edges)",
              graph_masks == {a: (r["address_id"], int(r["degree"]), set_aside.get(r["address_id"], 0)) for a, r in rel.items()})
        matched = 0
        for a in rel:
            cur.execute(expected, {"address": a})
            matched += cur.fetchone()[0] > 0
        check("masked addresses carried by an HPD contact match fixture", matched == t["masked_with_hpd_contacts"], f"{matched}")
    return finish()


if __name__ == "__main__":
    sys.exit(main())
