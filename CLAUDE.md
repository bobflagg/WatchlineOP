# WatchlineOP

An ontology pipeline that produces a Neo4j knowledge graph. An AI agent, with a human in the loop, uses it to help NYC tenants, organizers and housing researchers investigate a landlord from a street address, following the PESP guide *How to Research Your Landlord* (May 2026). The output is a reproducible, source-cited dossier.

## Specs (the only sources of truth)

Accepted decisions in `specs/decisions.md` override anything else. Source inventory and the frozen baseline are in `data/sources.yaml` and `data/README.md`.

- `specs/mission.md`: the mission: the ontology pipeline and how we work.
- `specs/use-case.md`: the PESP landlord accountability use case: users, research workflow, distinctions to preserve, evidence rules, dossier and stopping rules.
- `specs/roadmap.md`: the pipeline stages, exit criteria, acceptance types, expected-answer policy, order of work and open decisions.
- `specs/stage1-procedure.md`: the per-question procedure for stage 1 (CLaRO-style cleanup, then vocabulary).
- `specs/tech-stack.md`: data sources and ingestion, tools by stage, the SKOS MCP server, adaptations to the pipeline, planned layout.
- `specs/physical-implementation.md`: where mappings live (profiles, loaders), Q1 encodings, validation, access rules, rebuild and environment.
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
- Use `validate_skos` after every change to a file in `vocabulary/`, and report its findings before moving on. From the command line, `make vocab` runs the same validator (set `SKOS_REPO` if the clone is not at `~/git-alt/intentional-arrangement-skos`).
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

