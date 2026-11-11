# Stage 5 procedure: ontology, per question

Run this for each competency question after its [stage 4](stage4-procedure.md) is accepted, one question at a time. Stage definition and exit criterion: [roadmap.md](roadmap.md#stages) (Stage 5 row, exit criterion 5) and the [SKOS-to-ontology mapping policy](roadmap.md#skos-to-ontology-mapping). Tools: [tech-stack.md](tech-stack.md).

To run it in a fresh Claude Code session, start with: "Execute specs/stage5-procedure.md for QNN."

**Goal:** turn the question's approved vocabulary into an OWL 2 ontology fragment that can state what the question's answer must say, test it with example data, and trace every element to a concept and a question. Add only what the question needs.

## Ground rules

- Check first that the question's stages 1 to 4 are accepted in `specs/decisions.md` and that `make profiles`, `make taxonomy` and `make thesaurus` pass. If not, stop and say so.
- Read: `CLAUDE.md` (auto-loaded), the question file, `vocabulary/watchline.ttl`, `vocabulary/taxonomy-notes.md`, `vocabulary/thesaurus-notes.md`, this question's `profiles/` files, `specs/physical-implementation.md` (sections 2 and 3), `specs/decisions.md`, and the existing `ontology/` files.
- Three namespaces stay separate: concepts (`https://watchline.example/vocab/`), ontology elements (`https://watchline.example/onto/`), instances (`https://watchline.example/id/`). Never use a concept IRI as a class or property IRI, except a controlled value that the mapping table explicitly records.
- No automatic promotion. A `skos:broader` link is not a subclass axiom, a `skos:related` link is not an object property, and a concept does not become a class by existing. Disjointness is declared only where the definitions support it (start from the candidates in `taxonomy-notes.md`).
- Reuse before minting. Reuse an element from the ontology when its meaning fits, and reuse PROV-O for provenance.
- Preserve the specs' distinctions in the model: recorded, derived and reported are kept apart; roles (registrant, grantee, process contact, managing agent) are not collapsed; lot-wide values are not attached to buildings; Operational Network and Owner Portfolio memberships are scoped to a source snapshot and run; no universal one-building-per-lot rule.
- An OWL class does not require instances in the physical graph. Do not decide physical labels or relationship types here; those are Stage 6.
- Do not commit to Git unless asked. Stop and ask when a decision is unsettled.

## One-time setup (first question only)

Confirm with the user (recommended defaults apply if they say "go"), then log in [decisions.md](decisions.md):

- **Layout:** `ontology/watchline-onto.ttl` (TBox and CBox), `ontology/abox/qNN.ttl` (example data), `ontology/abox/negative/` (cases that must be rejected), `ontology/concept-mapping.csv`, `ontology/ontology-notes.md`. Turtle is the committed format.
- **Naming:** classes UpperCamelCase, properties lowerCamelCase, stable once minted. Every element gets `rdfs:label` (from the approved preferred label), an `rdfs:comment` definition specific to its formal role, and a question trace.
- **Mapping table columns:** `concept_iri`, `element_iri`, `element_kind` (class, object_property, datatype_property, annotation_property, controlled_value, individual), `questions`, `note` (an explicit exception goes here). Unused concepts need no row.
- **External terms:** reuse PROV-O IRIs without `owl:imports`, declaring locally only the terms used. Record the choice.
- **Toolchain:** check `java -version` and `robot --version`. If ROBOT is missing, ask the user before installing it. Choose and pin the reasoner (ELK or HermiT) and record the versions actually used. Protégé is optional for hand editing.
- **Pitfall scan:** OOPS! is a web service. Submit the TBox file only, never the example data, and only with the user's go-ahead. If the user prefers, they run it and paste the result.
- **Versioning:** POC rules apply. Set an ontology IRI, no version IRI.
- **Check script:** add `scripts/check_ontology.py` (`rdflib`) and implement `make ontology` (see step 9).

## Per-question steps

1. **List what the question requires.** From its answer shape, profiles and caveats, list the things it talks about (candidate classes), relations between them, attributes with datatypes, value sets, and rules about what may be asserted.
2. **Decide each element's kind.** For each item choose: class, object property, datatype property, controlled value (a SKOS concept used directly, as the address resolution outcomes are), annotation, or not modeled (a presentation choice or a query-time computation). Write the reason for anything not modeled.
3. **Draft the elements.** Mint IRIs in the ontology namespace. Give each a label, a role-specific definition and a question trace. Use PROV-O for source records, snapshots and runs where it fits, and carry the evidence fields from `profiles/evidence.yaml`. Keep the assertion type (recorded, derived, reported) and review status as explicit, queryable parts of the model.
4. **Add axioms sparingly.** Subclass axioms only where the is-a test holds on the formal meaning. Domain and range only where every use satisfies them (they cause inferences). Disjointness and cardinality only where the definitions support them. For each axiom write a one-line reason in `ontology-notes.md`. Rules OWL cannot express (required properties, closed-world checks, counting-unit rules) are not forced into axioms. List them in `ontology-notes.md` under **Rules for Stage 6 shapes**.
5. **Write the mapping rows.** One row per domain element, with the concept IRI(s) it draws on. An element may draw on several concepts and a concept may inform several elements. Explicit exceptions (for example a controlled value that keeps its concept IRI) go in `note`.
6. **Write the example data** (`ontology/abox/qNN.ttl`). Use the question's anchor properties with the values from its worked examples, labelled provisional until verified against the frozen snapshot. Use instance IRIs. Do not include individuals' names. Add negative cases in `abox/negative/` only for axioms that are meant to reject something, each with a comment on why it must be inconsistent.
7. **Run the reasoner and the pitfall scan.** Run ROBOT `reason` on the ontology plus the example data and report: consistent or not, unsatisfiable classes, unexpected inferences. Confirm each negative case is flagged. Run `robot report` if available. Run OOPS! on the TBox. Resolve critical pitfalls. Explain any pitfall you keep, in one line each, in `ontology-notes.md`. A tool that cannot run leaves the stage pending, not passed.
8. **Pilot the answer shape.** Fill a table in `ontology-notes.md`: each answer field in `profiles/qNN-answer.yaml` against the ontology element(s) that can state it. Fields not expressible in the ontology are either added, or recorded as derived at query time, pending (matching the profile), or not modeled with a reason.
9. **Check.** `make ontology` must pass. The script fails nonzero if: a file does not parse; an element lacks a label, definition or question trace; an element IRI is in the concept namespace or a concept IRI is used as a class or property outside the explicit exceptions; a mapping row names a concept not in `watchline.ttl` or an element not in the ontology; a subclass axiom has no reason in the notes; ROBOT reports an inconsistency or unsatisfiable class; or any step was skipped. Then re-run `make profiles`, `make taxonomy` and `make thesaurus`.
10. **Review and accept.** Check the exit criterion below, log decisions in `decisions.md`, update `CLAUDE.md` (open points) and the vocabulary term-trace if concepts changed, and report results and anything left open.

## Exit criterion (per question)

- The reasoner reports no inconsistency and no unsatisfiable class, with tool versions recorded. Each negative case is flagged.
- OOPS! shows no unresolved critical pitfall. Kept pitfalls are explained.
- Every class and property traces to a question.
- The mapping table records the vocabulary basis for every domain element and identifies each explicit exception.
- Every answer field of the question is expressible or has a recorded reason.
- Each axiom has a stated reason. No SKOS link was promoted automatically.
- Rules for Stage 6 shapes are listed.
- `make ontology`, `make profiles`, `make taxonomy` and `make thesaurus` pass, with nothing skipped.

## Deliverables (updated per question)

- `ontology/watchline-onto.ttl`
- `ontology/abox/qNN.ttl` and `ontology/abox/negative/`
- `ontology/concept-mapping.csv`
- `ontology/ontology-notes.md`
- `scripts/check_ontology.py` (first question)
- New entries in `decisions.md`

## Carry-over from Q1

- Candidate elements, to confirm against the question rather than assume: tax lot, building, street address, address resolution and its outcome, address candidate, HPD registration, the four source-reported characteristics, reported counts with counting units, source snapshot, source record. The addressed building is a role in one answer (see `taxonomy-notes.md`), not a subclass of building.
- Identifiers `bbl` and `bin` are concepts about identifiers. Decide whether each becomes a datatype property of its subject. The identifier format is in `profiles/pluto.yaml` and `profiles/hpd_registrations.yaml`.
- The outcome values stay SKOS concepts used as controlled values, with explicit mapping rows.
- Lot-wide characteristics (units, year built, class, assessed value) belong to the lot, not the building.
- Fields still `pending` in `profiles/q01-answer.yaml` stay pending in the pilot table.

## After all questions

Consolidate: run the full reasoner and OOPS! pass over the whole ontology, check that each concept maps consistently, reconcile duplicate elements, and re-run all checks, as in the roadmap's order of work. Report the reasoner and pitfall results for the complete ontology.
