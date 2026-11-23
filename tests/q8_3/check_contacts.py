"""Check (Landlord)-[:BASED_ON_CONTACT]->(Contact) against the pinned release (Q8.3). Read-only on the graph and the release.

1. The release itself: the selected observations name the contact keys in the fixture totals; the fixture landlords match.
2. The graph, over all 31035 landlords: a landlord is linked to exactly the Contacts that carry the registration, type, corporation
   name and person name of one of its selected observations (all contacts that differ only in title). A key the graph does not hold
   is not linked. Every linked contact is on a registration the landlord covers. The lookup returns the fixture contacts.
Person names are compared in memory and never printed or stored. Any failure or error is a failure; nothing is skipped.
Run: uv run python tests/q8_3/check_contacts.py
"""

import os
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from bor_support import check, connect, finish, load_fixtures  # noqa: E402


def person(c: dict) -> str:
    return " ".join(p.strip() for p in (c["first_name"], c["middle_initial"], c["last_name"]) if p and p.strip())


def main() -> int:
    driver, pg, release = connect()
    fx = load_fixtures(HERE / "fixtures_contacts.yaml")
    members = {int(r["node_id"]) for r in release.rows("group_members")}
    contacts = {r["observation_id"]: r for r in release.rows("observation_contacts")}
    keys = set()
    for r in release.rows("node_observations"):
        n = int(r["node_id"])
        c = contacts.get(r["selected_observation_id"])
        if n in members and c:
            keys.add((n, int(r["registration_id"]), c["contact_type"], (c["corporation_name"] or "").strip(), person(c)))
    t = fx["totals"]
    check("release: selected contact keys, landlords with one, and keys by type match the fixture",
          (len(keys), len({k[0] for k in keys}), dict(Counter(k[2] for k in keys))) ==
          (t["selected_contact_keys"], t["landlords_with_a_selected_contact"], t["by_type"]), f"{len(keys)}")
    for f in fx["landlords"]:
        got = sorted({(k[1], k[2]) for k in keys if k[0] == f["nodeId"]})
        check(f"fixture node {f['nodeId']} matches the release", got == sorted(tuple(c) for c in f["contacts"]), f"release gives {got}")

    with driver, driver.session(database=os.environ["NEO4J_DATABASE"], default_access_mode="READ") as s:
        held = Counter()
        for r in s.run("MATCH (g:Registration)-[:HAS_CONTACT]->(c:Contact) "
                       "RETURN g.registrationId AS rid, c.contactType AS t, coalesce(c.corporationName, '') AS corp, coalesce(c.personName, '') AS pe"):
            held[(r["rid"], r["t"], r["corp"], r["pe"])] += 1
        expected = {(k[0], k[1:]) for k in keys if k[1:] in held}
        want_links = sum(held[k[1:]] for k in keys if k[1:] in held)
        got = defaultdict(int)
        for r in s.run("MATCH (a:Landlord)-[:BASED_ON_CONTACT]->(c:Contact)<-[:HAS_CONTACT]-(g:Registration) "
                       "RETURN a.nodeId AS n, g.registrationId AS rid, c.contactType AS t, coalesce(c.corporationName, '') AS corp, "
                       "coalesce(c.personName, '') AS pe"):
            got[(r["n"], (r["rid"], r["t"], r["corp"], r["pe"]))] += 1
        check("graph: every landlord is linked to the contacts of its selected observations and to no other",
              set(got) == expected and sum(got.values()) == want_links, f"graph {sum(got.values())} links vs expected {want_links}")
        check("graph: contacts that differ only in title are all linked (one link per contact)",
              all(n == held[k] for (_, k), n in got.items()))
        n_none = sum(1 for k in keys if k[1:] not in held)
        check("graph: selected contacts not held, held, links and landlords linked match the fixture",
              (n_none, len(keys) - n_none, sum(got.values()), len({n for n, _ in got})) ==
              (t["keys_not_held"], t["keys_linked"], t["links"], t["landlords_linked"]),
              f"not held {n_none}, held {len(keys) - n_none}, links {sum(got.values())}, landlords {len({n for n, _ in got})}")
        bad = s.run("MATCH (a:Landlord)-[:BASED_ON_CONTACT]->(c:Contact)<-[:HAS_CONTACT]-(g:Registration) "
                    "WHERE NOT (a)-[:COVERS {registrationId: g.registrationId}]->(:Lot) RETURN count(*) AS n").single()["n"]
        check("graph: every linked contact is on a registration the landlord covers", bad == 0, f"{bad} links")
        lookup = (HERE / "lookup_landlords.cypher").read_text()
        for gid in sorted({f["groupId"] for f in fx["landlords"]}):
            rows = {r["nodeId"]: r["selectedContacts"] for r in s.run(lookup, groupId=gid)}
            for f in fx["landlords"]:
                if f["groupId"] == gid:
                    got_c = sorted((c["registrationId"], c["contactType"]) for c in rows.get(f["nodeId"], []))
                    check(f"lookup: node {f['nodeId']} in {gid} returns the fixture contacts", got_c == sorted(tuple(c) for c in f["contacts"]), f"graph gives {got_c}")
    pg.close()
    return finish()


if __name__ == "__main__":
    sys.exit(main())
