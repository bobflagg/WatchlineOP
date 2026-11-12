# Roadmap

High-level plan for going from the competency questions to a validated Neo4j knowledge graph. The stage sequence follows Jessica Talisman's *Ontology Pipeline* (vocabulary, metadata schema, taxonomy, thesaurus, ontology, knowledge graph). Tools, sources and adaptations to the stack are in `tech-stack.md`.

## Principles

- **Questions drive everything.** The 28 files in `specs/questions/` are the requirements and the evaluation set. Each term, class, property and shape traces to at least one question.
- **One question at a time.** For each question: draft terms, then the ontology fragment, then the applicable acceptance fixtures/contracts and graph test queries, then a shape where applicable. Review before moving on.
- **Vocabulary first.** Terms live in SKOS. Ontology classes and properties use separate IRIs and explicitly trace to the concepts that informed them; they reuse approved terminology, not concept identifiers as class/property identifiers.
- **Derived is not recorded.** The Type I / Type II / reported-claim distinction and the source categories are modelled explicitly, not left to prose.

## Stages

| Stage | Question it answers | Method in this project | Output | Standards |
|---|---|---|---|---|
| 1. Controlled vocabulary | What do we call things? | Mine the question files, the specs and the source column names for terms. Reconcile synonyms and homonyms (owner vs registrant vs grantee). Write definitions and scope notes. Pilot: can every question be stated using only approved terms? | Approved terms with IDs, labels, definitions | SKOS, ANSI/NISO Z39.19 |
| 2. Metadata schema | Which fields describe things, and what values are allowed? | Profile each source's columns in use: type, units, allowed values, sentinels. For each question, declare every graph element and answer field with its vocabulary concept, source, type, allowed values and null policy, and check that the graph holds exactly what is declared. Define per-record evidence fields (source key, snapshot, run id, assertion type, review status) only when a question stores derived edges, claims, documents or cached responses. | Source profiles and question schema | Dublin Core, DCAT, PROV-O, ISO 8601 |
| 3. Taxonomy | How do terms nest? | Only where the questions need a hierarchy: party roles, document types, violation classes, complaint types, case types, stop reasons, absence reasons. Add broader/narrower links only where their meaning is justified. Prefer shallow hierarchies without a fixed depth. Permit multiple parents and overlapping siblings; require disjointness only when supported by the definitions. | Hierarchical concept schemes | SKOS |
| 4. Thesaurus | What relates across branches? | Add related links in both directions (for example role to document type). Map to external schemes where one exists. Review disconnected concepts, cycles, and mixed hierarchy meanings; do not invent links merely to remove a warning. | SKOS thesaurus | SKOS, SKOS-XL, ISO 25964 |
| 5. Ontology | What is true, and what follows from it? | Three boxes. CBox: governance and the rules for what may be asserted. TBox: classes and properties derived from the questions (Tax lot, Building, Party, Role, Deed, Registration, Operational Network, Owner Portfolio, Claim, Evidence). ABox: the anchor-property examples as test data. Run a reasoner and OOPS! for pitfalls. | OWL 2 ontology | OWL 2, RDF/RDFS, PROV-O |
| 6. Knowledge graph | What do we know, and can we query it? | Load instances from the local JustFix/WoW snapshot using the question's profile and loader scripts. Compile shapes with shacl2cypher (`--strict`) and run them as read-only Cypher. Per-sub-question checks scored against expected answers from SQL. Deliver fixtures/contracts for downstream retrieval and investigation acceptance separately. Monitor drift on each new snapshot. | Populated graph, SHACL shapes, graph test queries, downstream acceptance fixtures/contracts | SHACL, Cypher, loader scripts |

Stage 6 follows [the physical implementation contract](physical-implementation.md): documented profiles and loaders, native identity constraints, exact value encodings, reconciliation, and complete validation. These are POC implementation requirements, not additional release machinery.

## Exit criteria per stage

1. Domain terms used in questions resolve to approved concepts in context. Each concept has at most one preferred label per language. Preferred labels should distinguish concepts within a scheme/language; qualify ambiguous homonyms or document an intentional exception. Shared alternative labels and labels repeated across schemes are permitted when definitions and scope make their meanings clear.
2. Every field in an answer shape has a profile entry with source, type and allowed values.
3. Every broader/narrower link has a justified hierarchical meaning. Multiple parents are allowed when each link is valid; sibling concepts need not be disjoint. Prefer shallow hierarchies, adding depth only when it helps the questions or source classification. Review cycles and inconsistent meanings; do not automatically interpret SKOS hierarchy as OWL subclassing.
4. Related links are symmetric. Each concept belongs to an intended scheme; top-level or isolated concepts may remain when no defensible semantic link is needed. Review and explain disconnection warnings rather than add artificial parents or related links.
5. Reasoner reports no inconsistency or unsatisfiable class; OOPS! has no unresolved critical pitfall; every class traces to a question; the concept-to-ontology mapping table records the vocabulary basis for each domain class/property and identifies any explicit exception.
6. Every question passes its designated acceptance tests. Graph validation, retrieval/extraction accuracy, and investigation behavior are evaluated separately. For the WatchlineOP release, all applicable graph tests must pass, shapes must pass on the loaded graph and fail on seeded bad data, and downstream acceptance fixtures/contracts must be delivered. Retrieval/extraction and investigation results remain pending until the downstream consumer passes them; they are not required to claim graph readiness and must not be reported as passed solely because the graph is ready.

## Acceptance types and responsibility

Each question declares an `acceptance_types` list in its YAML front matter. Types are cumulative: when a question declares several, all are required for full question acceptance. Shared prerequisites (such as address resolution before querying a building) are tested by their own questions rather than copied onto every question.

