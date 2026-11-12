# Stage 5 procedure: ontology, per question

Run this for each competency question after its [stage 4](stage4-procedure.md) is accepted, one question at a time. Stage definition and exit criterion: [roadmap.md](roadmap.md#stages) (Stage 5 row, exit criterion 5) and the [SKOS-to-ontology mapping policy](roadmap.md#skos-to-ontology-mapping). Tools: [tech-stack.md](tech-stack.md).

To run it in a fresh Claude Code session, start with: "Execute specs/stage5-procedure.md for QNN."

**Goal:** turn the question's approved vocabulary into a small OWL 2 ontology fragment that states what the question's graph holds and what its answer may say, test it against example data taken from the verified fixtures, and trace every element to a concept, a graph element and a question. Add only what the question needs.

## Ground rules

- Check first that the question's stages 1 to 4 are accepted in `specs/decisions.md` and that `make profiles` and `make thesaurus` pass (and `make taxonomy` once it exists). If not, stop and say so.
- Read: `CLAUDE.md` (auto-loaded), the question file, `vocabulary/watchline.ttl`, `vocabulary/taxonomy-notes.md`, `vocabulary/thesaurus-notes.md`, this question's `profiles/qNN.yaml`, `specs/physical-implementation.md` (sections 2 and 3), `specs/decisions.md`, and the existing `ontology/` files.
- Three namespaces stay separate: concepts (`https://watchline.example/vocab/`), ontology elements (`https://watchline.example/onto/`), instances (`https://watchline.example/id/`). Never use a concept IRI as a class or property IRI, except a controlled value that the mapping table explicitly records.
- No automatic promotion. A `skos:broader` link is not a subclass axiom, a `skos:related` link is not an object property, and a concept does not become a class by existing. Disjointness is declared only where the definitions support it (start from the candidates in `taxonomy-notes.md`).
- **The ontology follows the schema.** The graph's labels, relationship types and properties are already fixed in `profiles/qNN.yaml` and checked against the live graph. Each ontology class or property that corresponds to a graph element records its graph name. Do not rename graph elements here.
- Reuse before minting. Reuse an existing element when its meaning fits. Use PROV-O only when a question stores provenance (derived edges, claims, documents, cached responses); database facts carry dataset-level provenance and need no PROV-O terms.
- Preserve the specs' distinctions where the question involves them: recorded, derived and reported are kept apart; roles are not collapsed; lot-wide values are not attached to buildings; Operational Network and Owner Portfolio memberships are scoped to a source snapshot and run; no universal one-building-per-lot rule.
- An OWL class does not require a physical node. Stage 6 decides how the ontology's rules are checked on the graph.
- Do not commit to Git unless asked. Stop and ask when a decision is unsettled.

## One-time setup (first question only)

Confirm with the user, then log in [decisions.md](decisions.md):

- **Layout:** `ontology/watchline-onto.ttl` (TBox and CBox), `ontology/abox/qNN.ttl` (example data), `ontology/abox/negative/` (cases that must be rejected), `ontology/concept-mapping.csv`, `ontology/ontology-notes.md`. Turtle is the committed format.
- **Naming:** classes UpperCamelCase, properties lowerCamelCase, stable once minted. Every element gets `rdfs:label` (from the approved preferred label), an `rdfs:comment` definition specific to its formal role, and a question trace.
- **Mapping table columns:** `concept_iri`, `element_iri`, `element_kind` (class, object_property, datatype_property, annotation_property, controlled_value, individual), `graph_name` (from `profiles/qNN.yaml`, blank if not stored in the graph), `questions`, `note`. Unused concepts need no row.
- **Toolchain:** check `java -version` and `tools/robot --version`. If ROBOT is missing, ask the user before installing it. Choose and pin the reasoner (ELK or HermiT) and record the versions actually used.
- **Pitfall scan:** OOPS! is a web service. Submit the TBox file only, never the example data, and only with the user's go-ahead. If the user prefers, they run it and paste the result.
- **Versioning:** POC rules apply. Set an ontology IRI, no version IRI.
- **Check script:** `scripts/check_ontology.py` (`rdflib`) behind `make ontology` (step 9).

## Per-question steps

1. **List what the question requires.** From its answer fields, `profiles/qNN.yaml` and caveats, list the things it talks about (candidate classes), relations between them, attributes with datatypes, value sets, and rules about what may be asserted. Start from the schema's graph elements and answer fields so nothing the graph holds is left out.
2. **Decide each element's kind.** For each item choose: class, object property, datatype property, controlled value (a SKOS concept used directly, as the address resolution outcomes are), annotation, or not modeled. Terms Stage 2 listed as tool output or answer contract (not stored in the graph) are usually not modeled; write the reason for each.
3. **Draft the elements.** Mint IRIs in the ontology namespace. Give each a label, a role-specific definition and a question trace.
4. **Add axioms sparingly.** Subclass axioms only where the is-a test holds on the formal meaning. Domain and range only where every use satisfies them (they cause inferences). Disjointness, functional properties and cardinality only where the definitions or the loaded data support them. For each axiom write a one-line reason in `ontology-notes.md`. Rules OWL cannot express (required properties, closed-world checks, counting-unit rules) are not forced into axioms. List them in `ontology-notes.md` under **Rules for Stage 6 shapes**.
5. **Write the mapping rows.** One row per domain element, with the concept IRI(s) it draws on and its graph name. An element may draw on several concepts and a concept may inform several elements. Explicit exceptions go in `note`.
6. **Write the example data** (`ontology/abox/qNN.ttl`) from the verified fixtures in `tests/qN_M/fixtures.yaml`, with the anchor values and odd cases they hold. Use instance IRIs. Do not include individuals' names. Add negative cases in `abox/negative/` only for axioms that are meant to reject something, each with a comment on why it must be inconsistent.
7. **Run the reasoner and the pitfall scan.** Run ROBOT `reason` on the ontology plus the example data and report: consistent or not, unsatisfiable classes, unexpected inferences. Confirm each negative case is flagged. Run `robot report` if available. Run OOPS! on the TBox. Resolve critical pitfalls. Explain any pitfall you keep, in one line each, in `ontology-notes.md`. A tool that cannot run leaves the stage pending, not passed.
8. **Pilot the answer fields.** Fill a table in `ontology-notes.md`: each answer field in `profiles/qNN.yaml` against the ontology element(s) that can state it. Fields not expressible in the ontology are either added, or recorded as derived at query time, or not modeled with a reason.
9. **Check.** `make ontology` must pass. The script fails nonzero if: a file does not parse; an element lacks a label, definition or question trace; an element IRI is in the concept namespace or a concept IRI is used as a class or property outside the explicit exceptions; a mapping row names a concept not in `watchline.ttl` or an element not in the ontology; a mapping row's `graph_name` is not a label, relationship type or property in `profiles/qNN.yaml`; a graph element in the schema has no ontology element; a subclass axiom has no reason in the notes; ROBOT reports an inconsistency or unsatisfiable class; or any step was skipped. Then re-run `make profiles` and `make thesaurus`.
10. **Review and accept.** Check the exit criterion, log decisions in `decisions.md`, update `CLAUDE.md` (open points) and the vocabulary term-trace if concepts changed, and report results and anything left open.

## Exit criterion (per question)

- The reasoner reports no inconsistency and no unsatisfiable class, with tool versions recorded. Each negative case is flagged.
- OOPS! shows no unresolved critical pitfall. Kept pitfalls are explained.
- Every class and property traces to a question, a concept and, where stored, a graph element; every graph element in the schema has an ontology element.
- Every answer field of the question is expressible or has a recorded reason.
- Each axiom has a stated reason. No SKOS link was promoted automatically.
- Rules for Stage 6 shapes are listed.
- `make ontology`, `make profiles` and `make thesaurus` pass, with nothing skipped.

## Deliverables (updated per question)

- `ontology/watchline-onto.ttl`
- `ontology/abox/qNN.ttl` and `ontology/abox/negative/`
- `ontology/concept-mapping.csv`
- `ontology/ontology-notes.md`
- `scripts/check_ontology.py` (first question)
- New entries in `decisions.md`

## After all questions

Consolidate: run the full reasoner and OOPS! pass over the whole ontology, check that each concept maps consistently, reconcile duplicate elements, and re-run all checks, as in the roadmap's order of work. Report the reasoner and pitfall results for the complete ontology.
