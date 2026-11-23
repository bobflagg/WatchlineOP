"""Check Q18.3 (the grouping is not its own evidence, and the uncertainty is stated).

1. tests/q18_1 and q18_2 lookups never read group membership: no IN_PORTFOLIO, IN_NETWORK, OwnerPortfolio or OperationalNetwork in the query text.
2. The signals for a lot do not change when it is asked about alone or inside its portfolio set (a deed's signals depend on its own lots only
   when the same lots are passed; the result for a deed on lot X is identical for [X] and for a larger set that contains X and no other lot it covers).
3. contract.yaml lists the caveats the answer carries; each is a non-empty string and the "uncertain" list is non-empty.
Any failure or error is a failure. Run: uv run python tests/q18_3/check_independence.py
"""

import os
import re
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from q18_support import check, connect, finish  # noqa: E402


def main() -> int:
    fx = yaml.safe_load((HERE / "fixtures.yaml").read_text())
    for q in ("q18_1", "q18_2"):
        text = re.sub(r"//.*", "", (HERE.parent / q / "lookup.cypher").read_text())
        check(f"{q}: lookup reads no group membership", not re.search(r"IN_PORTFOLIO|IN_NETWORK|OwnerPortfolio|OperationalNetwork", text))
    contract = yaml.safe_load((HERE / "contract.yaml").read_text())
    check("contract: caveats and uncertainty are stated", all(contract.get(k) for k in ("caveats", "uncertain", "fields")) and all(isinstance(c, str) and c for c in contract["caveats"]))
    lookup = (HERE.parent / "q18_2" / "lookup.cypher").read_text()
    driver, pg = connect()
    with driver, pg, driver.session(database=os.environ["NEO4J_DATABASE"], default_access_mode="READ") as s:
        for f in fx["pairs"]:
            alone = {r["documentId"]: r for r in s.run(lookup, bbls=[f["bbl"]], start=None, end=None).data()}
            wide = {r["documentId"]: r for r in s.run(lookup, bbls=f["set"], start=None, end=None).data()}
            same = all(alone[d][k] == wide[d][k] for d in alone if d in wide and wide[d]["lots"] == alone[d]["lots"]
                       for k in ("granteeNamedForLot", "sameName", "granteeRegisteredOwner", "signals"))
            check(f"{f['bbl']}: signals are the same alone and inside the larger set", same and all(d in wide for d in alone))
    return finish()


if __name__ == "__main__":
    sys.exit(main())
