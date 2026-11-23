"""Shared helpers for tests/q26_*: what each source holds for a lot, derived from the frozen source database and the pinned BOR release.

Read-only on the source, the release and the graph. Independent of the loaders. The five absence reasons are BOR's top-level reasons
(vocabulary scheme `network-absence-reasons`); Q26 applies the same five to the non-layer sources (decision 2026-11-19).
"""

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from bor_support import check, connect, finish, load_fixtures, status_rows  # noqa: E402,F401
from q17_support import source_missing  # noqa: E402,F401
from q19_support import NET, PORT  # noqa: E402,F401
from watchline.compare import n3  # noqa: E402

OWNER_TYPES = ["CorporateOwner", "IndividualOwner", "JointOwner"]
VALID_BIN = "r.bin ~ '^[1-5][0-9]{6}$' AND r.bin !~ '000000$' AND r.registrationid > 0"
OWNERS_SQL = f"""SELECT DISTINCT c.type, nullif(btrim(c.corporationname), '') FROM hpd_registrations r JOIN hpd_contacts c ON c.registrationid = r.registrationid
WHERE r.bbl::text = %(bbl)s AND {VALID_BIN} AND c.type = ANY(%(types)s)"""
DOS_SQL = """SELECT dosid FROM dos_active_corporations
WHERE regexp_replace(upper(replace(replace(replace(btrim(currententityname),'.',''),',',' '),'''','')),'\\s+',' ','g') = %(key)s"""
VIOL_SQL = "SELECT count(*), count(*) FILTER (WHERE violationstatus = 'Open') FROM hpd_violations WHERE bbl::text = %(bbl)s"
VIOL_LOADED_SQL = """SELECT count(*) FROM hpd_violations v
WHERE v.bin IN (SELECT r.bin FROM hpd_registrations r WHERE r.bbl::text = %(bbl)s AND r.bin ~ '^[1-5][0-9]{6}$' AND r.bin !~ '000000$')
  AND v.bbl IN (SELECT DISTINCT bbl FROM hpd_registrations WHERE bbl IS NOT NULL)"""


def source_dos(cur, bbl: str) -> dict:
    """{'names': {name: [dosid,...]}, 'reason': ...}: DOS candidates per owner corporation name (rule N3), and the lot-level outcome.
    Lot level: present when any corporation name has a record; else no_qualifying_linkage when a corporation name was looked up;
    else outside_method_input (no owner contact, or only a person: no entity name to look up)."""
    cur.execute(OWNERS_SQL, {"bbl": bbl, "types": OWNER_TYPES})
    names = sorted({co for _t, co in cur.fetchall() if co})
    found = {}
    for nm in names:
        cur.execute(DOS_SQL, {"key": n3(nm)})
        found[nm] = [r[0] for r in cur.fetchall()]
    if any(found.values()):
        reason = None
    elif found:
        reason = "no_qualifying_linkage"
    else:
        reason = "outside_method_input"
    return {"names": found, "reason": reason}


def source_violations(cur, bbl: str) -> dict:
    cur.execute(VIOL_SQL, {"bbl": bbl})
    total, open_ = cur.fetchone()
    cur.execute(VIOL_LOADED_SQL, {"bbl": bbl})
    return {"total": int(total), "open": int(open_), "loadable": int(cur.fetchone()[0])}
