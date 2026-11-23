"""Check Q20.2 (layers apart; no ownership claim rests on a layer). Read-only on the graph.

1. Q10.1 returns the Operational Network and the Owner Portfolio as separate values (ON- and OP- ids); a lot in one layer has the other null.
2. The graph holds no stored dossier, finding, ownership claim or beneficial owner on any lot, network or portfolio (computed at answer time).
Any failure or error is a failure. Run: uv run python tests/q20_2/check_layers.py
"""

import os
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from q12_support import check, connect, finish  # noqa: E402

STORED = """
CALL () { MATCH (n) WHERE any(l IN labels(n) WHERE l IN ['Dossier', 'Finding', 'Claim', 'Lead', 'BeneficialOwner', 'StopReason']) RETURN count(n) AS labels }
CALL () { MATCH (n:Lot) WHERE n.owner IS NOT NULL OR n.ownedBy IS NOT NULL OR n.beneficialOwner IS NOT NULL OR n.stopReason IS NOT NULL RETURN count(n) AS lots }
CALL () { MATCH (n) WHERE (n:OperationalNetwork OR n:OwnerPortfolio) AND (n.owner IS NOT NULL OR n.ownedBy IS NOT NULL OR n.beneficialOwner IS NOT NULL) RETURN count(n) AS groups }
RETURN labels, lots, groups
"""


def main() -> int:
    fx = yaml.safe_load((HERE / "fixtures.yaml").read_text())
    lookup = (HERE.parent / "q10_1" / "lookup.cypher").read_text()
    driver, pg = connect()
    pg.close()
    with driver, driver.session(database=os.environ["NEO4J_DATABASE"], default_access_mode="READ") as s:
        for f in fx["lots"]:
            r = s.run(lookup, bbl=f["bbl"]).single()
            check(f"{f['bbl']}: network id present is {f['network']}", (r["networkId"] is not None) == f["network"])
            check(f"{f['bbl']}: portfolio id present is {f['portfolio']}", (r["portfolioId"] is not None) == f["portfolio"])
            check(f"{f['bbl']}: ids belong to their own layer", (r["networkId"] or "ON-").startswith("ON-") and (r["portfolioId"] or "OP-").startswith("OP-"))
        r = s.run(STORED).single()
        check("nothing stored: no dossier, finding, claim, lead, stop reason or owner on a lot or group", r["labels"] == 0 and r["lots"] == 0 and r["groups"] == 0, str(dict(r)))
    return finish()


if __name__ == "__main__":
    sys.exit(main())
