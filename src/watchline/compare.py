"""Name and address comparison for Q3.4 and Q3.5. Pure functions; nothing here touches a database.

Names are compared as recorded strings, never as a finding of "same party" (a name match is a lead).
  N1  uppercase, trim, collapse every run of whitespace to one space.
  N2  N1, then remove periods and turn commas into spaces (re-collapsed).
Spaces inside a name are never removed, so "K S TURNPIKE LLC" and "KS TURNPIKE LLC" are different.

Outcomes (scheme name-agreement-outcomes):
  exact-normalized     equal after N1
  normalization-match  not equal after N1, equal after N2 (the answer states rule N2)
  different            both names present, not equal after N2
  not-comparable       either name is absent

Addresses (rule A1, scheme address-agreement-outcomes):
  same     street line equal after N1 and ZIP equal on the first five digits
  differs  both street lines and both ZIPs present, and at least one differs
  absent   either street line or either ZIP is absent
The second address line (a unit or a suite) is returned apart and never compared. A shared address at a mail drop
is not evidence of anything; flagging mail drops needs a curated list that does not exist yet.
"""

import re

N1_RULE = "N1"
N2_RULE = "N2"
A1_RULE = "A1"


def n1(value: str | None) -> str | None:
    if value is None:
        return None
    text = re.sub(r"\s+", " ", value.strip().upper())
    return text or None


def n2(value: str | None) -> str | None:
    text = n1(value)
    if text is None:
        return None
    return n1(text.replace(".", "").replace(","," "))  # a comma may separate words; a period never does


def name_agreement(a: str | None, b: str | None) -> dict:
    """Compare two recorded names. Returns {outcome, rule}; rule is set only for a normalization match."""
    x, y = n1(a), n1(b)
    if x is None or y is None:
        return {"outcome": "not-comparable", "rule": None}
    if x == y:
        return {"outcome": "exact-normalized", "rule": N1_RULE}
    if n2(a) == n2(b):
        return {"outcome": "normalization-match", "rule": N2_RULE}
    return {"outcome": "different", "rule": None}


def zip5(value: str | None) -> str | None:
    if value is None:
        return None
    m = re.match(r"\s*(\d{5})", value)
    return m.group(1) if m else None


def address_agreement(line_a, zip_a, line_b, zip_b, unit_a=None, unit_b=None) -> dict:
    """Compare two addresses by street line and ZIP. The unit of each is returned apart."""
    la, lb, za, zb = n1(line_a), n1(line_b), zip5(zip_a), zip5(zip_b)
    if None in (la, lb, za, zb):
        outcome = "absent"
    elif la == lb and za == zb:
        outcome = "same"
    else:
        outcome = "differs"
    return {"outcome": outcome, "rule": A1_RULE, "units": [n1(unit_a), n1(unit_b)]}
