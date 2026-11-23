"""Check Q24.4 (answer outcome, normalization statement, snapshot dates and caveats). Read-only. The contract dates must equal data/sources.yaml,
the outcome rule must give the three outcomes, and an absent entity name and an absent person name must both come out as no match in these sources.
Run: uv run python tests/q24_4/check_contract.py
"""

import os
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from q24_support import ROOT, assemble, check, connect, finish, load_fixtures, n3  # noqa: E402


def main() -> int:
    c = yaml.safe_load((HERE / "contract.yaml").read_text())
    src = yaml.safe_load((ROOT / "data" / "sources.yaml").read_text())
    src = src.get("sources", src)
    check("contract snapshot dates equal data/sources.yaml", {k: str(src[k]["data_through"]) for k in c["snapshot"]} == c["snapshot"], str({k: src[k]["data_through"] for k in c["snapshot"]}))
    check("the three outcomes", c["outcome"] == ["matches", "leads-only", "no-match-in-these-sources"])
    check("outcome rule: matches, leads only, none",
          (assemble([1], [], [])["outcome"], assemble([], [1], [])["outcome"], assemble([], [], [1])["outcome"], assemble([], [], [])["outcome"]) == ("matches", "leads-only", "leads-only", "no-match-in-these-sources"))
    check("caveats name leads, roles, 'does not exist', DOS scope and near-name limits", all(any(w in x for x in c["caveats"]) for w in ("lead", "Roles are as recorded", "does not exist", "DOS", "spacing")))
    l1, l2, l3 = (yaml.safe_load((HERE.parent / d / "fixtures.yaml").read_text()) for d in ("q24_1", "q24_2", "q24_3"))
    driver, pg = connect()
    with driver, pg, driver.session(database=os.environ["NEO4J_DATABASE"], default_access_mode="READ") as s:
        name = l1["absent"][0]["name"]
        ent = s.run((HERE.parent / "q24_1" / "lookup.cypher").read_text(), key=n3(name)).data()
        per = s.run((HERE.parent / "q24_2" / "lookup.cypher").read_text(), person=l2["absent"][0]["person"], reversed=l2["absent"][0]["reversed"]).data()
        words = n3(name).split(" ")
        near = s.run((HERE.parent / "q24_3" / "lookup.cypher").read_text(), key=n3(name), core=" ".join(words[:-1])).data()
        check("an absent entity and an absent person assemble to 'no match in these sources'", assemble(ent, per, near)["outcome"] == "no-match-in-these-sources", f"{len(ent)} {len(per)} {len(near)}")
    return finish()


if __name__ == "__main__":
    sys.exit(main())
