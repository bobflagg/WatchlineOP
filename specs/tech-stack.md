# Tech stack

The graph is a Neo4j knowledge graph queried with Cypher. The pipeline follows Jessica Talisman's *Ontology Pipeline* (see `roadmap.md`), adapted to this stack: Cypher instead of SPARQL, and SHACL shapes compiled to Cypher by shacl2cypher instead of load-time SHACL validation. n10s (Neosemantics) is not used.

See [external references and data dependencies](dependencies.md) for the PESP guide and BOR interface; no personal filesystem layout is assumed.

## Data sources

| Source or service | Intended contribution |
| --- | --- |
| NYC Geosupport, accessed through Docker | On-demand address resolution and its native outcome evidence |
| PLUTO | Tax-lot characteristics, classification, source-reported year built, residential units, and assessed value |
| HPD registrations | Recorded address/building/parcel associations and registration evidence |
| HPD registration contacts | Disclosed parties and business roles |
| ACRIS master, parties, and legals | Deeds, recorded transactions, financing documents, parties, and parcel associations |
| NY DOS active-entity data | Entity identifiers, filing information, process contacts, and available registered-agent information |
| HPD violations, complaints/problems, and litigation | Recorded enforcement and building-level condition-related evidence |
| BOR/NLR releases | Derived memberships, identity/deed signals, evidence paths, masking, exclusions, and method evaluation |
| Retrieved business filings, free public registries, reporting, and business web pages | Additional sourced records, extracted values, reported claims, and investigative leads |

The frozen local JustFix/WoW PostgreSQL snapshot is the ingestion source and sole expected-answer authority for database-backed graph tests. Live public records do not override its values. BOR/NLR releases and cached retrieval/service evidence remain separate, versioned inputs for the questions that require them. Pin their manifests/checksums and preserve their differing coverage dates. See [the expected-answer policy](roadmap.md#expected-answer-policy).

Identifiers: **BBL** is the NYC tax lot identifier and **BIN** is the NYC building identifier.

## Tools by stage

| Stage | Tools |
|---|---|
| 1. Controlled vocabulary | CLaRO-style question cleanup; CQbyCQ; Barrasa ontology-builder skill; Intentional Arrangement SKOS (editor and `validate_skos`) |
| 2. Metadata schema | YAML profiles; the editor's Sources tab (Dublin Core, FOAF, PROV-O) for concept-level provenance |
| 3. Taxonomy | Intentional Arrangement SKOS editor (orphan and cycle checks, collections, top concepts); CSV/XLSX import for a spreadsheet start |
| 4. Thesaurus | Intentional Arrangement SKOS (related links, SKOS-XL, ISO 25964 relation mode, Crosswalk tab with SSSOM export, Markdown validation report) |
| 5. Ontology | Protégé or ROBOT; OOPS! |
| 6. Knowledge graph | Neo4j, shacl2cypher |

## SKOS MCP server (stages 1 to 4)

The [Intentional Arrangement SKOS](https://github.com/jesstalisman-ia/intentional-arrangement-skos) MCP server (`mcp-server/skos_mcp.py`) is registered in Claude Code as `skos`. It provides `validate_skos`, `convert_skos`, `skos_profile` and `parse_skos_vocabulary`.

- Run `validate_skos` on the vocabulary after each question's terms are added, before the change is accepted. Apply [the taxonomy review policy](roadmap.md#taxonomy-review-policy): review tool warnings in context, document justified exceptions, and do not treat fixed depth, sibling exclusivity, or zero isolated concepts as acceptance requirements.
- Turtle is the committed format in `vocabulary/`. `convert_skos` produces other serializations when needed.
- The browser editor and the MCP server work on the same files. The editor is for hand edits; the server is for validation and conversion inside Claude Code.
- Not yet tested against this project's vocabulary. Try a small file first.

## Vocabulary and ontology identifiers

Follow [the SKOS-to-ontology mapping policy](roadmap.md#skos-to-ontology-mapping): separate concept and ontology namespaces, distinct class/property IRIs, and an explicit concept-to-element mapping table stored alongside the ontology. Controlled values can retain their SKOS IRIs when explicitly mapped. Approved labels may be reused without making a concept and a class/property the same resource. Record namespace bases in the artifact documentation; instance identifiers are separate from both.

## Adaptations to the pipeline

- **SPARQL becomes Cypher.** The stage 6 graph query language and graph acceptance test queries are Cypher. Retrieval/extraction and investigation acceptance use separate fixture-based tests, as defined in `roadmap.md`; they are not replaced by Cypher queries.
- **R2RML becomes profiles and loaders.** The graph schema per question is `profiles/qNN.yaml`; loader scripts in `scripts/` do the joins and transformations, as in [the physical implementation contract](physical-implementation.md). There are no separate mapping files.
- **SHACL compatibility.** Pin the compiler version and verify its supported constructs with a small compatibility fixture. Compile strictly. Required constraints must be executed, guaranteed by the installed schema, or covered by named supplemental checks; unsupported or skipped rules cannot silently disappear. Semantic-to-physical differences use a documented derived profile.
- **Native Neo4j schema is explicit.** Identity uniqueness constraints, indexes, and loader integrity checks are required independently of shacl2cypher. The loaders create their constraints. Graph Type remains optional and is not a POC prerequisite.
- **Derived layers are imported, not computed.** Operational Networks and Owner Portfolios come from BOR/NLR releases and are modelled with run, snapshot and method version.

## Physical implementation

Follow [physical-implementation.md](physical-implementation.md) for mapping content, Q1 scalar encodings and provenance, native schema, rebuild behavior, environment pins, and complete validation. The contract requires bounded citywide verification and source-value reconciliation in addition to shape conformance.

## Repository layout

`vocabulary/` (SKOS), `profiles/`, `ontology/`, `shapes/`, `tests/` (per-sub-question checks, negative cases, results), `scripts/`, `data/`, `specs/`.

## Open decisions

- Graph Type: optional future evaluation; native constraints and validation do not depend on adopting it.
- Whether to model the vocabulary in a separate SKOS file per scheme or one file.
