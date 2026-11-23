"""Check Q24.3 (near-match name leads) against the frozen source. Read-only on both databases.

HPD candidates are re-derived from the source and must equal the graph's; deed-party candidates must all exist in the source's party names.
Every candidate is classified with compare.entity_name_comparison; "different" is dropped, and no lead is ever an exact-normalized match.
Run: uv run python tests/q24_3/check_near.py
"""

import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from q24_support import VALID, check, connect, finish, load_fixtures, n3, prefix_of  # noqa: E402
from watchline.compare import _core, entity_name_comparison  # noqa: E402


def core_of(name: str) -> str:
    return " ".join(_core(n3(name)))


def lead_kind(key: str, cand: str) -> dict:
    """compare.entity_name_comparison, plus one Q24 lead kind: the same name with a legal-form word added or removed (compare calls that `different`)."""
    o = entity_name_comparison(key, cand)
    if o["outcome"] == "different" and _core(key) == _core(cand):
        return {"outcome": "legal-suffix-only", "rule": "core"}
    return o


def main() -> int:
    fx = load_fixtures(HERE)
    q = (HERE / "lookup.cypher").read_text()
    driver, pg = connect()
    with driver, driver.session(database=os.environ["NEO4J_DATABASE"], default_access_mode="READ") as s, pg, pg.cursor() as cur:
        for f in fx["names"] + fx["not_found"]:
            key, core = n3(f["name"]), core_of(f["name"])
            check(f"{f['name']}: the core is {core}", core == f["core"], core)
            rows = s.run(q, key=key, core=core).data()
            cur.execute(f"""SELECT DISTINCT c.registrationid, nullif(btrim(c.corporationname), '') FROM hpd_contacts c JOIN hpd_registrations r ON r.registrationid = c.registrationid
                            WHERE regexp_replace(upper(c.corporationname), '[^A-Z0-9]', '', 'g') LIKE %(p)s AND {VALID}""", {"p": prefix_of(core)})
            src: dict = {}
            for rid, nm in cur.fetchall():
                k = n3(nm) if nm else None
                if k and k != key and (k == core or k.startswith(core + " ")):
                    src.setdefault(k, set()).add(rid)
            g = {r["nameKey"]: r["records"] for r in rows if r["source"] == "hpd_contacts"}
            check(f"{f['name']}: HPD candidate keys and registration counts equal the source", g == {k: len(v) for k, v in src.items()}, f"graph {len(g)}, source {len(src)}")
            cur.execute("""SELECT DISTINCT name FROM real_property_parties WHERE partytype = 2 AND regexp_replace(upper(name), '[^A-Z0-9]', '', 'g') LIKE %(p)s""", {"p": prefix_of(core)})
            src_deed = {n3(r[0]) for r in cur.fetchall() if r[0]}
            gd = {r["nameKey"] for r in rows if r["source"] == "acris_parties"}
            check(f"{f['name']}: every deed-party candidate is a grantee name in the source", gd <= src_deed, str(sorted(gd - src_deed)[:3]))
            leads = {}
            for r in rows:
                o = lead_kind(key, r["nameKey"])
                if o["outcome"] != "different":
                    leads[r["nameKey"]] = o
            check(f"{f['name']}: no lead is an exact-normalized match (that is a match, Q24.1)", all(o["outcome"] != "exact-normalized" for o in leads.values()))
            for e in f.get("expect", []):
                o = leads.get(e["nameKey"])
                check(f"{f['name']}: lead {e['nameKey']} is {e['outcome']} ({e['rule']})", o == {"outcome": e["outcome"], "rule": e["rule"]}, str(o))
            if "missing" in f:
                check(f"{f['name']}: the misspelling's neighbour {f['missing']} is not found by prefix (documented limit)", f["missing"] not in {r["nameKey"] for r in rows})
    return finish()


if __name__ == "__main__":
    sys.exit(main())
