"""Name and address comparison for Q3.4 and Q3.5. Pure functions; nothing here touches a database.

Names are compared as recorded strings, never as a finding of "same party" (a name match is a lead).
  N1  uppercase, trim, collapse every run of whitespace to one space.
  N2  N1, then remove periods and turn commas into spaces (re-collapsed).
  N3  N2, then remove apostrophes. Used only to match an owner name to a NY DOS entity name (Q5, dos_name_agreement).
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
N3_RULE = "N3"
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


def n3(value: str | None) -> str | None:
    """N3 (Q5, owner name against NY DOS entity name): N2, then remove apostrophes. Spaces inside a name stay."""
    text = n2(value)
    if text is None:
        return None
    return n1(text.replace("'", ""))


def dos_name_agreement(a: str | None, b: str | None) -> dict:
    """Compare an owner name with a DOS entity name. Like name_agreement, plus rule N3 (apostrophes)."""
    out = name_agreement(a, b)
    if out["outcome"] == "different" and n3(a) == n3(b):
        return {"outcome": "normalization-match", "rule": N3_RULE}
    return out


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


# ---- Q22: same entity or not. Rules apply in this order; the first that makes the names equal is reported. Derived, a lead only.
#  N1/N2/N3 as above; S1  spaces removed (after N3): `KS` = `K S`, `COMPAN Y` = `COMPANY`;
#  L1  legal-suffix words to short form (INCORPORATED, CORPORATION, COMPANY, DEVELOPMENT) on the space-free text;
#  AB1 abbreviation table (HDFC = HOUSING DEVELOPMENT FUND COMPANY). Q3 and Q5 keep a space as a difference; only Q22 uses S1, L1, AB1.
# differs-by-numeral-or-word: after N3 one name is the other plus trailing words or a numeral (`X HOLDINGS` / `X HOLDINGS II`); never a match.
S1_RULE, L1_RULE, AB1_RULE = "S1", "L1", "AB1"
_L1 = (("INCORPORATED", "INC"), ("CORPORATION", "CORP"), ("COMPANY", "CO"), ("DEVELOPMENT", "DEV"))
_AB1 = (("HDFC", "HOUSINGDEVFUNDCO"),)


def _nospace(value: str | None) -> str | None:
    t = n3(value)
    return t.replace(" ", "") if t else None


def _l1(t: str) -> str:
    for long, short in _L1:
        t = t.replace(long, short)
    return t


def _ab1(t: str) -> str:
    for ab, full in _AB1:
        t = t.replace(ab, full)
    return t


def _core(text: str) -> list:
    """Words of an N3 name without trailing legal-form words (LLC, INC, CORP, CO, LP, LTD)."""
    words = text.split(" ")
    while len(words) > 1 and words[-1] in ("LLC", "INC", "CORP", "CO", "LP", "LTD", "INCORPORATED", "CORPORATION", "COMPANY"):
        words.pop()
    return words


def entity_name_comparison(a: str | None, b: str | None) -> dict:
    """Q22.1. Returns {outcome, rule}. Outcomes (scheme entity-name-outcomes): exact-normalized, normalization-match
    (rule N2, N3, S1 or L1), abbreviation-match (AB1), differs-by-numeral-or-word, different, not-comparable."""
    if n1(a) is None or n1(b) is None:
        return {"outcome": "not-comparable", "rule": None}
    out = dos_name_agreement(a, b)
    if out["outcome"] != "different":
        return out
    sa, sb = _nospace(a), _nospace(b)
    if sa == sb:
        return {"outcome": "normalization-match", "rule": S1_RULE}
    if _l1(sa) == _l1(sb):
        return {"outcome": "normalization-match", "rule": L1_RULE}
    if _ab1(_l1(sa)) == _ab1(_l1(sb)):
        return {"outcome": "abbreviation-match", "rule": AB1_RULE}
    ta, tb = _core(n3(a)), _core(n3(b))
    short, long_ = (ta, tb) if len(ta) <= len(tb) else (tb, ta)
    if len(short) < len(long_) and long_[: len(short)] == short:
        return {"outcome": "differs-by-numeral-or-word", "rule": None}
    return {"outcome": "different", "rule": None}
