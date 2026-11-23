"""Check Q20.1 (the assembled recorded trail equals its component answers) for anchor A. Read-only on both databases.

1. Each fact in fixtures.yaml is re-derived from the frozen source with SQL, independent of the graph.
2. The component lookups (Q1.2, Q2.2, Q3.1, Q5.1, Q5.2, Q11.1, Q10.1) return the same facts from the graph.
3. The trail adds no fact: the owner name, DOS name and mortgage borrower agree under rule N3 only as a lead; the process name equals the
   entity itself and no agent is recorded.
Person names are never printed. Any failure or error is a failure. Run: uv run python tests/q20_1/check_trail.py
"""

import os
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from q12_support import check, connect, finish, n3  # noqa: E402


def q(name):
    return (HERE.parent / name / "lookup.cypher").read_text()


def main() -> int:
    a = yaml.safe_load((HERE / "fixtures.yaml").read_text())["anchor_a"]
    driver, pg = connect()
    with driver, pg, driver.session(database=os.environ["NEO4J_DATABASE"], default_access_mode="READ") as s, pg.cursor() as cur:
        # source
        cur.execute("SELECT DISTINCT type, nullif(btrim(corporationname), '') FROM hpd_contacts WHERE registrationid = %s "
                    "AND type IN ('CorporateOwner','IndividualOwner','JointOwner')", (a["registrationId"],))
        check("source: registered owner", cur.fetchall() == [(a["owner"]["contactType"], a["owner"]["name"])])
        cur.execute("SELECT dosid, dosprocessname, dosprocessaddress1, dosprocesscity, dosprocesszip FROM dos_active_corporations WHERE dosid = %s", (a["dos"]["dosId"],))
        d = a["dos"]
        check("source: DOS process name and address", [tuple(x.strip() if isinstance(x, str) else x for x in r) for r in cur.fetchall()]
              == [(d["dosId"], d["processName"], d["processAddress"], d["processCity"], d["processZip"])])
        # graph, component lookups
        r = s.run(q("q1_2"), bbl=a["bbl"]).single()
        check("Q1.2: the addressed building is on the lot", a["bin"] in {b["bin"] for b in r["buildings"]})
        r = s.run(q("q2_2"), bin=a["bin"]).data()
        owners = {(o["contactType"], o["corporationName"]) for row in r if row["registrationId"] == a["registrationId"] for o in row["owners"]}
        check("Q2.2: registered owner", owners == {(a["owner"]["contactType"], a["owner"]["name"])})
        deeds = {x["documentId"]: x for x in s.run(q("q3_1"), bbl=a["bbl"]).single()["deeds"]}
        check("Q3.1: both deeds present with recorded date and amount",
              all(k in deeds and deeds[k]["recordedDate"] == v["recorded"] and deeds[k]["amount"] == v["amount"] for k, v in a["deeds"].items()))
        key = n3(a["owner"]["name"])
        cands = s.run(q("q5_1"), key=key).data()
        check("Q5.1: one DOS candidate for the owner name", [c["dosId"] for c in cands] == [a["dos"]["dosId"]])
        p = s.run(q("q5_2"), dosId=a["dos"]["dosId"]).single()
        check("Q5.2: the entity is its own process name, at the recorded address",
              p["processName"] == a["owner"]["name"] and p["processAddress"] == a["dos"]["processAddress"] and p["processZip"] == a["dos"]["processZip"])
        m = {x["documentId"]: x for x in s.run(q("q11_1"), nameKey=key).data()}.get(a["mortgage"]["documentId"])
        check("Q11.1: the joint mortgage is recorded", m is not None and m["amount"] == a["mortgage"]["amount"])
        if m:
            names = {(p_["partyType"], p_["name"]) for p_ in m["parties"]}
            exp = {(1, n) for n in a["mortgage"]["borrowers"]} | {(2, n) for n in a["mortgage"]["lenders"]}
            check("Q11.1: borrowers and lender as recorded", names == exp)
        lay = s.run(q("q10_1"), bbl=a["bbl"]).single()
        check("Q10.1: anchor A is in no network and no portfolio", lay["networkId"] is None and lay["portfolioId"] is None)
    return finish()


if __name__ == "__main__":
    sys.exit(main())
