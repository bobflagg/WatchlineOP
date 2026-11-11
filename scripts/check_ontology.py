"""Stage 5 check: ontology, example data, mapping table, reasoner, report and OOPS! record.

Reads ontology/watchline-onto.ttl, ontology/abox/, ontology/concept-mapping.csv, ontology/ontology-notes.md
and vocabulary/watchline.ttl. Runs ROBOT (tools/robot or `robot` on PATH) with the pinned reasoner.
Exits nonzero on any failure. A check that cannot run counts as a failure.
"""
import csv
import hashlib
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml
from rdflib import BNode, Graph, Literal, Namespace, RDF, RDFS, URIRef
from rdflib.collection import Collection
from rdflib.namespace import OWL, SKOS, XSD

ROOT = Path(__file__).resolve().parent.parent
ONTO_DIR = ROOT / "ontology"
TBOX = ONTO_DIR / "watchline-onto.ttl"
ABOX = ONTO_DIR / "abox" / "q01.ttl"
NEGATIVE_DIR = ONTO_DIR / "abox" / "negative"
MAPPING = ONTO_DIR / "concept-mapping.csv"
NOTES = ONTO_DIR / "ontology-notes.md"
REPORT_PROFILE = ONTO_DIR / "report-profile.txt"
VOCAB_FILE = ROOT / "vocabulary" / "watchline.ttl"
ANSWER_PROFILE = ROOT / "profiles" / "q01-answer.yaml"

VOCAB = Namespace("https://watchline.example/vocab/")
ONTO = Namespace("https://watchline.example/onto/")
TRACE = ONTO.traceQuestion
REASONER = "HermiT"
KIND_OF = {
    OWL.Class: "class",
    OWL.ObjectProperty: "object_property",
    OWL.DatatypeProperty: "datatype_property",
    OWL.AnnotationProperty: "annotation_property",
}
EXPECTED_CHECKS = [
    "files parse", "element has label, definition and trace", "no concept IRI as class or property",
    "concept IRI only as mapped controlled value", "mapping row well formed", "mapping concept exists",
    "mapping element exists with the stated kind", "every element has a mapping row", "mapping questions match trace",
    "axiom has a reason", "pilot table covers every answer field", "tool versions recorded",
    "reasoner: example data consistent", "reasoner: expected inference", "reasoner: negative case flagged",
    "report has no error", "OOPS! result recorded for this TBox",
]

errors: list[str] = []
ran: dict[str, int] = {}


def fail(msg: str) -> None:
    errors.append(msg)


def ran_check(name: str) -> None:
    ran[name] = ran.get(name, 0) + 1


def local(node) -> str:
    return str(node).removeprefix(str(ONTO)).removeprefix(str(VOCAB))


def die(msg: str) -> None:
    print(f"FAILED: {msg}", file=sys.stderr)
    sys.exit(1)


# --- parse ---------------------------------------------------------------

for p in (TBOX, ABOX, MAPPING, NOTES, REPORT_PROFILE, VOCAB_FILE, ANSWER_PROFILE):
    if not p.exists():
        die(f"{p.relative_to(ROOT)} not found")
notes = NOTES.read_text()

tbox, vocab = Graph(), Graph()
tbox.parse(TBOX, format="turtle")
vocab.parse(VOCAB_FILE, format="turtle")
Graph().parse(ABOX, format="turtle")
negatives = sorted(NEGATIVE_DIR.glob("*.ttl"))
for n in negatives:
    Graph().parse(n, format="turtle")
ran_check("files parse")

with MAPPING.open(newline="") as fh:
    mapping = list(csv.DictReader(fh))
if not mapping:
    die("concept-mapping.csv has no rows")

concepts = {str(s) for s in vocab.subjects(RDF.type, SKOS.Concept)}

# --- elements ------------------------------------------------------------

elements: dict[str, str] = {}  # onto-namespace element iri -> kind
for rdf_type, kind in KIND_OF.items():
    for s in tbox.subjects(RDF.type, rdf_type):
        if isinstance(s, URIRef) and str(s).startswith(str(ONTO)):
            elements[str(s)] = kind
        if isinstance(s, URIRef) and str(s).startswith(str(VOCAB)):
            fail(f"{local(s)}: a concept IRI is declared as {kind}")
        ran_check("no concept IRI as class or property")

