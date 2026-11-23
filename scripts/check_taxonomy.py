"""Check the SKOS hierarchy of vocabulary/watchline.ttl (Stage 3). Offline; reads only the vocabulary and the ontology file.

Fails (exit 1) if any check fails; nothing is skipped.
1. No skos:broader cycle.
2. Every broader/narrower link has its inverse, and both ends are in the same scheme.
3. A concept with a broader concept is not a top concept, and has exactly one broader concept unless listed in MULTIPLE_PARENTS.
4. Hierarchy is shallow (at most MAX_DEPTH levels below a top concept).
5. Every concept with a broader link has a dct:source (the source's own grouping or the question).
6. No SKOS hierarchy link is turned into an ontology axiom: ontology/watchline-onto.ttl has no skos:broader or skos:narrower.
7. skos:Collection members exist and are concepts.

Run: uv run python scripts/check_taxonomy.py
"""

import sys
from pathlib import Path

from rdflib import Graph, RDF
from rdflib.namespace import DCTERMS, SKOS

ROOT = Path(__file__).resolve().parents[1]
MULTIPLE_PARENTS: set[str] = set()   # concepts allowed more than one broader concept, each justified in taxonomy-notes.md
MAX_DEPTH = 2

results: list[bool] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  ({detail})" if detail and not ok else ""))


def short(node) -> str:
    return str(node).rsplit("/", 1)[-1]


def main() -> int:
    g = Graph()
    g.parse(ROOT / "vocabulary" / "watchline.ttl")
    concepts = set(g.subjects(RDF.type, SKOS.Concept))
    broader = {(a, b) for a, b in g.subject_objects(SKOS.broader)}
    narrower = {(b, a) for a, b in g.subject_objects(SKOS.narrower)}   # stored as (child, parent)

    parents: dict = {}
    for child, parent in broader | narrower:
        parents.setdefault(child, set()).add(parent)
    check("every broader/narrower link joins two concepts", all(c in concepts and p in concepts for c, p in broader | narrower))
    check("every broader link has its narrower inverse, and the reverse", broader == narrower,
          f"only broader: {sorted(short(c) + '>' + short(p) for c, p in broader - narrower)}; only narrower: {sorted(short(c) + '>' + short(p) for c, p in narrower - broader)}")

    def cyclic(node, seen=()):
        return node in seen or any(cyclic(p, seen + (node,)) for p in parents.get(node, ()))
    check("no broader cycle", not any(cyclic(c) for c in parents))

    def depth(node):
        return 0 if node not in parents else 1 + max(depth(p) for p in parents[node])
    check(f"every hierarchy is at most {MAX_DEPTH} levels deep", all(depth(c) <= MAX_DEPTH for c in parents))

    for child, ps in sorted(parents.items(), key=lambda kv: str(kv[0])):
        name = short(child)
        schemes = set(g.objects(child, SKOS.inScheme))
        check(f"{name} and its broader concepts share a scheme", all(set(g.objects(p, SKOS.inScheme)) & schemes for p in ps))
        check(f"{name} is not a top concept", not list(g.objects(child, SKOS.topConceptOf)))
        check(f"{name} has one broader concept" if name not in MULTIPLE_PARENTS else f"{name} may have several broader concepts",
              len(ps) == 1 or name in MULTIPLE_PARENTS, f"parents: {sorted(short(p) for p in ps)}")
        check(f"{name} has a dct:source", bool(list(g.objects(child, DCTERMS.source))))

    for coll in g.subjects(RDF.type, SKOS.Collection):
        check(f"collection {short(coll)} members are concepts", all(m in concepts for m in g.objects(coll, SKOS.member)))

    onto = (ROOT / "ontology" / "watchline-onto.ttl").read_text()
    check("the ontology file uses no skos:broader or skos:narrower", "skos:broader" not in onto and "skos:narrower" not in onto)

    failed = results.count(False)
    print(f"{len(results) - failed}/{len(results)} checks passed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
