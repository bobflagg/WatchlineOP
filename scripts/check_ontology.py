"""Check the Stage 5 ontology against the vocabulary, the schema and the reasoner.

Fails (exit 1) if any check fails; nothing is skipped. Needs Java and tools/robot (ROBOT) for the reasoner.
No database is touched.

1. Files parse; each element has a label equal to a mapped concept's preferred label, a comment and a question trace.
2. Element IRIs are in the ontology namespace; no concept IRI is used as an element.
3. Mapping rows name real concepts, real elements of the right kind and real graph names in profiles/qNN.yaml;
   every schema graph element and property has a mapping row; every element has a row.
4. Every axiom (disjointness, domain, functional, subclass) has a row in ontology-notes.md, and no row is stale.
5. Every answer field in profiles/qNN.yaml appears in the notes.
6. The reasoner (HermiT through ROBOT) finds the example data consistent, and every negative case inconsistent.
   The TBox and each ABox file are merged into one Turtle file first, because ROBOT reads files one at a time
   and would otherwise read undeclared properties as annotations.

Run: uv run python scripts/check_ontology.py
"""

import csv
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml
from rdflib.collection import Collection
from rdflib import Graph, Namespace, RDF, RDFS, OWL, URIRef, BNode
from rdflib.namespace import SKOS

ROOT = Path(__file__).resolve().parents[1]
ONTO = Namespace("https://watchline.example/onto/")
VOCAB = "https://watchline.example/vocab/"
ROBOT = ROOT / "tools" / "robot"
KINDS = {"class": OWL.Class, "object_property": OWL.ObjectProperty, "datatype_property": OWL.DatatypeProperty}
results: list[bool] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  ({detail})" if detail and not ok else ""))


def local(iri) -> str:
    return str(iri).rsplit("/", 1)[-1]


def section(text: str, title: str) -> str:
    """Every '### title' section, joined: each question adds its own."""
    return "\n".join(m.group(1) for m in re.finditer(rf"(?ms)^### {re.escape(title)}\s*$(.*?)(?=^##|\Z)", text))


