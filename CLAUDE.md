# WatchlineOP

An ontology pipeline that produces a Neo4j knowledge graph. An AI agent, with a human in the loop, uses it to help NYC tenants, organizers and housing researchers investigate a landlord from a street address, following the PESP guide *How to Research Your Landlord* (May 2026). The output is a reproducible, source-cited dossier.

## Specs (the only sources of truth)

Accepted decisions in `specs/decisions.md` override anything else. Source inventory and the frozen baseline are in `data/sources.yaml` and `data/README.md`.

- `specs/mission.md`: the mission: the ontology pipeline and how we work.
- `specs/use-case.md`: the PESP landlord accountability use case: users, research workflow, distinctions to preserve, evidence rules, dossier and stopping rules.
- `specs/roadmap.md`: the pipeline stages, exit criteria, acceptance types, expected-answer policy, order of work and open decisions.
- `specs/stage1-procedure.md`: the per-question procedure for stage 1 (CLaRO-style cleanup, then vocabulary).
- `specs/tech-stack.md`: data sources and ingestion, tools by stage, the SKOS MCP server, adaptations to the pipeline, planned layout.
- `specs/physical-implementation.md`: mappings, Neo4j schema, validation, access rules, rebuild and environment.
- `specs/dependencies.md`: external references (PESP guide, BOR releases).
- `specs/decisions.md`: dated log of accepted decisions.
- `specs/competency-questions.md`: the 28 competency questions, their vocabulary, and how examples were chosen.
- `specs/questions/qNN.md`: one file per question. Each has a real example on a neutral building, the answer shape, who asks and why, and the sources needed.

The questions drive the ontology and become the evaluation dataset. Read the relevant question file before working on a term, class or test. Some questions are split into sub-questions (`Qn.1`, `Qn.2`); the parent passes when all parts pass.

## Running the pipeline

Use `make help`. Steps are Make targets, and unbuilt steps fail on purpose ("not implemented"). Destructive resets need `CONFIRM=<database name>` and only ever target the POC graph.

## Database and graph access

- MCP servers (`postgres-justfix`, `neo4j-watchline`) are for exploration and spot checks only. The Neo4j MCP is read-only. Nothing committed comes from a chat session.
- Loads, tests and expected-answer SQL are scripts using `.env` credentials. The source database is read-only everywhere. Only scripts write to the POC graph.
- Expected answers come from SQL against the frozen database, independent of the graph. See `specs/physical-implementation.md`, section 6.
- Never print or commit credentials. `.env` and `.mcp.json` are git-ignored.

## Tooling: SKOS MCP server

