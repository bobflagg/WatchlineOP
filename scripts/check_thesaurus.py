"""Stage 4 check: validate related links, scheme membership and external mappings.

Reads vocabulary/watchline.ttl, vocabulary/thesaurus-notes.md and vocabulary/mappings/external.sssom.tsv.
Exits nonzero on any failure. A check that cannot run counts as a failure.
validate_skos (the skos MCP server) stays the authority on SKOS validity.
"""
import csv
import io
import re
import sys
from pathlib import Path

import yaml
from rdflib import Graph, Namespace, RDF
from rdflib.namespace import SKOS

ROOT = Path(__file__).resolve().parent.parent
VOCAB = Namespace("https://watchline.example/vocab/")
NOTES = ROOT / "vocabulary" / "thesaurus-notes.md"
SSSOM = ROOT / "vocabulary" / "mappings" / "external.sssom.tsv"
ALLOWED_PREDICATES = {"skos:exactMatch", "skos:closeMatch", "skos:broadMatch", "skos:narrowMatch", "skos:relatedMatch"}
REQUIRED_COLUMNS = {"subject_id", "predicate_id", "object_id", "mapping_justification", "author_id", "mapping_date"}

errors: list[str] = []
ran: dict[str, int] = {}


def fail(msg: str) -> None:
    errors.append(msg)


def ran_check(name: str) -> None:
    ran[name] = ran.get(name, 0) + 1


def slug(node) -> str:
    return str(node).removeprefix(str(VOCAB))


for path in (NOTES, SSSOM, ROOT / "vocabulary" / "watchline.ttl"):
    if not path.exists():
        print(f"FAILED: {path.relative_to(ROOT)} not found", file=sys.stderr)
        sys.exit(1)

g = Graph()
g.parse(ROOT / "vocabulary" / "watchline.ttl", format="turtle")
notes = NOTES.read_text()
concepts = {slug(c) for c in g.subjects(RDF.type, SKOS.Concept)}

# Association kinds: bullets "- `kind`: ..." under "## Association kinds".
kinds_section = re.search(r"## Association kinds\n(.*?)(?=\n## )", notes, re.S)
kinds = set(re.findall(r"^- `([^`]+)`", kinds_section.group(1), re.M)) if kinds_section else set()
ran_check("kinds list read")
if not kinds:
    fail("notes: no association kinds found")

# Related links table.
section = re.search(r"## Related links\n(.*?)(?=\n## )", notes, re.S)
rows: dict[frozenset, tuple[str, str]] = {}
if not section:
    fail("notes: no Related links section")
else:
    for m in re.finditer(r"^\|\s*`([^`]+)`\s*\|\s*`([^`]+)`\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*$", section.group(1), re.M):
        a, b, kind, just = m.groups()
        key = frozenset((a, b))
        ran_check("related row well formed")
        if a == b or len(key) != 2:
            fail(f"notes: row {a} / {b} is not a pair of different concepts")
        if key in rows:
            fail(f"notes: pair {a} / {b} listed more than once")
        if kind not in kinds:
            fail(f"notes: {a} / {b}: kind '{kind}' not in the Association kinds list")
        if not just.strip():
            fail(f"notes: {a} / {b}: empty justification")
        rows[key] = (kind, just)

# Related triples.
related = {(slug(a), slug(b)) for a, b in g.subject_objects(SKOS.related)}
ran_check("related collected")

# 1. Symmetry.
for a, b in sorted(related):
    ran_check("related has inverse")
    if (b, a) not in related:
        fail(f"{a} skos:related {b} has no inverse")
    for end in (a, b):
        if end not in concepts:
            fail(f"related link {a} / {b}: {end} is not a skos:Concept")

# 2. Related is disjoint from hierarchy (direct or through any chain of broader links).
broader: dict[str, set[str]] = {}
for c, p in g.subject_objects(SKOS.broader):
    broader.setdefault(slug(c), set()).add(slug(p))
for p, c in g.subject_objects(SKOS.narrower):
    broader.setdefault(slug(c), set()).add(slug(p))


def ancestors(n: str) -> set[str]:
    seen: set[str] = set()
    stack = [n]
    while stack:
        for p in broader.get(stack.pop(), ()):
            if p not in seen:
                seen.add(p)
                stack.append(p)
    return seen


for a, b in sorted(related):
    ran_check("related disjoint from hierarchy")
    if b in ancestors(a) or a in ancestors(b):
        fail(f"{a} / {b}: related pair is also connected by skos:broader")

# 3. Every related pair has a notes row, and every row matches a pair.
pairs = {frozenset(p) for p in related}
for key in sorted(pairs, key=sorted):
    ran_check("related pair has notes row")
    if key not in rows:
        fail(f"{' / '.join(sorted(key))}: no row in thesaurus-notes.md")
for key in sorted(rows, key=sorted):
    ran_check("notes row matches a related pair")
    if key not in pairs:
        fail(f"notes row {' / '.join(sorted(key))} has no skos:related link in watchline.ttl")

# 4. Scheme membership.
schemes = {slug(s) for s in g.subjects(RDF.type, SKOS.ConceptScheme)}
for c in sorted(concepts):
    ran_check("concept in an intended scheme")
    in_schemes = {slug(s) for s in g.objects(VOCAB[c], SKOS.inScheme)}
    if not in_schemes:
        fail(f"{c}: not in any scheme")
    elif not in_schemes <= schemes:
        fail(f"{c}: inScheme names an undeclared scheme {sorted(in_schemes - schemes)}")

# 5. SSSOM.
raw = SSSOM.read_text().splitlines()
meta = yaml.safe_load("\n".join(l[1:] for l in raw if l.startswith("#"))) or {}
curie_map = meta.get("curie_map") or {}
ran_check("sssom metadata read")
if not curie_map:
    fail("sssom: no curie_map in the header")
reader = csv.DictReader(io.StringIO("\n".join(l for l in raw if not l.startswith("#"))), delimiter="\t")
missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
if missing:
    fail(f"sssom: missing columns {sorted(missing)}")
else:
    seen_rows: set[tuple] = set()
    for i, r in enumerate(reader, 1):
        ran_check("sssom row checked")
        where = f"sssom row {i}"
        subj = r["subject_id"]
        prefix, _, local = subj.partition(":")
        if curie_map.get(prefix) != str(VOCAB) or local not in concepts:
            fail(f"{where}: subject {subj} is not a known concept")
        if r["predicate_id"] not in ALLOWED_PREDICATES:
            fail(f"{where}: predicate {r['predicate_id']} is not an allowed SKOS mapping predicate")
        obj_prefix, _, obj_local = r["object_id"].partition(":")
        base = curie_map.get(obj_prefix)
        if not base or not obj_local or not re.fullmatch(r"https?://[^\s<>\"]+", base + obj_local):
            fail(f"{where}: object {r['object_id']} does not expand to a well-formed IRI")
        if not r["mapping_justification"].strip():
            fail(f"{where}: empty mapping_justification")
        for col in ("author_id", "mapping_date"):
            if not r[col].strip():
                fail(f"{where}: empty {col}")
        key = (subj, r["predicate_id"], r["object_id"])
        if key in seen_rows:
            fail(f"{where}: duplicate mapping {key}")
        seen_rows.add(key)

required_checks = {
    "kinds list read", "related collected", "related has inverse", "related disjoint from hierarchy",
    "related pair has notes row", "notes row matches a related pair", "concept in an intended scheme",
    "sssom metadata read", "sssom row checked", "related row well formed",
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
print(f"\nOK. {len(pairs)} related pairs, {len(rows)} justified, {ran['sssom row checked']} mappings, no skipped checks.")