- Frozen baseline recorded 2026-11-16 (`data/README.md`): `justfixwow-poc-baseline_2026-11-16.sql.gz`, SHA-256 `9124f6c0d0f0d2e453f1971247ed29c217d3d4b5f55338d95344e04a617b6278` (plain-SQL dump of the 11 `public` source tables). Fixture headers and `tests/results/*.yaml` still say "provisional" until updated. Q1 was restarted on 2026-11-11 with a minimal graph (`Lot`, `Building`, `HAS_BUILDING`); Q1.1 to Q1.4 pass `make test`. Re-run `make test` and re-verify the fixtures once the dump is recorded.
- BOR release v0.3.0 and run `2026-05-29-869bd299` are provisional; edge-level evidence is not yet exported.
- The `mail_drop_list` is undefined (Q3 carries the mail-drop caveat in the vocabulary only). `acris_document_codes` is unusable locally; the descriptions of the eight deed codes are recorded in `data/sources.yaml`, other codes are undefined until a question needs them. HPD contact types for "registered owner" were settled for Q2 and name normalization for Q3 (2026-11-12).
- Q1 restart: the old Q1 stage 1-6 artifacts were archived to `ignore-this-directory/old-q1-artifacts-2026-11-11.tar.gz` and deleted. All six stage procedures (`specs/stage1-procedure.md` to `stage6-procedure.md`) are rewritten for the minimal model and were run for Q1. Q1 acceptance is pending only on the frozen dump identity (`data/README.md`). To start the next question, run one stage at a time: "Execute specs/stage1-procedure.md for Q2", then stage 2, and so on.
- Q1 stage 1 is complete: `validate_skos` reports 0 violations and 0 warnings (21 concepts, 100% documented). Two info notes remain: neither scheme names a `dcterms:publisher`. Set it when the vocabulary is first published.
- Q1 stage 2 is complete: `make profiles` passes 78/78 (source profiles for PLUTO, HPD registrations and Geosupport; `profiles/q01.yaml`). Per-record evidence fields are not defined yet; add them when a question first stores derived edges, claims, documents or cached responses.
- Q1 stage 3 is complete: no hierarchy needed (see `vocabulary/taxonomy-notes.md`). Add `scripts/check_taxonomy.py` and implement `make taxonomy` when the first question has a link or collection to check.
- Q1 stage 4 is complete: 8 related pairs and the label review are written (`vocabulary/thesaurus-notes.md`); `make thesaurus` passes 11/11. `validate_skos` (via `skoslib.validate_rdf`, 2026-11-12): 0 violations, 0 warnings; the only SHACL notes are the optional `dcterms:publisher` info items. Stage 4 is complete for Q1. No external mappings sought.
- Q1 stage 5 is complete: `make ontology` passes 28/28; the OOPS! rescan (`make oops`) shows only P13 (minor, accepted: no inverse for `hasBuilding`). Stage 6 procedure is rewritten for the minimal model (`specs/stage6-procedure.md`); next is running it for Q1.
- Q1 stage 6: shapes written and passing (`make shapes` 46/46). Results in `tests/results/q01-2026-11-12.yaml`: graph, retrieval/extraction and investigation acceptance all `pending` until the frozen dump is identified in `data/README.md` (and, for the last two, until the downstream consumer runs them).
- Q2 stages 1 and 2 are complete: `make test` passes Q2.1 (22) and Q2.2 (26) alongside Q1; `make profiles` passes 136/136 over Q1 and Q2 (`profiles/q02.yaml`, `profiles/hpd_contacts.yaml`). Registered owner = the contact types `CorporateOwner`, `IndividualOwner`, `JointOwner` (decision 2026-11-12). `registrationcontactid` is not unique in the snapshot. Q2 stage 3 is complete: no hierarchy needed (`vocabulary/taxonomy-notes.md`). Q2 stage 4 is complete: 3 related pairs, label review, no external mappings; `make thesaurus` passes 11/11. Q2 stage 5 is complete: `make ontology` passes 41/41; `make oops` shows only P13 (minor, accepted: now 3 properties lack inverses). Q2 stage 6 is complete: after a full rebuild, `make graph` passes (shapes 78/78 over Q1 and Q2), `make ontology` 41/41, `make thesaurus` 11/11; results in `tests/results/q02-2026-11-12.yaml`. Stage 6 found `registrationid` 0 is a placeholder on 3 unrelated buildings; it is excluded and counted. Q2 acceptance is pending on the frozen dump identity.
- Q3 stage 1 is complete (graph tests pass): loaders (`scripts/load_deeds.py`, address columns in `scripts/load_registrations.py`), tests `tests/q3_1` to `q3_5`, comparison code `src/watchline/compare.py`, vocabulary (56 concepts, `make vocab` clean). Q3 stage 2 is complete: `make profiles` passes 227/227 (`profiles/q03.yaml`, ACRIS source profiles). Q3 stage 3 is complete: no hierarchy needed (`vocabulary/taxonomy-notes.md`). Q3 stage 4 is complete: 12 related pairs, label review, no external mappings; `make thesaurus` passes 11/11. Q3 stage 5 is complete: `make ontology` passes 58/58 (2 classes, 2 object and 9 datatype properties; agreements not modeled); `make oops` shows only P13 (minor, accepted: 5 properties lack inverses). Q3 stage 6 is complete: after a full rebuild, `make graph` passes (shapes 131/131 over Q1 to Q3), `make ontology` and `make thesaurus` pass; results in `tests/results/q03-2026-11-12.yaml`. Q3 acceptance is pending on the frozen dump identity. Q22 treats a spacing difference as a normalization match while Q3 keeps it a difference; reconcile before Q22.
- Contact merge (2026-11-15): `OwnerContact` and `RoleContact` are one `Contact` node (`HAS_CONTACT`, all nine HPD types, `corporationName` and `personName`, no `name`); statements below that name the old classes are history. The graph needs a rebuild and reload before `make profiles shapes test` pass again.
- Landlord to Contact (2026-11-15): `BASED_ON_CONTACT` links each landlord record to the HPD contacts of its selected observations (`scripts/load_landlord_contacts.py`, `tests/q8_3/check_contacts.py`); a record link, not a finding of ownership.
- Q4 stages 1 and 2 are complete: `make profiles` passes 266/266 (`profiles/q04.yaml`; `RoleContact`, `HAS_ROLE_CONTACT`; `title` added to `profiles/hpd_contacts.yaml`). Q4 stage 3 is complete: no hierarchy needed (`vocabulary/taxonomy-notes.md`). Q4 stage 4 is complete: 4 related pairs, label review, no external mappings; `make thesaurus` 11/11, `make vocab` clean. Q4 stage 5 is written: `make ontology` passes 66/66 (adds `RoleContact`, `hasRoleContact`, `contactTitle`, `corporationName`, `personName`; negative cases n11, n12); `make oops` shows only P13 (minor, accepted: 6 properties lack inverses). Stage 5 is complete for Q4. Q4 stage 6 is complete: after a full rebuild, `make graph` passes (shapes 166/166 over Q1 to Q4), `make ontology` and `make thesaurus` pass; results in `tests/results/q04-2026-11-12.yaml`. Q4 acceptance is pending on the frozen dump identity.
- Q5 stage 1 is written, not yet run against the graph: `DosEntity`, `scripts/load_dos.py` (in `make load`), tests `tests/q5_1` to `q5_3`, vocabulary 77 concepts (`make vocab` clean). New name rule N3 (N2 plus apostrophes) for DOS matching; reconcile with Q22. Q5.4 (retrieval) is later. The user runs `make load` and `make test`.
- Q5 stage 2 is complete: `make profiles` passes 346/346 (`profiles/nys_corporations.yaml`, `profiles/q05.yaml`). The graph holds 119,999 `DosEntity` records (scope includes Grantee names), not the 55,694 in the Q5 findings; correct the finding in stage 6 or `q05.md`. Q5 stage 3 is complete: no hierarchy needed (`vocabulary/taxonomy-notes.md`); `make vocab` clean. Q5 stage 4 is complete: 10 related pairs, label review, no external mappings; `make thesaurus` 11/11, `make vocab` clean, `make profiles` 346/346. Q5 stage 5 is written: `make ontology` passes 88/88 (adds `DosEntity`, 17 datatype properties, negative cases n13 to n15); `make oops` not yet run (expect P13 and P32 for the repeated address-part labels). Stage 5 closes for Q5 once `make oops` is run and recorded; on 2026-11-13 oops.linkeddata.es was unreachable, so the scan is pending (retry later).
- Q5 stage 6 is written: `shapes/q05.ttl`, three supplemental checks (0 violations on the 119,999 `DosEntity` records, read-only), 30 negative cases, results in `tests/results/q05-2026-11-13.yaml`. The user runs the rebuild, `make graph`, `make ontology` and `make thesaurus` and records the counts. Q5.4 needs a replayable cache of state filings (user's machine). Q5 acceptance is pending on the frozen dump identity.
- Resolved 2026-11-19: anchor C is in Owner Portfolio `OP-98617` (release v0.3.0), as Q9 and Q19 say. The Q26 co-op example now uses 20 River Terrace (`1000160180`, `coop_condo_dominated`, in network `ON-1710`).
- Q20's list of required component questions is incomplete.


# IMPORTANT!!

Make your responses concise.  Don't throw a wall of text at me!!
- Q8 (Operational Network, BOR release v0.3.0): stage 1 complete (`tests/q8_1` to `q8_4` pass; `scripts/load_networks.py` in `make load`; vocabulary 109 concepts, `make vocab` clean); stage 2 complete (`make profiles` passes; `profiles/q08.yaml`, `profiles/bor_layers.yaml`); stage 3 complete (absence-reason hierarchy; `make taxonomy` 49/49); stage 4 complete (`make thesaurus` 11/11). stage 5 written (`make ontology` 107/107; OOPS! pending: `make oops`). stage 6 written (`shapes/q08.ttl`, three checks, 26 negative cases; not yet run: user runs `make shapes`, then `make rebuild CONFIRM=watchline && make graph`). Next: Q9 reusing `Landlord`, then Q9 reusing `Landlord`. Idea for later: use Beneficial Owner for the shared meaning of Landlord. 23 graph lots without BOR status rows are unexplained (1,032 vs 1,009 expected).
- Q9 (Owner Portfolio): stages 1 to 5 complete (`make profiles`, `taxonomy`, `thesaurus` pass; `make ontology` 121/121; OOPS! run 2026-11-13: P11 and P13 kept). Stage 6 complete: `make shapes` passes 310/310 after a rebuild (user-reported); `shapes/q09.ttl`, `queries/checks/q09-*.cypher`, `tests/negative/q09/cases.yaml` (21 cases), `tests/results/q09-2026-11-13.yaml` (pending). Q8 shape and check relaxed for the shared Landlord layer. Acceptance pending on the frozen dump identity.
- Q6 (aggregator or mail-drop address): stages 1 to 5 complete (loader `scripts/load_service_addresses.py`; tests `tests/q6_1` to `q6_4` pass; `make profiles`, `taxonomy`, `thesaurus` and `ontology` 136/136 pass; OOPS! nothing new). Stage 6 complete: `make shapes` and `make test` pass on the loaded graph (user-reported 2026-11-14); `shapes/q06.ttl`, `queries/checks/q06-*.cypher`, `tests/negative/q06/cases.yaml` (19 cases), `tests/results/q06-2026-11-13.yaml` (pending). Q6.3 is answered per address since 2026-11-15 (`PortfolioMaskedAddress`, 579 texts derived from 5,298 masked identities; `tests/q6_3/check_portfolio_masked.py`; graph checks pending a reload). Open: the list's address normalizer (the list's keys differ from HPD's spelling); the list is preliminary (all unreviewed).

## Lessons since Q1 (apply to every new question)

- **Names.** Compare with rule N3 (`src/watchline/compare.py`): case-insensitive, so `702 Plaza LLC` equals `702 PLAZA LLC`. Look names up through `nameKey`; never compare raw strings.
- **Scope.** Measure a loader's row count before building it. If a scope rule is much wider than the question needs (Q7: 4.4M documents), stop and offer the user narrower options.
- **Fixtures.** Every fixture is re-derived from its source (frozen baseline dump, pinned BOR release) by the check, so a stale fixture fails. Cite the baseline in `data/README.md`; never "provisional".
- **Counting unit.** Name it (rental lots, distinct documents, distinct links). Count `DISTINCT` documents, not links.
- **Cypher.** `as` is reserved: never use it as a variable name.
- **Computed, not stored.** Differences, member counts and comparisons between layers are computed from existing elements. Add a graph element only when a question cannot be answered without it.
- **Files per question.** Spec sub-question table; `tests/qN_M/` (lookup.cypher, check_*.py, fixtures.yaml); `profiles/qNN.yaml` when elements are new; vocabulary concepts plus `term-trace.md`, `thesaurus-notes.md`, `taxonomy-notes.md`; ontology, `concept-mapping.csv` (quote every field containing a comma), `ontology-notes.md`; shapes plus `shapes/coverage.yaml`; negative cases in `tests/negative/qNN/cases.yaml`; a row in `specs/decisions.md`; `tests/results/qNN-DATE.yaml`.
- **Order.** Run one stage at a time. Offline checks I can run: `check_taxonomy`, `check_thesaurus`, `check_ontology`, `validate_skos`, shacl2cypher compile. The user runs `make test`, `make shapes`, `make profiles`, `make oops` and every loader.
- **Reset.** Only `make rebuild CONFIRM=watchline`. Scripts write only to the POC database `watchline`.
- **Privacy.** Person names are never printed or stored in fixtures, logs or results.
- **Relationship properties** get no domain in the ontology (OOPS! P11 accepted); inverses are required for thesaurus related links.
- Q11 (Affiliations): stages 1 to 3 complete (no new graph elements; `scripts/load_mortgages.py` adds scope M, 492,092 MTGE documents naming an HPD owner; `tests/q11_1` to `q11_4`; `profiles/q11.yaml`; `make profiles` 757/757). Anchor C's mortgage is a recorded gap (ACRIS and HPD spell the owner differently). Q11.5 (reported claims, parent company) needs a retrieval cache. Stages 3 and 4 complete (no hierarchy; 16 related pairs, no external mappings). Stage 5 complete (no new ontology element). Stage 6 complete: `make test` and `make shapes` pass (user-reported); graph acceptance passed, Q11.5 pending a retrieval cache. 19 mortgages record one party (shape relaxed to one).
- Q12 (Transfers of a lot): stage 1 complete (`scripts/load_deeds.py` adds `Grantor`, `HAS_GRANTOR`, `nameKey` on `Grantee`; `tests/q12_1` to `q12_3`; not a sale = amount 0 or CORRD/CONDEED; attribution is an N3 name lead). Stage 2 complete: `make profiles` passes 805/805 (`profiles/q12.yaml`). Stage 3 complete: no hierarchy needed (`vocabulary/taxonomy-notes.md`). Stage 4 complete: 6 related pairs, label review, no external mappings; `make thesaurus` 11/11, `make vocab` clean.
- Q12 stage 5 is written: `Grantor`, `hasGrantor`, `grantorName` (`make ontology` passes 162/162; `abox/q12.ttl`, negative cases n34, n35). OOPS! pending: user runs `make oops`. Stage 6 is written: `shapes/q12.ttl`, `queries/checks/q12-name-keys.cypher`, 14 negative cases, `tests/results/q12-2026-11-17.yaml` (compiles offline, 209 rules). `make test` and `make shapes` pass and `make oops` shows only P11 and P13 (user-reported 2026-11-17): Q12 graph acceptance passed.
- Q13 (Mortgages, assignments, satisfactions): stage 1 written (`scripts/load_financing.py`, `HAS_FINANCING_DOCUMENT`, 2,885,412 documents; `tests/q13_1` to `q13_3`). Stage 2 complete: `load_financing.py` reconciled (2,885,412 documents, 3,279,564 pairs, 7,345,721 party links) and `make profiles` passes 824/824 (user-reported). Stage 6 must relax `queries/checks/q07-documents.cypher` and `tests/q7_3/check_documents.py` for scope F.
- Q13 stage 3 is complete: the five document kinds are narrower than `financing-document` (`make taxonomy` 109/109, `make vocab` clean). The user runs `make profiles` to confirm it still passes. Q13 stage 4 is complete: 5 related pairs (kind `acts-on`), label review, no external mappings; `make thesaurus` 11/11 (user-confirm), `make vocab` clean, `make profiles` 824/824. Q13 stage 5 is complete (`make ontology` 165/165; OOPS! P11 and P13). Q13 stage 6 is written: `shapes/q13.ttl`, `queries/checks/q13-financing.cypher`, 12 negative cases, `tests/results/q13-2026-11-17.yaml` (210 rules compile offline); Q7.3 and Q11.1 checks relaxed for scope F. The user runs `make rebuild CONFIRM=watchline`, `make graph`, `make ontology`, `make thesaurus`; Q13 stage 6 is complete: `make test`, `make shapes` 461/461, `make ontology` 165/165, `make thesaurus` 11/11 pass (user-reported 2026-11-17); Q13 graph acceptance passed.
- Q14 (title holder and registered owner on a violation date): stage 1 written; stage 2 complete (`profiles/q14.yaml`, no graph element; violations not loaded; `make profiles` passes 848/848, user-reported 2026-11-17). Stage 3 complete (no hierarchy). Stage 4 complete: 10 related pairs, label review, no external mappings; `make thesaurus` 11/11, `make vocab` clean, `make profiles` 848/848. Stage 5 complete: no new ontology element (`abox/q14.ttl`; `make ontology` 166/166, `taxonomy` 109/109; OOPS! not rerun, TBox unchanged).
- Q14 stage 6 is complete: `make test` 73/73, `make shapes` 468/468 (user-reported 2026-11-18); graph acceptance passed. No new shape; `queries/checks/q14-computed-not-stored.cypher`, 6 negative cases, coverage rows Q14-R1 and R2, `tests/results/q14-2026-11-17.yaml` (retrieval and investigation not declared).
- Q15 (Open violations of a building): stage 1 written; stage 2 complete (`profiles/hpd_violations.yaml`, `profiles/q15.yaml`: `Violation`, `HAS_VIOLATION`; `make profiles` passes 883/883, user-reported 2026-11-18). `scripts/load_violations.py` loads 1,901,592 violations in a couple of minutes; 10,770 are excluded and counted. Stage 3 complete (no hierarchy needed). Stage 4 complete (5 related pairs, no external mappings). Stage 5 complete (no new ontology element; `make ontology` 179/179). Stage 6 written (`queries/checks/q19-computed-not-stored.cypher`, 5 negative cases, `tests/results/q19-2026-11-19.yaml`); `make test` and `make shapes` pass (user-reported 2026-11-19): Q19 graph acceptance passed.
- Q15 stage 3 is complete: no hierarchy needed (`vocabulary/taxonomy-notes.md`); `make taxonomy` 109/109, `make vocab` clean (0 violations, 0 warnings). Next: stage 4.
- Q15 stage 4 is complete (10 related pairs, no external mappings). Stage 5 is complete: `Violation`, `hasViolation`, `violationId`, `violationClass`, `violationStatus`, `inspectionDate`; concept `violation-id` added; `make ontology` 176/176, `make taxonomy` 109/109, `make thesaurus` 11/11, `make profiles` 883/883; `make oops` shows only P11 and P13 (accepted). Next: stage 6.
- Q15 stage 6 is complete; graph acceptance passed (user-reported 2026-11-18): `shapes/q15.ttl`, `queries/checks/q15-violations.cypher`, 18 negative cases, `tests/results/q15-2026-11-18.yaml` (223 rules compile offline). The Q14 no-`Violation` check was relaxed. The user runs `make rebuild CONFIRM=watchline`, `make graph`, `make ontology`, `make thesaurus`.
- Q16 (Reports and filing documents): stages 1 to 3 complete (retrieval-extraction only, no graph element; `profiles/q16.yaml`; no hierarchy needed, `make taxonomy` 109/109, `make vocab` clean). Stage 4 complete: 6 related pairs, label review, no external mappings; `make thesaurus` 11/11, `make profiles` 908/908, `make vocab` clean. Stage 5 complete: no new ontology element (`make ontology` 176/176; reasoner and OOPS! not rerun, TBox unchanged). Stage 6 written: `queries/checks/q16-computed-not-stored.cypher`, 6 negative cases, coverage Q16-R1, `tests/q16/contract.yaml`, `tests/results/q16-2026-11-18.yaml` ; `make shapes` passes (user-reported 2026-11-18): graph acceptance passed; retrieval acceptance pending a cache.
- Q17 (Missing, lapsed or stale registration): stage 1 complete, `make test` passes (user-reported 2026-11-18) (`tests/q17_1` to `q17_4`, shared `tests/q17_support.py`; no new graph element; five answer-contract concepts, `make vocab` clean, `make thesaurus` 11/11, `make taxonomy` 109/109). Answered per lot as of 2026-05-29. `make test` now runs checks in parallel (`scripts/run_tests.py`; `K=q17`, `FAILED=1`, `JOBS=n`). Stages 2 and 3 complete. Stage 4 complete: 10 related pairs, label review, no external mappings; `make thesaurus` 11/11, `make vocab` clean. Stage 5 complete: no new ontology element (`abox/q17.ttl`; `make ontology` 177/177; OOPS! not rerun, TBox unchanged). Stage 6 written: `queries/checks/q17-computed-not-stored.cypher`, 4 negative cases, coverage Q17-R1 and R2, `tests/results/q17-2026-11-18.yaml` (`make shapes` 511/511, user-reported: graph acceptance passed).
- Q19 (Membership explanation): stages 1 to 5 complete (no new graph element; `tests/q19_1` to `q19_4`, `tests/q19_support.py`; four answer-contract concepts; `profiles/q19.yaml`; `make profiles` 999/999, `make vocab` clean, `make thesaurus` 11/11, `make taxonomy` 109/109). The user runs `make test K=q19`. Release v0.3.0 has no stage precision figure, so Q19.4 answers "not evaluated". Stage 3 complete (no hierarchy needed). Stage 4 complete (5 related pairs, no external mappings). Stage 5 complete (no new ontology element; `make ontology` 179/179). Next: stage 6.
- Q21 (Violations across a layer): stages 1 to 6 written (no new graph element; `tests/q21_1` to `q21_3`, `tests/q21_support.py`; `profiles/q21.yaml`, `make profiles` 1052/1052; `make ontology` 181/181; `make thesaurus` 11/11; `make taxonomy` 109/109). Stage 6: `queries/checks/q21-computed-not-stored.cypher` (0 on the loaded graph), 4 negative cases, `tests/results/q21-2026-11-19.yaml`. Graph acceptance is pending: the user runs `make test K=q21` and `make shapes`.
- Q15 pest extension (Q15.3, 2026-11-21): stages 1 to 6 complete, graph acceptance passed (user-reported 2026-11-21) (stage 3: no hierarchy needed; stage 4: three related pairs, no mappings; stage 5: `orderNumber`, `make ontology` 216/216). `Violation.orderNumber` (text) added to `scripts/load_violations.py`; pest kinds come from `data/hpd_pest_orders.yaml` (mice 569 and 869; 566 and 866 are unspecified vermin, never mice); `tests/q15_3`; concepts `order-number` and `pest-violation`; `make profiles` 1287/1287. The user reloads violations and runs `make test K=q15`. (`queries/checks/q15-violations.cypher` and `shapes/q15.ttl` do not know `orderNumber`). The Q27 `minorCategory` extension is separate and not started.
- Q27 pest extension (Q27.3, 2026-11-21): stages 1 to 6 complete, graph acceptance passed (user-reported 2026-11-21) (stage 3: no hierarchy needed; stage 4: six related pairs, no mappings; stage 5: `minorCategory` and `problemCode`, `make ontology` 219/219; stage 6: 270 rules compile, 30 negative cases; `make profiles` 1297/1298, the one failure clears after the reload). `Problem.minorCategory` and `Problem.problemCode` (text) added to `scripts/load_problems.py`; pests are minor category PESTS named by problem code (MICE 147,185 of 349,021 loaded); `tests/q27_3`; concepts `minor-category`, `problem-code`, `pest-complaint`. Correction: complaints do name the pest (earlier note that they do not was wrong). The user reloads problems and runs `make test K=q27`. (`queries/checks/q27-problems.cypher`, `shapes/q27.ttl` and `profiles/q27.yaml` do not know the new properties).
