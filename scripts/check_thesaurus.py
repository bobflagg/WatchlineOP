"""Check the Stage 4 thesaurus: related links, notes, labels and external mappings.

Fails (exit 1) if any check fails; nothing is skipped. Reads vocabulary/ only; no database is touched.

1. Every skos:related has its inverse, and no related pair is also joined by skos:broader/narrower.
2. Every related pair has one row in vocabulary/thesaurus-notes.md with a known kind and a justification,
   and every row names a real pair.
3. Every concept is in a scheme; every concept without a related link has an Exceptions line.
4. No label (preferred, alternative or hidden) is shared by two concepts.
5. External mappings: if vocabulary/mappings/external.sssom.tsv exists, each row is valid; if not, the notes
   must record "None sought".

Run: uv run python scripts/check_thesaurus.py
"""

import re
import sys
from pathlib import Path

from rdflib import Graph, RDF
from rdflib.namespace import SKOS

ROOT = Path(__file__).resolve().parents[1]
SSSOM = ROOT / "vocabulary" / "mappings" / "external.sssom.tsv"
SKOS_MATCH = {"skos:exactMatch", "skos:closeMatch", "skos:broadMatch", "skos:narrowMatch", "skos:relatedMatch"}
results: list[bool] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  ({detail})" if detail and not ok else ""))


def slug(iri) -> str:
    return str(iri).rsplit("/", 1)[-1]


def section(text: str, title: str) -> str:
    m = re.search(rf"(?ms)^## {re.escape(title)}\s*$(.*?)(?=^## |\Z)", text)
    return m.group(1) if m else ""


def main() -> int:
    g = Graph()
    g.parse(ROOT / "vocabulary" / "watchline.ttl")
    notes = (ROOT / "vocabulary" / "thesaurus-notes.md").read_text()
    concepts = sorted(g.subjects(RDF.type, SKOS.Concept), key=str)

    # 1. symmetry and hierarchy
    related = {(a, b) for a, b in g.subject_objects(SKOS.related)}
    asym = sorted((slug(a), slug(b)) for a, b in related if (b, a) not in related)
    check("every skos:related has its inverse", not asym, f"one-way: {asym}")
    hier = {(a, b) for a, b in g.subject_objects(SKOS.broader)} | {(b, a) for a, b in g.subject_objects(SKOS.narrower)}
    both = sorted((slug(a), slug(b)) for a, b in related if (a, b) in hier or (b, a) in hier)
    check("no related pair is also joined by broader or narrower", not both, f"overlap: {both}")
    pairs = {tuple(sorted((slug(a), slug(b)))) for a, b in related}

    # 2. notes table
    rel = section(notes, "Related links")
    kinds = set(re.findall(r"(?m)^- `([a-z-]+)`:", rel))
    rows = re.findall(r"(?m)^\|\s*`([^`]+)`\s*\|\s*`([^`]+)`\s*\|\s*([a-z-]+)\s*\|\s*(\S.*?)\s*\|\s*$", rel)
    noted = {}
    for a, b, kind, why in rows:
        noted.setdefault(tuple(sorted((a, b))), []).append((kind, why))
    check("notes list at least one association kind", bool(kinds))
    check("each related pair has exactly one notes row", all(len(noted.get(p, [])) == 1 for p in pairs),
          f"missing or repeated: {sorted(p for p in pairs if len(noted.get(p, [])) != 1)}")
    check("each notes row names a real related pair", all(p in pairs for p in noted),
          f"not in the vocabulary: {sorted(p for p in noted if p not in pairs)}")
    check("each notes row has a known kind", all(k in kinds for v in noted.values() for k, _ in v),
          f"unknown: {sorted({k for v in noted.values() for k, _ in v if k not in kinds})}")

    # 3. schemes and exceptions
    check("every concept is in a scheme", all(list(g.objects(c, SKOS.inScheme)) for c in concepts))
    linked = {slug(a) for a, _ in related}
    exceptions = set(re.findall(r"`([^`]+)`", section(notes, "Exceptions")))
    unexplained = sorted(slug(c) for c in concepts if slug(c) not in linked and slug(c) not in exceptions)
    check("every unlinked concept has an Exceptions line", not unexplained, f"missing: {unexplained}")
    stale = sorted(e for e in exceptions if e in linked)
    check("no Exceptions line names a linked concept", not stale, f"linked: {stale}")

    # 4. labels
    seen: dict[str, str] = {}
    clash = []
    for c in concepts:
        for prop in (SKOS.prefLabel, SKOS.altLabel, SKOS.hiddenLabel):
            for lab in g.objects(c, prop):
                key = str(lab).strip().lower()
                if key in seen and seen[key] != slug(c):
                    clash.append((key, seen[key], slug(c)))
                seen[key] = slug(c)
    check("no label is shared by two concepts", not clash, f"shared: {clash}")

    # 5. external mappings
    if SSSOM.exists():
        lines = [l for l in SSSOM.read_text().splitlines() if l.strip() and not l.startswith("#")]
        header, body = lines[0].split("\t"), [l.split("\t") for l in lines[1:]]
        need = ["subject_id", "predicate_id", "object_id", "mapping_justification", "author_id", "mapping_date"]
        check("SSSOM header has the required columns", all(c in header for c in need))
        ok = True
        if all(c in header for c in need):
            ix = {c: header.index(c) for c in need}
            ok = all(r[ix["predicate_id"]] in SKOS_MATCH and r[ix["object_id"]].startswith("http")
                     and r[ix["mapping_justification"]] and any(slug(c) == r[ix["subject_id"]].rsplit("/", 1)[-1] for c in concepts)
                     for r in body)
        check("every SSSOM row has a known subject, a SKOS predicate, an IRI object and a justification", ok)
    else:
        check("no SSSOM file, and the notes record 'None sought'", "none sought" in section(notes, "External mappings").lower())

    failed = results.count(False)
    print(f"{len(results) - failed}/{len(results)} checks passed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
