"""Check Q24.2 (records that carry a person's name, as leads with counts) against the frozen source. Read-only on both databases.

Person names come from rules in fixtures.yaml, are held in memory and never printed. HPD contacts and deed parties (both name orders) are re-derived
from the source; the graph lookup must give the same counts per role and order. Any failure or error is a failure.
Run: uv run python tests/q24_2/check_person.py
"""

import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from q24_support import PERSON, check, connect, deed_parties, finish, hpd_person, load_fixtures, lots_of_bins, n3  # noqa: E402


def swap(name: str) -> str | None:
    w = name.split(" ")
    return f"{w[-1]} {' '.join(w[:-1])}" if len(w) > 1 else None


def pick(cur, s, rule: str) -> str:
    base = f"""SELECT upper({PERSON}) p, count(DISTINCT c.registrationid) n, min(c.registrationid) first_reg FROM hpd_contacts c
               WHERE c.type = 'IndividualOwner' AND {PERSON} IS NOT NULL AND array_length(string_to_array({PERSON}, ' '), 1) = 2 GROUP BY 1"""
    if rule == "most_frequent_two_word_individual_owner":
        cur.execute(base + " ORDER BY n DESC, p LIMIT 1")
        return cur.fetchone()[0]
    if rule == "first_individual_owner_with_one_registration":
        cur.execute(base + " HAVING count(DISTINCT c.registrationid) = 1 ORDER BY first_reg, p LIMIT 1")
        return cur.fetchone()[0]
    # first by registration id whose reversed order is a deed party in the graph's scope (the graph only picks the candidate; the answer comes from the source)
    cur.execute(base + " ORDER BY first_reg, p LIMIT 3000")
    cands = [r[0] for r in cur.fetchall()]
    for i in range(0, len(cands), 200):
        chunk = cands[i:i + 200]
        got = {r["k"] for r in s.run("UNWIND $ks AS k MATCH (g:Grantee {nameKey: k}) RETURN DISTINCT k", ks=[n3(swap(c)) for c in chunk]).data()}
        for c in chunk:
            if n3(swap(c)) in got:
                return c
    raise RuntimeError("no candidate")


def source_counts(cur, person: str) -> dict:
    out = {}
    hp = hpd_person(cur, person)
    for role in {r[1] for r in hp}:
        sub = [r for r in hp if r[1] == role]
        out[("hpd_contacts", role, "as given")] = (len({r[0] for r in sub}), len({r[2] for r in sub}), len(lots_of_bins(cur, {r[2] for r in sub})))
    for order, nm in (("as given", person), ("reversed", swap(person))):
        if nm is None:
            continue
        for (role, doc), lots in deed_parties(cur, [n3(nm)]).items():
            out.setdefault(("acris_parties", role, order), [set(), set()])
            out[("acris_parties", role, order)][0].add(doc)
            out[("acris_parties", role, order)][1].update(lots)
    return {k: (v if isinstance(v, tuple) else (len(v[0]), None, len(v[1]))) for k, v in out.items()}


def graph_counts(s, q, person: str) -> dict:
    rows = s.run(q, person=person, reversed=swap(person)).data()
    return {(r["source"], r["role"], r["order"]): (r["records"], r["buildings"], r["lots"]) for r in rows}


def main() -> int:
    fx = load_fixtures(HERE)
    q = (HERE / "lookup.cypher").read_text()
    driver, pg = connect()
    with driver, driver.session(database=os.environ["NEO4J_DATABASE"], default_access_mode="READ") as s, pg, pg.cursor() as cur:
        for f in fx["persons"]:
            person = pick(cur, s, f["rule"])
            src, gr = source_counts(cur, person), graph_counts(s, q, person)
            check(f"{f['rule']}: roles, orders and counts equal the source", src == gr, f"graph {len(gr)} groups, source {len(src)}")
            check(f"{f['rule']}: HPD contact roles are recorded roles (never owner conclusions)", all(k[1] for k in gr))
            if f["rule"] == "first_individual_owner_found_reversed_in_deeds":
                check(f"{f['rule']}: a reversed-order deed row is returned", any(k[2] == "reversed" for k in gr), str(list(gr)))
            if f["rule"] == "most_frequent_two_word_individual_owner":
                check(f"{f['rule']}: many records, so the count matters (more than 10 registrations)", any(k[0] == "hpd_contacts" and v[0] > 10 for k, v in gr.items()))
        for f in fx["absent"]:
            check("an absent person returns no row", s.run(q, person=f["person"], reversed=f["reversed"]).data() == [])
    return finish()


if __name__ == "__main__":
    sys.exit(main())