for iri in elements:
    s = URIRef(iri)
    for prop, what in ((RDFS.label, "label"), (RDFS.comment, "definition (rdfs:comment)"), (TRACE, "question trace")):
        if not any(True for _ in tbox.objects(s, prop)):
            fail(f"{local(s)}: missing {what}")
    ran_check("element has label, definition and trace")

# Concept IRIs may appear only as mapped controlled values.
controlled = {r["element_iri"] for r in mapping if r["element_kind"] == "controlled_value"}
for s, p, o in tbox:
    for term in (s, p, o):
        if isinstance(term, URIRef) and str(term).startswith(str(VOCAB)):
            if str(term) not in controlled:
                fail(f"concept IRI {local(term)} used in the TBox without a controlled_value mapping row")
            if term == p or (p == RDF.type and term == o):
                fail(f"concept IRI {local(term)} used as a property or a class")
            ran_check("concept IRI only as mapped controlled value")
for cv in controlled:
    if cv not in concepts:
        fail(f"controlled value {cv} is not a concept in watchline.ttl")
    if (URIRef(cv), RDF.type, OWL.NamedIndividual) not in tbox:
        fail(f"controlled value {local(cv)} is not declared as an owl:NamedIndividual")

# --- mapping table -------------------------------------------------------

REQUIRED = ["concept_iri", "element_iri", "element_kind", "questions", "note"]
if list(mapping[0].keys()) != REQUIRED:
    fail(f"mapping columns must be {REQUIRED}, found {list(mapping[0].keys())}")
valid_kinds = set(KIND_OF.values()) | {"controlled_value", "individual"}
rows_by_element: dict[str, list[dict]] = {}
for i, row in enumerate(mapping, start=2):
    where = f"mapping row {i}"
    if row["element_kind"] not in valid_kinds:
        fail(f"{where}: unknown element_kind {row['element_kind']!r}")
    if not row["questions"].strip():
        fail(f"{where}: no questions")
    if not row["concept_iri"]:
        if not row["note"].startswith("no concept:"):
            fail(f"{where}: empty concept_iri needs a note starting 'no concept:'")
    elif row["concept_iri"] not in concepts:
        fail(f"{where}: concept {row['concept_iri']} is not in watchline.ttl")
    ran_check("mapping row well formed")
    ran_check("mapping concept exists")
    rows_by_element.setdefault(row["element_iri"], []).append(row)
    if row["element_kind"] == "controlled_value":
        if row["concept_iri"] != row["element_iri"]:
            fail(f"{where}: a controlled_value row must keep its concept IRI as the element IRI")
    else:
        actual = elements.get(row["element_iri"])
        if actual is None:
            fail(f"{where}: element {row['element_iri']} not in the ontology")
        elif actual != row["element_kind"]:
            fail(f"{where}: {local(URIRef(row['element_iri']))} is a {actual}, row says {row['element_kind']}")
        ran_check("mapping element exists with the stated kind")

for iri in elements:
    if iri not in rows_by_element:
        fail(f"{local(URIRef(iri))}: no mapping row")
    ran_check("every element has a mapping row")
    traces = {str(o) for o in tbox.objects(URIRef(iri), TRACE)}
    mapped = {q.strip() for r in rows_by_element.get(iri, []) for q in r["questions"].split(";")}
    if traces != mapped:
        fail(f"{local(URIRef(iri))}: trace {sorted(traces)} differs from mapping questions {sorted(mapped)}")
    ran_check("mapping questions match trace")

# --- axiom reasons -------------------------------------------------------


def named(node) -> bool:
    return isinstance(node, URIRef) and str(node).startswith(str(ONTO))


def restriction_property(node):
    return next(tbox.objects(node, OWL.onProperty), None)


needed: set[tuple[str, str]] = set()
for s, _, o in tbox.triples((None, RDFS.subClassOf, None)):
    if named(s):
        needed.add((local(s), "subclass" if isinstance(o, URIRef) else "restriction"))
for s, _, o in tbox.triples((None, OWL.equivalentClass, None)):
    if named(s):
        needed.add((local(s), "equivalent"))
for s, _, o in tbox.triples((None, OWL.disjointWith, None)):
    for x in (s, o):
        if named(x):
            needed.add((local(x), "disjoint"))
