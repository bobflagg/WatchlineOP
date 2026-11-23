"""Check Q20.3 (lead rule and one stop reason) for the anchor A trail. Read-only on the graph.

The lead rule is applied here as a reference classifier: a name or address from a recorded source is a lead unless it is a service address
(DOS process address), a masked address (Q6.2) or a financing party; each is logged either way. The stop reason is one of five.
1. The classifier reproduces every expected value in fixtures.yaml.
2. Q6.2 finds no mask and Q6.4 finds no list row for the lead address (a miss is reported as not clearance, never as safe).
3. Exactly one stop reason is chosen and it is one of the five enumerated ones.
Any failure or error is a failure. Run: uv run python tests/q20_3/check_leads.py
"""

import os
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from q12_support import check, connect, finish  # noqa: E402

REASONS = {"reached_service_address", "no_further_link", "needs_payment", "budget_reached", "unresolved_conflict"}


def main() -> int:
    fx = yaml.safe_load((HERE / "fixtures.yaml").read_text())["trail"]
    masked_q = (HERE.parent / "q6_2" / "lookup.cypher").read_text()
    listed_q = (HERE.parent / "q6_4" / "lookup.cypher").read_text()
    driver, pg = connect()
    pg.close()
    with driver, driver.session(database=os.environ["NEO4J_DATABASE"], default_access_mode="READ") as s:
        leads_left = 0
        for a in fx["addresses"]:
            masked = bool(s.run(masked_q, address=a["street"]).data())
            listed = bool(s.run(listed_q, address=a["street"], zip5=a["zip5"]).data())
            got = "logged" if (a["role"] == "service" or masked) else "lead"
            check(f"{a['street']}: classified {a['expect']}", got == a["expect"])
            if a["role"] == "business":
                check(f"{a['street']}: masked {a['masked']}, listed {a['listed']}", (masked, listed) == (a["masked"], a["listed"]))
            leads_left += got == "lead"
        for e in fx["entities"]:
            got = "logged" if "financing" in e.get("why", "") else "lead"
            check(f"{e['name']}: classified {e['expect']}", got == e["expect"])
        reason = fx and yaml.safe_load((HERE / "fixtures.yaml").read_text())["stop_reason"]
        check("exactly one stop reason, from the five", reason in REASONS)
        check("the stop reason names the service address reached, with business leads still open (budget not used up)", reason == "reached_service_address" and leads_left >= 1)
    return finish()


if __name__ == "__main__":
    sys.exit(main())
