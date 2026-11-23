"""Check Q23.3 (an agent's business addresses and whether the Operational Network or Owner Portfolio method masked them) against the pinned BOR release and the frozen source.

Masks are re-derived from the release (masked_addresses; decision_events + identity_names, as tests/q6_3). Address candidates come from the source.
Every graph address must be a source candidate and its mask degrees must equal the release's. Any failure or error is a failure.
Run: uv run python tests/q23_3/check_masks.py
"""

import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from bor_support import check, connect, finish, load_fixtures  # noqa: E402

CAND = """SELECT DISTINCT upper(btrim(concat_ws(' ', nullif(btrim(c.businesshousenumber), ''), nullif(btrim(c.businessstreetname), ''), nullif(btrim(c.businessapartment), ''))))
FROM hpd_contacts c WHERE c.type = 'Agent' AND nullif(btrim(c.corporationname), '') IS NOT NULL AND upper(btrim(c.corporationname)) LIKE %(prefix)s"""


def main() -> int:
    driver, pg, release = connect()
    fx = load_fixtures(HERE / "fixtures.yaml")
    q = (HERE / "lookup.cypher").read_text()
    net = {r["address"]: int(r["degree"]) for r in release.rows("masked_addresses")}
    text = {r["identity_id"]: " ".join(p.strip() for p in (r["business_house"], r["business_street"], r["business_apartment"]) if p and p.strip())
            for r in release.rows("identity_names")}
    port: dict[str, int] = {}
    for e in release.rows("decision_events", rule="splink_address_evidence_mask"):
        port[text[e["subject_id"]]] = int(json.loads(e["detail"])["addr_degree"])
    with driver, pg, driver.session(database=os.environ["NEO4J_DATABASE"], default_access_mode="READ") as s, pg.cursor() as cur:
        for f in fx["agents"]:
            k = f["nameKey"]
            cur.execute(CAND, {"prefix": k.split(" ")[0] + "%"})
            cands = {" ".join(r[0].split()) for r in cur.fetchall() if r[0]}
            rows = s.run(q, nameKey=k).data()
            check(f"{k}: the graph returns addresses", len(rows) > 0)
            check(f"{k}: every graph address is a source candidate", all(r["address"] is None or r["address"] in cands for r in rows), str([r["address"] for r in rows if r["address"] and r["address"] not in cands][:3]))
            bad = [r["address"] for r in rows if r["address"] and (r["networkDegree"], r["portfolioDegree"]) != (net.get(r["address"]), port.get(r["address"]))]
            check(f"{k}: mask degrees equal the release for every address", not bad, str(bad[:3]))
            check(f"{k}: contacts count is not an address count (sums to the agent's contacts)",
                  sum(r["contacts"] for r in rows) == s.run("MATCH (c:Contact {nameKey: $k, contactType: 'Agent'}) RETURN count(c) AS n", k=k).single()["n"])
            a = f["maskedAddress"]
            hit = [r for r in rows if a and r["address"] == a]
            if a:
                check(f"{k}: {a} is masked with the fixture degrees", len(hit) == 1 and (hit[0]["networkDegree"], hit[0]["portfolioDegree"]) == (f["networkDegree"], f["portfolioDegree"]), str(hit))
            else:
                check(f"{k}: no address is masked by either method", all(r["networkDegree"] is None and r["portfolioDegree"] is None for r in rows))
    return finish()


if __name__ == "__main__":
    sys.exit(main())