| Value | Acceptance test | Execution responsibility |
| --- | --- | --- |
| `graph` | Run Cypher against frozen source fixtures and compare required values, counts, evidence links, and uncertainty with the expected answer. Validate the mapped graph with shapes separately. | WatchlineOP |
| `retrieval-extraction` | Replay cached pages, documents, or service responses; check returned/extracted values, citations, match outcomes, and uncertainty. | Downstream consumer; WatchlineOP supplies fixtures and contracts |
| `investigation` | Exercise the complete dossier workflow; check evidence trails, unresolved leads, step/time budgets, and stopping reasons. | Downstream research agent; WatchlineOP supplies fixtures and contracts |

Q1 combines graph tests with replayed address-resolution service tests. Q5 combines registry-snapshot graph tests with filing retrieval tests. Q16 and Q25 require retrieval/extraction tests. Q20 combines component graph and retrieval tests with an investigation scenario; it is not a single Cypher query.

Track results per question and acceptance type as `pending`, `passed`, or `failed`, with the fixture version and test evidence. A missing fixture remains pending. Full question acceptance requires every declared type to pass. For example, graph acceptance can pass for Q1 while service acceptance remains pending; completion of the graph alone never completes Q20.

## Expected-answer policy

- **Database-backed graph tests:** use only the chosen frozen JustFix/WoW PostgreSQL snapshot for both source inputs and expected answers. Derive and review expectations from that source evidence, not solely from the graph or ETL being tested. Live public data is not a test oracle and must not override the frozen values.
- **Derived-layer tests:** use the separately pinned BOR/NLR release, including its manifest, checksums, source context, and run. Preserve any differences between that release's source vintage and the database snapshot; do not assume they describe the same time.
- **Retrieval/extraction and investigation tests:** use versioned caches of documents, pages, and service responses, including Geosupport responses. Record retrieval time and service/dataset version where available. Acceptance runs replay the cache rather than re-fetching live expected values.
- **Fixture records:** identify the question, fixture version, evidence identifiers/checksums, query parameters, relevant dates, expected values and caveats, and verification status. Worked examples and local checks are provisional until verified against the selected frozen evidence. Missing evidence leaves the affected test pending.
- **Refreshes:** a new snapshot, BOR release, or cache version creates a new fixture version. Retain the previous baseline. Differences from newer public records are reported as freshness or coverage limits, not failures of the older snapshot-backed tests.

This is an evaluation policy, not a claim that the snapshot is complete, current, or correct about the world. No new live-data ingestion is required by it.

## Taxonomy review policy

For a generic kind-of hierarchy, use the is-a test. If a source scheme instead organizes concepts by a documented part-whole or other hierarchical relation, state that meaning explicitly; do not mix relation meanings without explanation. Not every source code list needs a hierarchy. Severity order or workflow sequence alone does not establish a broader/narrower relationship.

Multiple parents and overlapping categories are permitted. Disjointness is a separate, justified ontology decision, not a default consequence of sibling placement. Validator warnings prompt review; they do not require adding unsupported structure. Keep a one-line explanation with any intentional exception.

## SKOS-to-ontology mapping

Use separate namespaces for vocabulary concepts, ontology elements, and instance data. The concrete namespace bases must be recorded when the first artifacts are created; this policy does not rename existing identifiers automatically.

- **Concepts:** SKOS IRIs identify controlled meanings and retain their approved labels, definitions, and scope notes.
- **Classes and properties:** mint distinct ontology IRIs when a question requires a class, object property, or datatype property. Reuse approved terminology where its meaning fits, with a definition specific to the element's formal role.
- **Controlled values:** a SKOS concept may be used directly as a controlled value where the ontology and physical mapping explicitly specify that representation. It does not need a duplicate OWL class merely to appear in the graph.
- **Traceability:** keep a compact mapping table with the concept IRI(s), ontology element IRI, element kind, and relevant question IDs alongside the ontology. One concept may inform several elements, and an element may draw on several concepts. Unused concepts need not generate ontology elements.
- **No automatic semantic promotion:** concept-to-element links document design traceability, not identity or logical equivalence. Do not automatically translate broader/narrower links into subclass axioms or related links into object properties.

During the POC, the mapping table is sufficient; a mapping registry or conversion framework is not required. Review it with each ontology fragment. The physical Neo4j mapping separately identifies labels, relationship types, properties, and any encoding of controlled-value IRIs.

## Lightweight POC iteration

During the POC, accepted model changes trigger a graph rebuild and rerun of existing tests. Formal artifact versioning, migrations, dependency registries, and release governance are deferred until a viable POC exists. Rebuild only the designated POC graph; the source snapshot remains unchanged.

- Keep Q1–Q28 and concept IRIs stable. A label change does not change the identifier; do not reuse an identifier for a different meaning.
- Track specs, vocabularies, profiles, ontology, shapes, tests, and scripts in Git. Exclude credentials, raw datasets, and generated graph data. Small test fixtures may be committed.
- Record accepted modeling choices in [decisions.md](decisions.md), using a date, decision, and short rationale.
- Identify the fixed source dump and restoration details in [data/README.md](../data/README.md). The expected-answer policy still applies; Git revisions and a short fixture note suffice for POC fixture identification. No automated release machinery is required.

## Order of work

1. Pick the first question and run stages 1 to 6 in miniature for it (thin vertical slice), proving the toolchain end to end.
2. Add questions in dependency order; each adds terms, then an ontology fragment, applicable acceptance fixtures/contracts, and graph checks and shapes where needed.
3. After all 28: consolidate the taxonomy and thesaurus, run the full reasoner and pitfall pass, and run the graph evaluation. Deliver the complete downstream acceptance suite; report downstream execution results separately.