for ax in tbox.subjects(RDF.type, OWL.AllDisjointClasses):
    for m in Collection(tbox, next(tbox.objects(ax, OWL.members))):
        if named(m):
            needed.add((local(m), "disjoint"))
        elif (p := restriction_property(m)) is not None:
            needed.add((local(p), "disjoint"))
for p in elements:
    for _, _, d in tbox.triples((URIRef(p), RDFS.domain, None)):
        needed.add((local(URIRef(p)), "domain"))
    for _, _, rg in tbox.triples((URIRef(p), RDFS.range, None)):
        if isinstance(rg, URIRef) and str(rg).startswith(str(ONTO)):
            needed.add((local(URIRef(p)), "range"))
    if (URIRef(p), OWL.propertyChainAxiom, None) in tbox:
        needed.add((local(URIRef(p)), "chain"))

reasons: set[tuple[str, str]] = set()
section = re.search(r"## Axioms\n(.*?)(?=\n## |\Z)", notes, re.S)
if not section:
    die("ontology-notes.md has no '## Axioms' section")
for line in section.group(1).splitlines():
    cells = [c.strip() for c in line.strip().strip("|").split("|")]
    if len(cells) == 4 and re.search(r"`", cells[0]):
        if not cells[3]:
            fail(f"notes: empty reason in axiom row {cells[0]}")
        for name in re.findall(r"`([^`]+)`", cells[0]):
            reasons.add((name, cells[1]))
for key in sorted(needed):
    if key not in reasons:
        fail(f"axiom without a reason in the notes: {key[0]} ({key[1]})")
    ran_check("axiom has a reason")

# --- pilot table ---------------------------------------------------------

pilot = re.search(r"## Answer-shape pilot\n(.*?)(?=\n## |\Z)", notes, re.S)
if not pilot:
    die("ontology-notes.md has no '## Answer-shape pilot' section")
fields = yaml.safe_load(ANSWER_PROFILE.read_text())["fields"]
for name in fields:
    row = re.search(rf"^\|\s*`{re.escape(name)}`\s*\|(.*)\|\s*$", pilot.group(1), re.M)
    if not row or len([c for c in row.group(1).split("|") if c.strip()]) < 3:
        fail(f"pilot table: no complete row for answer field {name}")
    ran_check("pilot table covers every answer field")

# --- tools ---------------------------------------------------------------

robot = shutil.which("robot") or str(ROOT / "tools" / "robot")
if not Path(robot).exists() and not shutil.which("robot"):
    die("ROBOT not found (tools/robot or robot on PATH); the reasoner step cannot run")


