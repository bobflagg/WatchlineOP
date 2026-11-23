"""Shared helpers for tests/q24_*: records that carry a name, derived from the frozen source independent of the graph.

Read-only on both databases. Person names are never printed or stored: person fixtures are rules, and checks report counts only.
Counting units: distinct registrations, buildings (BIN), lots (BBL), deeds (document ids), DOS ids.
"""

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from q5_support import ROOT, check, connect, finish, load_fixtures, n3  # noqa: E402,F401
from q12_support import DEED_TYPES  # noqa: E402,F401

VALID = "r.bbl IS NOT NULL AND r.bin ~ '^[1-5][0-9]{6}$' AND r.bin !~ '000000$' AND r.registrationid > 0"
PERSON = "nullif(btrim(concat_ws(' ', nullif(btrim(c.firstname), ''), nullif(btrim(c.middleinitial), ''), nullif(btrim(c.lastname), ''))), '')"
# The graph's lot scope (Q1): HPD-registered lots plus unregistered lots with 3 or more residential units.
LOT_SCOPE = f"""(SELECT DISTINCT r.bbl::text AS bbl FROM hpd_registrations r WHERE {VALID}
                 UNION SELECT bbl::text FROM pluto_latest WHERE unitsres >= 3)"""


def prefix_of(key: str) -> str:
    """A narrowing LIKE prefix over the letters and digits of a key; rule N3 is applied in code afterwards."""
    return "".join(ch for ch in key if ch.isalnum())[:5] + "%"


def hpd_corporation(cur, key: str) -> list[tuple]:
    """(registrationid, contact type, corporation name as recorded, bin, bbl) of contacts whose corporation name has N3 key `key`, on registrations the graph holds."""
    cur.execute(f"""SELECT DISTINCT c.registrationid, c.type, nullif(btrim(c.corporationname), ''), r.bin, r.bbl::text
                    FROM hpd_contacts c JOIN hpd_registrations r ON r.registrationid = c.registrationid
                    WHERE regexp_replace(upper(c.corporationname), '[^A-Z0-9]', '', 'g') LIKE %(p)s AND {VALID}""", {"p": prefix_of(key)})
    return [r for r in cur.fetchall() if r[2] and n3(r[2]) == key]


def hpd_person(cur, person: str) -> list[tuple]:
    """(registrationid, contact type, bin, bbl) of contacts whose person name equals `person` (upper case, single spaces)."""
    cur.execute(f"""SELECT DISTINCT c.registrationid, c.type, r.bin, r.bbl::text FROM hpd_contacts c
                    JOIN hpd_registrations r ON r.registrationid = c.registrationid
                    WHERE upper({PERSON}) = %(p)s AND {VALID}""", {"p": person})
    return cur.fetchall()


def lots_of_bins(cur, bins) -> set:
    """Lots of buildings: every lot on which HPD records one of these BINs (a building on two lots counts toward both), as the graph's Lot-HAS_BUILDING->Building."""
    cur.execute("SELECT DISTINCT bbl::text FROM hpd_registrations WHERE bin = ANY(%s) AND bbl IS NOT NULL AND registrationid > 0", (sorted(bins),))
    return {r[0] for r in cur.fetchall()}


DEED_SQL = f"""
WITH cur AS (SELECT DISTINCT ON (m.documentid) m.documentid, m.doctype FROM real_property_master m
             WHERE m.documentid = ANY(%(docs)s) ORDER BY m.documentid, m.modifieddate DESC NULLS LAST, m.goodthroughdate DESC NULLS LAST)
SELECT DISTINCT c.documentid, l.bbl::text FROM cur c JOIN real_property_legals l ON l.documentid = c.documentid
WHERE c.doctype = ANY(%(types)s) AND l.bbl::text IN {LOT_SCOPE}
"""


def deed_parties(cur, keys: list[str]) -> dict:
    """{(role, documentid): [bbl]} for deeds on in-scope lots where a party (grantor 1, grantee 2) has an N3 key in `keys`."""
    out: dict = {}
    for k in keys:
        cur.execute("""SELECT DISTINCT documentid, partytype, name FROM real_property_parties
                       WHERE partytype IN (1, 2) AND regexp_replace(upper(name), '[^A-Z0-9]', '', 'g') LIKE %(p)s""", {"p": prefix_of(k)})
        rows = [r for r in cur.fetchall() if r[2] and n3(r[2]) in keys]
        docs = sorted({r[0] for r in rows})
        if not docs:
            continue
        cur.execute(DEED_SQL, {"docs": docs, "types": DEED_TYPES})
        lots: dict = {}
        for d, b in cur.fetchall():
            lots.setdefault(d, set()).add(b)
        for d, pt, _ in rows:
            if d in lots:
                out.setdefault(("grantor" if pt == 1 else "grantee", d), set()).update(lots[d])
    return {k: sorted(v) for k, v in out.items()}


def assemble(matches: list, person_leads: list, near_leads: list) -> dict:
    """The Q24 answer outcome: entity matches win; otherwise any lead gives leads-only; otherwise no match in these sources."""
    if matches:
        outcome = "matches"
    elif person_leads or near_leads:
        outcome = "leads-only"
    else:
        outcome = "no-match-in-these-sources"
    return {"outcome": outcome, "matches": matches, "leads": {"person": person_leads, "near": near_leads}}
