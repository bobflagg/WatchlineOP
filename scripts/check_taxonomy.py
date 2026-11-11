"""Stage 3 check: validate skos:broader/narrower structure in vocabulary/watchline.ttl against vocabulary/taxonomy-notes.md.

Exits nonzero on any failure. A check that cannot run counts as a failure.
validate_skos (the skos MCP server) stays the authority on SKOS validity.
"""
import re
import sys
from pathlib import Path

from rdflib import Graph, Namespace, RDF
from rdflib.namespace import SKOS

ROOT = Path(__file__).resolve().parent.parent
VOCAB = Namespace("https://watchline.example/vocab/")
NOTES = ROOT / "vocabulary" / "taxonomy-notes.md"

errors: list[str] = []
ran: dict[str, int] = {}


def fail(msg: str) -> None:
    errors.append(msg)


def ran_check(name: str) -> None:
    ran[name] = ran.get(name, 0) + 1


def slug(node) -> str:
    return str(node).removeprefix(str(VOCAB))


g = Graph()
g.parse(ROOT / "vocabulary" / "watchline.ttl", format="turtle")
if not NOTES.exists():
    print(f"FAILED: {NOTES.relative_to(ROOT)} not found", file=sys.stderr)
    sys.exit(1)
notes = NOTES.read_text()

# Links tables: | `child` | `parent` | meaning | justification |
rows: dict[tuple[str, str], str] = {}
for m in re.finditer(r"^\|\s*`([^`]+)`\s*\|\s*`([^`]+)`\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*$", notes, re.M):
    child, parent, meaning, just = m.groups()
    if (child, parent) in rows:
        fail(f"notes: duplicate link row {child} -> {parent}")
    if not just.strip():
        fail(f"notes: empty justification for {child} -> {parent}")
    rows[(child, parent)] = meaning.strip()

# Exception lines mention backticked slugs in bullet lines under an "Exceptions" heading.
exception_text = "\n".join(
    sec for sec in re.findall(r"### Exceptions\n(.*?)(?=\n#|\Z)", notes, re.S)
)

# Broader links, normalised to child -> parent (skos:narrower counts as the inverse).
links: set[tuple[str, str]] = set()
for c, _, p in g.triples((None, SKOS.broader, None)):
    links.add((slug(c), slug(p)))
for p, _, c in g.triples((None, SKOS.narrower, None)):
    links.add((slug(c), slug(p)))
ran_check("links collected")

concepts = {slug(c) for c in g.subjects(RDF.type, SKOS.Concept)}

def schemes(s: str) -> set[str]:
    return {slug(x) for x in g.objects(VOCAB[s], SKOS.inScheme)}

# 1. Endpoints exist and sit in the same scheme.
for child, parent in sorted(links):
    ran_check("endpoint exists and shares a scheme")
    for end in (child, parent):
        if end not in concepts:
            fail(f"{child} -> {parent}: {end} is not a skos:Concept in watchline.ttl")
    if child in concepts and parent in concepts and not (schemes(child) & schemes(parent)):
        if f"`{child}`" not in exception_text:
            fail(f"{child} -> {parent}: endpoints share no scheme and no exception note")

# 2. No cycles.
parents: dict[str, set[str]] = {}
for c, p in links:
    parents.setdefault(c, set()).add(p)
ran_check("no broader cycle")
visiting: set[str] = set()
done: set[str] = set()

def visit(n: str, path: list[str]) -> None:
    if n in done:
        return
    if n in visiting:
        fail("broader cycle: " + " -> ".join(path[path.index(n):] + [n]))
        return
    visiting.add(n)
    for p in sorted(parents.get(n, ())):
        visit(p, path + [p])
    visiting.discard(n)
    done.add(n)

for n in sorted(parents):
    visit(n, [n])

# 3. Every broader link has a justification row, and every row matches a link.
for link in sorted(links):
    ran_check("link has justification row")
    if link not in rows:
        fail(f"{link[0]} -> {link[1]}: no justification row in taxonomy-notes.md")
for link in sorted(rows):
    ran_check("justification row matches a link")
    if link not in links:
        fail(f"notes row {link[0]} -> {link[1]} has no skos:broader link in watchline.ttl")

# 4. One hierarchy meaning per branch; multiple parents need an exception note.
def root(n: str, seen=()) -> str:
    ps = sorted(parents.get(n, ()))
    return n if not ps or n in seen else root(ps[0], seen + (n,))

meanings: dict[str, set[str]] = {}
for child, parent in links:
    if (child, parent) in rows:
        meanings.setdefault(root(parent), set()).add(rows[(child, parent)])
for branch, ms in sorted(meanings.items()):
    ran_check("one meaning per branch")
    if len(ms) > 1 and f"`{branch}`" not in exception_text:
        fail(f"branch {branch}: mixed meanings {sorted(ms)} without an exception note")
for child, ps in sorted(parents.items()):
    ran_check("multiple parents noted")
    if len(ps) > 1 and f"`{child}`" not in exception_text:
        fail(f"{child}: {len(ps)} broader parents without an exception note")

required_checks = {
    "links collected", "endpoint exists and shares a scheme", "no broader cycle",
    "link has justification row", "justification row matches a link",
    "one meaning per branch", "multiple parents noted",
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
print(f"\nOK. {len(links)} broader links, {len(rows)} justified, no skipped checks.")
