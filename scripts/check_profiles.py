"""Stage 2 check: validate profiles/*.yaml against the vocabulary, data/sources.yaml and the specs.

Exits nonzero on any failure. A check that cannot run counts as a failure.
"""
import re
import sys
from pathlib import Path

import yaml
from rdflib import Graph, Namespace, RDF
from rdflib.namespace import SKOS

ROOT = Path(__file__).resolve().parent.parent
VOCAB = Namespace("https://watchline.example/vocab/")
SOURCE_PROFILES = {"pluto", "hpd_registrations", "geosupport"}  # profiles/<source_key>.yaml
COLUMN_KEYS = {"semantic_type", "physical_type", "allowed", "concept", "used_by"}
FIELD_KEYS = {"requirement", "source", "type", "allowed", "concept"}

errors: list[str] = []
ran: dict[str, int] = {}


def fail(msg: str) -> None:
    errors.append(msg)


def ran_check(name: str) -> None:
    ran[name] = ran.get(name, 0) + 1


def load(path: Path):
    try:
        return yaml.safe_load(path.read_text())
    except Exception as exc:  # malformed YAML or unreadable file
        fail(f"{path.relative_to(ROOT)}: cannot parse: {exc}")
        return None


def is_pending(entry: dict) -> bool:
    return entry.get("status") == "pending"


vocab = Graph()
vocab.parse(ROOT / "vocabulary/watchline.ttl", format="turtle")
concepts = {str(s)[len(str(VOCAB)):] for s in vocab.subjects(RDF.type, SKOS.Concept)}
outcome_labels = {
    str(vocab.value(s, SKOS.prefLabel))
    for s in vocab.subjects(SKOS.inScheme, VOCAB["address-resolution-outcomes"])
}


def check_concept(where: str, slug) -> None:
    ran_check("concept IRI in watchline.ttl")
    if slug is None:
        return
    if slug not in concepts:
        fail(f"{where}: concept '{slug}' is not in vocabulary/watchline.ttl")


sources = load(ROOT / "data/sources.yaml")
columns_used = {}
if sources:
    for key, src in sources["sources"].items():
        columns_used[key] = {c.strip() for c in str(src.get("columns_used", "")).split(",") if c.strip()}

# --- evidence profile and enums against the specs ---
evidence = load(ROOT / "profiles/evidence.yaml")
required_evidence = {
    "source_key", "snapshot_id", "snapshot_date", "run_id", "source_category",
    "assertion_type", "review_status", "source_record_locator", "mapping_git_revision",
}
if evidence:
    ran_check("evidence profile fields")
    missing = required_evidence - set(evidence.get("fields", {}))
    if missing:
        fail(f"profiles/evidence.yaml: missing fields {sorted(missing)}")
    for name, f in evidence.get("fields", {}).items():
        for k in ("type", "allowed", "maps_to"):
            if k not in f:
                fail(f"profiles/evidence.yaml:{name}: missing '{k}'")
        check_concept(f"profiles/evidence.yaml:{name}", f.get("concept"))

    claude_md = (ROOT / "CLAUDE.md").read_text()
    m = re.search(r"source category separately: (.+)", claude_md)
    spec_cat = set(re.findall(r"`(\w+)`", m.group(1))) if m else set()
    ran_check("enum equals spec")
    if set(evidence["fields"]["source_category"]["allowed"]["values"]) != spec_cat:
        fail(f"source_category enum differs from CLAUDE.md: {spec_cat}")
    proc = (ROOT / "specs/stage2-procedure.md").read_text()
    m = re.search(r"`review_status` \(([^)]+)\)", proc)
    spec_rs = set(re.findall(r"`(\w+)`", m.group(1))) if m else set()
    ran_check("enum equals spec")
    if set(evidence["fields"]["review_status"]["allowed"]["values"]) != spec_rs:
        fail(f"review_status enum differs from specs: {spec_rs}")

