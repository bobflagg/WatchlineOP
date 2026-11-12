# Physical implementation contract (POC)

This contract connects the ontology and question schemas to source extraction, Neo4j storage and acceptance tests. It keeps the POC lightweight: YAML schemas, loader scripts, test files and results in Git. A mapping registry, migration framework and automated release system are not required.

## 1. Where the mapping lives

There are no separate mapping files. Each part of the mapping has one home:

| Item | Home |
| --- | --- |
| Source facts: tables, columns, keys, quirks, row counts | `profiles/<source_key>.yaml` |
| Graph elements per question: labels, relationship types, properties, types, keys, scope, rules, null policy, answer fields | `profiles/qNN.yaml` (checked against the live graph by `make profiles`) |
| Ontology element to graph name | `ontology/concept-mapping.csv` (`graph_name` column) |
| Joins, selection, exclusions, value transformations | the loader scripts `scripts/load_*.py`, with the rule stated in the profile |
| Verification | `tests/qN_M/` (independent SQL, Cypher lookup, fixtures, check script) |

Do not silently choose the first row of a conflicting join, merge entities on name alone, or create relationship endpoints without a documented identity rule. Ties that cannot be resolved leave the value absent, and the profile says so.

## 2. Identity and graph representation

- Keep vocabulary concepts, ontology elements and instances distinct as in [the roadmap](roadmap.md#skos-to-ontology-mapping). Graph names are never inferred from OWL; the profile names them.
- Store BBL and BIN as canonical strings. Validate the structure and source placeholders before creating identities (BIN: 7 digits, first digit 1 to 5, not ending 000000; BBL: 10 digits, first digit 1 to 5).
- Q1 uses `Lot` nodes identified by BBL and `Building` nodes identified by BIN, joined by `HAS_BUILDING`. Do not impose a universal one-building-per-lot or one-lot-per-building rule.
- Loaders use `MERGE` on identity keys, so replaying a batch creates no duplicates.
- Ordinary scalar values are node properties. Add observation or assertion nodes only when a question needs queryable history, conflicts, relationships or evidence. An OWL class does not require a physical node.
- Provenance for database facts is dataset-level: the frozen baseline in `data/README.md` and `specs/decisions.md`. No per-record source nodes. Add them only when a question stores derived items, claims, documents or cached responses.
- Import Operational Networks and Owner Portfolios from the selected BOR release, with run, method and membership context. Do not recompute them from co-location or confuse them with WoW's own grouping tables.

## 3. Q1 scalar encodings

The lot-wide PLUTO values are properties of `Lot`. They are not copied to buildings.

| PLUTO field | Property | Encoding and policy |
| --- | --- | --- |
| `yearbuilt` | `yearBuilt` | Integer. 0 is absent |
| `bldgclass` | `buildingClass` | String. Blank is absent |
| `unitsres` | `unitsRes` | Whole number. 0 is kept and means PLUTO records none |
| `assesstot` | `assessedTotal` | Whole US dollars as an integer. 0 is kept and means PLUTO records none |
| `numbldgs` | `plutoNumBuildings` | Integer, PLUTO's count. Named for its source and always reported apart from the number of `HAS_BUILDING` edges |

Missing values are absent properties, never empty strings or invented zeros. Never guess an assessment period or roll status from the ingestion date.

## 4. Neo4j schema and write checks

The loaders create their own uniqueness constraints (`lot_bbl_unique`, `building_bin_unique`) before loading. `make profiles` compares the live schema with `profiles/qNN.yaml`.

- Check identity properties during staging, and reconcile staged counts against graph counts with exclusions reported separately.
- Use native existence and type constraints where the pinned Neo4j edition supports them; the shapes cover the rest.
- Add an index only for an accepted lookup, with a stated purpose.
- Every intended relationship must resolve both endpoints.

Native constraints and loader checks are explicit artifacts, independent of shacl2cypher output.

## 5. Validation and graph acceptance

Shapes (`shapes/qNN.ttl`) are SHACL with `s2c:` annotations that give each ontology element its graph name, compiled by shacl2cypher in strict mode. For each required rule `shapes/coverage.yaml` records whether it is compiled and run, native, or covered by a named test. Unsupported constructs are rewritten or covered, never dropped. The supported-feature list is tied to the pinned compiler version.

Graph acceptance requires:

1. A rebuild from scratch (`make rebuild CONFIRM=watchline`, then `make graph`) and source-to-stage-to-graph counts that reconcile.
2. Persisted values compared with independent SQL; shapes alone cannot detect a wrong but well-typed value.
3. Every shape and supplemental check run, with no unexplained skipped check, error, timeout or violation.
4. Each sub-question check passing against frozen fixtures, including missing-data and ambiguity cases.
5. Seeded bad data (`tests/negative/qNN/`) rejected by the responsible layer, run in transactions that are rolled back. Never inject bad data into the accepted graph.

Use bounded batches for loading and reconciliation, with progress logging. A retry targets the same input and is recorded without erasing the first failure. A timeout is not a pass.

## 6. Access to the source database and the graph

- **Scripts:** loads, reconciliation, graph tests, and the SQL that produces expected answers use the Python drivers with credentials from `.env`. They are committed to Git and run in bounded batches.
- **MCP servers:** interactive exploration and spot checks only. Nothing committed (fixtures, expected answers, graph data) comes from a chat session.
- **Source database:** read-only everywhere. The MCP connection uses a read-only role.
- **Graph writes:** only scripts write to the POC graph. The MCP entry for the graph is read-only, or points at the POC database and no other. A write-capable MCP must never point at a graph other than the designated POC target.
- **Expected answers:** produced by SQL against the frozen source database, independent of the graph and the loader.

## 7. Rebuild and environment

Keep source extraction read-only. After an accepted model change, rebuild only the designated POC graph and rerun every check. A failed or partially validated build is not presented as accepted. Replaying a batch must be safe.

Retain source evidence outside any disposable graph container. Destructive reset commands (`make rebuild CONFIRM=watchline`) identify the POC target explicitly and never touch the source database or another graph. Changing snapshots requires an explicit decision, not a side effect of rebuilding.

Use uv and a committed lockfile. Pin the Neo4j version and edition, Cypher dialect, shacl2cypher version and any address-resolution service image used by a test, and record the versions actually exercised with the test result (`tests/results/`). New dependency choices need a small compatibility fixture before use.

Implementations stay within [the expected-answer policy](roadmap.md#expected-answer-policy) and [the lightweight POC rules](roadmap.md#lightweight-poc-iteration).