The controlled vocabulary is managed with [Intentional Arrangement SKOS](https://github.com/jesstalisman-ia/intentional-arrangement-skos). Its MCP server is registered in Claude Code as `skos` (see `specs/tech-stack.md`).

- Tools: `validate_skos`, `convert_skos`, `skos_profile`, `parse_skos_vocabulary`.
- Use `validate_skos` after every change to a file in `vocabulary/`, and report its findings before moving on.
- Turtle is the committed format. Use `convert_skos` for other serializations; do not commit converted copies.
- If the `skos` tools are not listed, say so. Do not validate by hand or claim a vocabulary is valid without running the tool.
- The server is third-party code. Do not modify it, and do not send anything other than vocabulary files to it.

## Users and entry points

- Primary user: a tenant or organizer who knows a building's street address. Researchers and journalists use the same evidence paths to inspect or challenge an answer.
- Entry points: an address (principal), an official property identifier, an organization name, or a person named in a recorded business role.
- Ambiguous matches return distinguishable candidates. Never silently select one.

## Research workflow

1. Identify the property: address to tax lot and buildings; separate the addressed building from others on the lot; report match uncertainty.
2. Identify recorded parties: registered owner, deed grantee, managing agent, other roles. Do not collapse distinct roles into one owner.
3. Investigate the entity: business registry records, addresses, filing attachments; follow entities into other jurisdictions when free public records exist.
4. Explore related properties: Operational Networks and Owner Portfolios, their evidence and methods, compared with the managing agent's footprint.
5. Examine transactions and conditions: transfers, financing, registrations, violations, building-level complaint summaries, HPD litigation, with dates and attribution limits.
6. Follow qualified leads within an explicit budget; log findings, exclusions, conflicts and dead ends.
7. Produce a dossier with findings, evidence paths, unresolved leads and an explicit stop reason.

Web discovery can recur at any step. The workflow is iterative.

## Distinctions the model must preserve

| Concept | Limit on interpretation |
| --- | --- |
| Tax lot (identifier: **BBL**) | A lot is not necessarily one building |
| Building (identifier: **BIN**) | Building counts and parcel counts differ |
| Title / registration facts | An HPD registrant, deed grantee, process contact and managing agent are not interchangeable |
| Management relationship (`MANAGED_BY`) | Shared management does not establish shared ownership. Not a grouping, not a rung in an ownership hierarchy |
| Operational Network | Derived grouping through registration infrastructure and resolved identities, with aggregator-address masking. Connected components; components over 300 lots are cut into communities by Louvain. Not a finding of common ownership |
| Owner Portfolio | Derived attribution to one apparent owner from resolved shared identity or a qualifying shared deed; co-op and condo buildings excluded. Not a legal determination of beneficial ownership |
| Aggregator / mail-drop address | Co-location alone must not support ownership or identity. Method-specific masking and curated classifications stay distinct |
| Corporate affiliation | Preserve the specific relationship (ownership, parent, management, financing, other) and its evidentiary basis |

- Operational Network and Owner Portfolio come from BOR/NLR releases. Eligibility rules, exclusions, component/community distinctions and method versions belong to the release evidence. Group identifiers and memberships are valid only within their snapshot and pipeline run.
- A BOR display name or "person anchor" is a presentation choice, not an assertion that the person owns the group.
- Both groupings are leads to verify in every answer.

## Evidence rules

- **Type I, recorded assertion:** a source states it, or records join on an official identifier. Describes how it was obtained, not that it is correct.
- **Type II, derived conclusion or lead:** a method resolves, groups, classifies or infers beyond what a source states.
- **Reported claim:** a publication states something. The publication is recorded evidence. The claim's truth and applicability need separate assessment.
- Reliability per question: **I**, **II**, or **I+II** (a recorded chain with derived links).
- Track source category separately: `public_record`, `published_reporting`, `web_content`, `project_derived`.
- Web and document findings are session/dossier evidence by default. Promoting them into the graph needs a separately governed process. Cached retrieval must support replay and evaluation.

## Sources

| Source | Contribution |
| --- | --- |
| NYC Geosupport (Docker) | On-demand address resolution and its outcome evidence |
| PLUTO | Lot characteristics, classification, source-reported year built, residential units, assessed value |
| HPD registrations | Address/building/parcel associations |
| HPD registration contacts | Disclosed parties and business roles |
| ACRIS master, parties, legals | Deeds, transactions, financing documents, parties, parcel associations |
| NY DOS active entities | Entity ids, filings, process contacts, registered agents |
| HPD violations, complaints/problems, litigation | Enforcement and condition-related evidence |
| BOR/NLR releases | Memberships, identity/deed signals, evidence paths, masking, exclusions, method evaluation |
| Retrieved filings, free public registries, reporting, business web pages | Extracted values, reported claims, leads |

The local JustFix/WoW PostgreSQL snapshot is the ingestion source and the sole authority for database-backed test inputs and expected answers. Live public records and Socrata never override it. BOR/NLR releases and cached retrieval/service evidence (including Geosupport responses) are separate, separately pinned inputs. Freezing is per source as questions are started; Q1 is frozen on PLUTO 26v1 and HPD registrations as of 2026-05-29 (see `specs/decisions.md`).

## Answer and dossier requirements

A dossier contains:

1. Input, resolution outcome, identified parcels and buildings.
2. Recorded title, registration, management and business-filing facts.
3. Operational Network and Owner Portfolio results, separately explained.
4. Transaction, financing, violation, complaint and litigation summaries.
5. Retrieved claims, document extractions and affiliation leads, labeled.
6. Conflicts, source gaps, excluded evidence, unresolved leads.
7. Run and snapshot context, citations, retrieval log, explicit stop reason.

Stopping rules:
- Follow new entity names and business addresses only if they come from recorded or retrieved evidence, are not masked service-address leads, and fit the step/time budget. Log retrieved items even if unused.
- Stop when the trail reaches a service or masked address, has no further recorded link, needs payment or an inaccessible source, exhausts the budget, or leaves an unresolved conflict.
- State the stopping reason. Never imply the investigation is complete in an absolute sense.

## Working with the examples

- Examples use neutral Sunset Park, Brooklyn buildings (anchors A to G in `specs/competency-questions.md`). Do not repeat individuals' names; write "a person (name not repeated)". The agent shows names with role and source.
- Example values in the question files are provisional until verified against the frozen snapshot. The "queried 2026-11-10" checks are observations, not a baseline. Do not refresh them from live services, and report differences from newer public records as freshness limits, not test failures.
- The A and B trail (same HPD business address, a joint mortgage, DOS filings a day apart) is a record link only. Do not assert common ownership.

## Open points

- Dump identifier and checksum for the frozen snapshot are not yet recorded (`data/README.md`).
- BOR release v0.2.1 and run `2026-05-29-149e871f` are provisional; edge-level evidence is not yet exported.
- Name-normalization rules, the `mail_drop_list`, ACRIS document-type descriptions (`acris_document_codes` is unusable locally) and which HPD contact types count as "registered owner" are undefined. Settle each when the first question needing it is started.
- Q26 says anchor C is excluded from the Owner Portfolio as a co-op; Q9 and Q19 say it is in one. Resolve before Q9, Q19 or Q26.
- Q20's list of required component questions is incomplete.
- Q1 stage 2: Geosupport fields and the answer fields depending on them are `pending` until the first cached responses are recorded (`profiles/geosupport.yaml`, `profiles/q01-answer.yaml`).
- Q1 stage 3 is done. Neither scheme names a `dcterms:publisher` (an info-level `validate_skos` note). Set it when the vocabulary is first published. Later questions add their hierarchies to `vocabulary/taxonomy-notes.md`.