# --- source profiles ---
profile_fields: dict[str, dict] = {}
for key in sorted(SOURCE_PROFILES):
    path = ROOT / f"profiles/{key}.yaml"
    prof = load(path) if path.exists() else None
    if prof is None:
        fail(f"profiles/{key}.yaml missing or unreadable")
        continue
    ran_check("source profile structure")
    if prof.get("source_key") != key:
        fail(f"{path.name}: source_key must be '{key}'")
    if key not in columns_used:
        fail(f"{path.name}: source key '{key}' not in data/sources.yaml")
    for col, c in prof.get("columns", {}).items():
        where = f"{path.name}:{col}"
        missing = COLUMN_KEYS - set(c)
        if missing:
            fail(f"{where}: missing keys {sorted(missing)}")
        if is_pending(c) and not c.get("pending_reason"):
            fail(f"{where}: pending without pending_reason")
        if not is_pending(c) and ("null_policy" not in c):
            fail(f"{where}: missing null_policy")
        check_concept(where, c.get("concept"))
        profile_fields[f"{key}.{col}"] = c

# --- answer profile ---
answer = load(ROOT / "profiles/q01-answer.yaml")
if answer:
    for name, f in answer.get("fields", {}).items():
        where = f"q01-answer.yaml:{name}"
        ran_check("answer field has source, type, allowed")
        pending = is_pending(f)
        if pending and not f.get("pending_reason"):
            fail(f"{where}: pending without pending_reason")
        missing = FIELD_KEYS - set(f)
        if missing:
            fail(f"{where}: missing keys {sorted(missing)}")
        if not pending and f.get("allowed") in (None, {}, {"pending": True}):
            fail(f"{where}: not pending but allowed values are empty")
        src = f.get("source")
        if src == "derived":
            if not f.get("derivation"):
                fail(f"{where}: derived field without derivation")
        elif src not in profile_fields:
            fail(f"{where}: source '{src}' is not a source-profile field")
        check_concept(where, f.get("concept"))
        if f.get("counting_unit") is None and f.get("concept") in {"parcel-count", "building-count", "unit-count"}:
            fail(f"{where}: count without counting_unit")
        allowed = f.get("allowed") or {}
        if name == "resolution_outcome":
            ran_check("enum equals spec")
            if set(allowed.get("values", [])) != outcome_labels:
                fail(f"{where}: outcome values differ from vocabulary scheme {sorted(outcome_labels)}")

# --- crosswalk ---
cross = load(ROOT / "profiles/crosswalk-q01.yaml")
if cross:
    seen = set()
    for row in cross.get("rows", []):
        where = f"crosswalk-q01.yaml:{row.get('source_key')}.{row.get('column')}"
        ran_check("crosswalk row")
        for k in ("source_key", "column", "profile_field", "concept", "neo4j"):
            if k not in row:
                fail(f"{where}: missing '{k}'")
        seen.add(row.get("profile_field"))
        if row.get("profile_field") not in profile_fields:
            fail(f"{where}: profile_field '{row.get('profile_field')}' not in a source profile")
        check_concept(where, row.get("concept"))
        src = sources["sources"].get(row.get("source_key")) if sources else None
        if src is None:
            fail(f"{where}: source key not in data/sources.yaml")
        elif src.get("table") is not None:
            ran_check("crosswalk column in columns_used")
            if row.get("column") not in columns_used[row["source_key"]]:
                fail(f"{where}: column missing from data/sources.yaml columns_used")
        elif not is_pending(row):
            fail(f"{where}: non-database source row must be pending")
    ran_check("every profiled column crosswalked")
    for pf in profile_fields:
        if pf not in seen:
            fail(f"{pf}: profiled column is not in the crosswalk")

required_checks = {
    "concept IRI in watchline.ttl", "evidence profile fields", "enum equals spec",
    "source profile structure", "answer field has source, type, allowed",
    "crosswalk row", "crosswalk column in columns_used", "every profiled column crosswalked",
}
for name in sorted(required_checks - set(ran)):
    fail(f"check did not run: {name}")

for name in sorted(ran):
    print(f"ran: {name} x{ran[name]}")
if errors:
    print(f"\nFAILED: {len(errors)} problem(s)", file=sys.stderr)
    for e in errors:
        print(f"  - {e}", file=sys.stderr)
    sys.exit(1)
pend = sum(1 for p in profile_fields.values() if is_pending(p))
print(f"\nOK. {len(profile_fields)} source columns ({pend} pending), no skipped checks.")
