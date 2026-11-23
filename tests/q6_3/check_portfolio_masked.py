"""Check the Owner Portfolio address masks (Q6.3) against the pinned BOR release and the frozen source. Read-only everywhere.

The release records this mask on identities (rule splink_address_evidence_mask, detail addr_degree), never on addresses. The address of each
masked identity is its own business address in identity_names (house, street and apartment, blanks left out, single spaces).
1. Release: 5298 events, all identity events of the base Splink stage with only addr_degree; they derive 579 texts, each with one degree.
2. Each fixture is re-derived from the release; the HPD contacts and ZIPs of each are counted from the source with expected.sql.
3. Each fixture is looked up in the graph with lookup.cypher; the graph's masks equal the derived ones.
Any failure or error is a failure. Run: uv run python tests/q6_3/check_portfolio_masked.py
"""

import json
import os
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from bor_support import check, connect, finish, load_fixtures  # noqa: E402


def main() -> int:
    driver, pg, release = connect()
    fx = load_fixtures(HERE / "fixtures.yaml")
    t = fx["totals"]
    expected = (HERE / "expected.sql").read_text()
    lookup = (HERE / "lookup.cypher").read_text()
    for table in ("decision_events", "identity_names"):
        check(f"{table}.csv checksum matches the manifest", release.verify_member(table))
    events = list(release.rows("decision_events", rule=t["method_rule"]))
    check("events: all identity events of the base Splink stage, outcome masked, detail only addr_degree",
          len(events) == t["masked_identities"] and {(e["layer"], e["stage"], e["subject_type"], e["outcome"]) for e in events} == {("identity", t["stage"], "identity", "masked")}
          and Counter(k for e in events for k in json.loads(e["detail"])) == Counter({"addr_degree": len(events)}), f"{len(events)}")
    text = {r["identity_id"]: " ".join(p.strip() for p in (r["business_house"], r["business_street"], r["business_apartment"]) if p and p.strip())
            for r in release.rows("identity_names")}
    check("every masked identity has a business address in identity_names", all(text.get(e["subject_id"]) for e in events))
    degrees: dict[str, set] = {}
    counts: Counter = Counter()
    for e in events:
        a = text[e["subject_id"]]
        degrees.setdefault(a, set()).add(int(json.loads(e["detail"])["addr_degree"]))
        counts[a] += 1
    check("derived: 579 texts, one degree each, all above the threshold, spanning the fixture range",
          len(degrees) == t["addresses"] and all(len(v) == 1 for v in degrees.values())
          and min(min(v) for v in degrees.values()) == t["degree_min"] and max(max(v) for v in degrees.values()) == t["degree_max"]
          and t["degree_min"] > t["threshold"], f"{len(degrees)}")
    net = {r["address"]: int(r["degree"]) for r in release.rows("masked_addresses")}
    both = [a for a in degrees if a in net]
    check("derived: texts also masked by the network method and those with a different degree match fixture",
          (len(both), sum(1 for a in both if net[a] != next(iter(degrees[a])))) == (t["also_network_masked"], t["degree_differs_from_network"]), f"{len(both)}")

    with driver, driver.session(database=os.environ["NEO4J_DATABASE"], default_access_mode="READ") as session, pg.cursor() as cur:
        for f in fx["masked"]:
            a = f["address"]
            check(f"{a}: release derivation matches fixture", a in degrees and next(iter(degrees[a])) == f["degree"] and counts[a] == f["maskedIdentities"],
                  f"release gives {degrees.get(a)} {counts.get(a)}")
            cur.execute(expected, {"address": a})
            contacts, zips = cur.fetchone()
            g = session.run(lookup, address=a).data()
            got = [(x["address"], x["degree"], x["maskedIdentities"], x["hpdContacts"], sorted(x["hpdZips"])) for x in g]
            check(f"{a}: graph matches fixture and the source's HPD contacts and ZIPs",
                  got == [(a, f["degree"], f["maskedIdentities"], contacts, list(zips))], f"graph has {got}, source gives {contacts} {zips}")
        for f in fx["not_masked"]:
            check(f"{f['address']}: not derived from the release", f["address"] not in degrees)
            check(f"{f['address']}: not masked in the graph", session.run(lookup, address=f["address"]).data() == [])
        graph = {r["a"]: (r["d"], r["n"]) for r in session.run(
            "MATCH (m:PortfolioMaskedAddress) RETURN m.address AS a, m.degree AS d, m.maskedIdentities AS n")}
        check("graph masks equal the derived masks (degree and identity count)", graph == {a: (next(iter(v)), counts[a]) for a, v in degrees.items()},
              f"{len(graph)} in graph vs {len(degrees)}")
        labels = {r["label"] for r in session.run("CALL db.labels() YIELD label RETURN label")}
        check("the graph has no per-identity mask node", not any("Identity" in l for l in labels))
    pg.close()
    return finish()


if __name__ == "__main__":
    sys.exit(main())