def reason(graph: Graph, workdir: Path, name: str) -> tuple[int, str]:
    merged = workdir / f"{name}.ttl"
    graph.serialize(merged, format="turtle")
    p = subprocess.run([str(ROBOT), "reason", "--reasoner", "HermiT", "--input", str(merged)], capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def merge_nodes(schemas: list[dict]) -> dict:
    """Nodes by label; a later question that adds properties to an earlier node (Q3 on Contact) extends it."""
    nodes: dict = {}
    for q in schemas:
        for lab, n in q["graph"]["nodes"].items():
            if lab in nodes:
                nodes[lab] = {**nodes[lab], "properties": {**nodes[lab]["properties"], **n["properties"]}}
            else:
                nodes[lab] = n
    return nodes


def main() -> int:
    onto = Graph()
    onto.parse(ROOT / "ontology" / "watchline-onto.ttl")
    vocab = Graph()
    vocab.parse(ROOT / "vocabulary" / "watchline.ttl")
    schemas = [yaml.safe_load(f.read_text()) for f in sorted((ROOT / "profiles").glob("q[0-9][0-9].yaml"))]
    schema = {
        "graph": {
            "nodes": merge_nodes(schemas),
            "relationships": {r: v for q in schemas for r, v in q["graph"]["relationships"].items()},
        },
        "answer": {k: v for q in schemas for k, v in q["answer"].items()},
    }
    notes = (ROOT / "ontology" / "ontology-notes.md").read_text()
    rows = list(csv.DictReader((ROOT / "ontology" / "concept-mapping.csv").open()))

    elements = {s for k in KINDS.values() for s in onto.subjects(RDF.type, k) if str(s).startswith(str(ONTO))}
    elements |= set(onto.subjects(RDF.type, OWL.AnnotationProperty))
    domain_elements = {e for e in elements if e != ONTO.question}
    concepts = {str(c) for c in vocab.subjects(RDF.type, SKOS.Concept)}

    # 1-2. annotations and namespaces
    for e in sorted(elements, key=str):
        ok = bool(list(onto.objects(e, RDFS.label))) and bool(list(onto.objects(e, RDFS.comment)))
        if e != ONTO.question:
            ok = ok and bool(list(onto.objects(e, ONTO.question)))
        check(f"{local(e)} has a label, a comment and a question trace", ok)
    check("every element IRI is in the ontology namespace and none is a concept", all(str(e).startswith(str(ONTO)) for e in elements)
          and not any(str(e) in concepts for e in elements))

    # 3. mapping table
    by_iri = {r["element_iri"] for r in rows}
    bad_concept = sorted(local(r["concept_iri"]) for r in rows if r["concept_iri"] not in concepts)
    check("every mapping row names a concept in watchline.ttl", not bad_concept, f"unknown: {bad_concept}")
    bad_kind = sorted(local(r["element_iri"]) for r in rows
                      if (ONTO[local(r["element_iri"])], RDF.type, KINDS.get(r["element_kind"], OWL.Nothing)) not in onto)
    check("every mapping row names an element of the stated kind", not bad_kind, f"mismatch: {bad_kind}")
    graph_names = {n for n in schema["graph"]["nodes"]} | {r for r in schema["graph"]["relationships"]}
    # identity_only properties (a loader key, never an answer field) are not modeled
    graph_names |= {f"{lab}.{p}" for lab, node in schema["graph"]["nodes"].items()
                    for p, v in node["properties"].items() if not v.get("identity_only")}
    graph_names |= {f"{r}.{p}" for r, rel in schema["graph"]["relationships"].items()
                    for p, v in rel.get("properties", {}).items() if not v.get("identity_only")}
    mapped = {r["graph_name"] for r in rows if r["graph_name"]}
    check("every mapped graph name is in profiles/qNN.yaml", mapped <= graph_names, f"unknown: {sorted(mapped - graph_names)}")
    check("every graph label, relationship type and property has an ontology element", graph_names <= mapped,
          f"unmapped: {sorted(graph_names - mapped)}")
    check("every ontology element has a mapping row", {str(e) for e in domain_elements} <= by_iri,
          f"no row: {sorted(local(e) for e in domain_elements if str(e) not in by_iri)}")
    wrong_label = []
    for e in sorted(domain_elements, key=str):
        element_label = str(next(iter(onto.objects(e, RDFS.label)), "")).lower()
        prefs = {str(l).lower() for r in rows if r["element_iri"] == str(e)
                 for l in vocab.objects(URIRef(r["concept_iri"]), SKOS.prefLabel)}
        if element_label not in prefs:
            wrong_label.append(local(e))
    check("every element's label equals a mapped concept's preferred label", not wrong_label, f"differs: {wrong_label}")

    # 4. axioms against the notes
    axioms = {("disjointWith", frozenset((local(a), local(b)))) for a, b in onto.subject_objects(OWL.disjointWith)}
    def domain_name(c):
        if isinstance(c, BNode):  # union of classes
            members = Collection(onto, onto.value(c, OWL.unionOf))
            return "|".join(sorted(local(m) for m in members))
        return local(c)
    axioms |= {("domain", local(p), domain_name(c)) for p, c in onto.subject_objects(RDFS.domain)}
    axioms |= {("functional", local(p)) for p in onto.subjects(RDF.type, OWL.FunctionalProperty)}
    axioms |= {("subClassOf", local(a), local(b)) for a, b in onto.subject_objects(RDFS.subClassOf) if str(b).startswith(str(ONTO))}
    documented = set()
    for line in section(notes, "Axioms").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 2 or not cells[0] or set(cells[0]) <= {"-", " "} or cells[0] == "Axiom":
            continue
        toks = re.findall(r"`([^`]+)`", cells[0])
        if "disjointWith" in cells[0]:
            documented.add(("disjointWith", frozenset(toks)))
        elif " domain " in cells[0] and " or " in cells[0]:
            documented.add(("domain", toks[0], "|".join(sorted(toks[1:]))))
        elif " domain " in cells[0]:
            documented |= {("domain", t, toks[-1]) for t in toks[:-1]}
        elif cells[0].rstrip().endswith("functional"):
            documented |= {("functional", t) for t in toks}
        elif "subClassOf" in cells[0]:
            documented.add(("subClassOf", toks[0], toks[1]))
    check("every axiom has a reason in ontology-notes.md", axioms <= documented, f"undocumented: {sorted(map(str, axioms - documented))}")
    check("no reason in ontology-notes.md names an axiom that does not exist", documented <= axioms, f"stale: {sorted(map(str, documented - axioms))}")

    # 5. answer fields
    fields = {f for a in schema["answer"].values() for f in a["fields"]}
    answer_text = section(notes, "Answer fields")
    check("every answer field of profiles/qNN.yaml appears in the notes", all(f"`{f}`" in answer_text for f in fields),
          f"missing: {sorted(f for f in fields if f'`{f}`' not in answer_text)}")

    # 6. reasoner
    if not ROBOT.exists():
        check("tools/robot is present", False, "install ROBOT as described in the stage 5 procedure")
    else:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            for abox in sorted((ROOT / "ontology" / "abox").glob("q*.ttl")):
                g = Graph()
                g.parse(ROOT / "ontology" / "watchline-onto.ttl")
                g.parse(abox)
                code, out = reason(g, work, abox.stem)
                check(f"example data {abox.name} is consistent with no unsatisfiable class", code == 0, out.strip()[-160:])
            for neg in sorted((ROOT / "ontology" / "abox" / "negative").glob("*.ttl")):
                g = Graph()
                g.parse(ROOT / "ontology" / "watchline-onto.ttl")
                g.parse(neg)
                code, out = reason(g, work, neg.stem)
                check(f"negative case {neg.name} is flagged inconsistent", code != 0 and "inconsistent" in out.lower(), out.strip()[-160:])

    failed = results.count(False)
    print(f"{len(results) - failed}/{len(results)} checks passed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