def run_robot(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([robot, *args], capture_output=True, text=True, timeout=600)


ver = run_robot("--version")
robot_version = ver.stdout.strip().splitlines()[-1] if ver.returncode == 0 and ver.stdout.strip() else ""
if not robot_version.startswith("ROBOT version"):
    die("could not read the ROBOT version")
for needle in (robot_version, f"{REASONER} "):
    if needle not in notes:
        fail(f"notes do not record the tool version: {needle!r}")
    ran_check("tool versions recorded")
versions = re.search(r"reasoner:\s*HermiT\s+(\S+)", notes)
jar = ROOT / "tools" / "robot.jar"
if versions and jar.exists():
    pom = subprocess.run(["unzip", "-p", str(jar), "META-INF/maven/net.sourceforge.owlapi/org.semanticweb.hermit/pom.properties"],
                         capture_output=True, text=True)
    actual = re.search(r"version=(\S+)", pom.stdout)
    if not actual or actual.group(1) != versions.group(1):
        fail(f"notes record HermiT {versions.group(1)}, jar has {actual.group(1) if actual else 'unknown'}")
elif not versions:
    fail("notes do not record 'reasoner: HermiT <version>'")

# --- reasoner ------------------------------------------------------------

tmp = Path(tempfile.mkdtemp(prefix="check_ontology_"))


def merged(*paths: Path) -> Path:
    # ROBOT reads each file alone; assertions in a file without the property declarations would be
    # read as annotations. Merge the graphs first so the reasoner sees object and data property assertions.
    g = Graph()
    for p in paths:
        g.parse(p, format="turtle")
    out = tmp / ("m_" + "_".join(p.stem for p in paths) + ".ttl")
    g.serialize(out, format="turtle")
    return out


pos = merged(TBOX, ABOX)
inferred = tmp / "inferred.ttl"
res = run_robot("reason", "--input", str(pos), "--reasoner", REASONER, "--dump-unsatisfiable", str(tmp / "unsat.owl"),
                "--axiom-generators", "ClassAssertion PropertyAssertion", "--exclude-tautologies", "true",
                "--create-new-ontology", "true", "--output", str(inferred))
if res.returncode != 0 or "ERROR" in res.stdout + res.stderr:
    fail("reasoner: example data inconsistent or classes unsatisfiable:\n" + "\n".join(
        l for l in (res.stdout + res.stderr).splitlines() if "ERROR" in l))
else:
    ran_check("reasoner: example data consistent")
    inf = Graph()
    inf.parse(inferred, format="turtle")
    ID = Namespace("https://watchline.example/id/")
    if (ID["resolution-synthetic-inferred"], RDF.type, ONTO.InferredResolution) not in inf:
        fail("reasoner: synthetic alternate-address resolution was not classified as InferredResolution")
    if (ID["resolution-synthetic-ambiguous"], RDF.type, ONTO.InferredResolution) in inf:
        fail("reasoner: ambiguous example wrongly classified as InferredResolution")
    for lot, n in (("taxlot-3008210012", 3), ("taxlot-3008260002", 1)):
        got = {o for o in inf.objects(ID[lot], ONTO.hasRecordedBuilding)}
        if len(got) != n:
            fail(f"reasoner: {lot} should have {n} recorded building(s) by property chain, found {len(got)}")
    ran_check("reasoner: expected inference")

if not negatives:
    fail("no negative cases in ontology/abox/negative/")
for n in negatives:
    out = run_robot("reason", "--input", str(merged(TBOX, n)), "--reasoner", REASONER)
    text = out.stdout + out.stderr
    if out.returncode == 0 or "inconsistent" not in text:
        fail(f"reasoner: negative case {n.name} was not flagged inconsistent")
    ran_check("reasoner: negative case flagged")

# --- report --------------------------------------------------------------

rep = run_robot("report", "--input", str(TBOX), "--profile", str(REPORT_PROFILE), "--fail-on", "ERROR",
                "--output", str(tmp / "report.tsv"))
if rep.returncode != 0:
    fail("robot report found errors:\n" + "\n".join(l for l in (rep.stdout + rep.stderr).splitlines() if "ERROR" in l))
ran_check("report has no error")

# --- OOPS! ---------------------------------------------------------------

oops = re.search(r"## OOPS! result\n(.*?)(?=\n## |\Z)", notes, re.S)
digest = hashlib.sha256(TBOX.read_bytes()).hexdigest()
if not oops:
    fail("OOPS! result not recorded: the stage stays pending (no '## OOPS! result' section)")
else:
    m = re.search(r"tbox-sha256:\s*([0-9a-f]{64})", oops.group(1))
    c = re.search(r"unresolved critical pitfalls:\s*(\d+)", oops.group(1))
    if not m or not c:
        fail("OOPS! section needs 'tbox-sha256: <hash>' and 'unresolved critical pitfalls: <n>'")
    else:
        if m.group(1) != digest:
            fail(f"OOPS! result is for a different TBox (current sha256 {digest}); rerun OOPS! on the current file")
        if int(c.group(1)) != 0:
            fail(f"OOPS! reports {c.group(1)} unresolved critical pitfalls")
    ran_check("OOPS! result recorded for this TBox")

# --- result --------------------------------------------------------------

shutil.rmtree(tmp, ignore_errors=True)
for name in EXPECTED_CHECKS:
    if ran.get(name, 0) == 0:
        if name == "OOPS! result recorded for this TBox" and not oops:
            continue  # already failed above
        fail(f"check did not run: {name}")
for name, count in sorted(ran.items()):
    print(f"ran: {name} x{count}")
if errors:
    print("\nFAILED:", file=sys.stderr)
    for e in errors:
        print(f"  - {e}", file=sys.stderr)
    sys.exit(1)
print(f"\nOK. {len(elements)} elements, {len(mapping)} mapping rows, {len(negatives)} negative cases, no skipped checks.")
