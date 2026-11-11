# Physical implementation contract (POC)

This contract connects the ontology and application profiles to source extraction, Neo4j storage, and acceptance tests. It preserves the lightweight POC approach: readable mapping files, Cypher schema files, scripts, and test results in Git. A mapping registry, migration framework, and automated release system are not required.

## 1. Mapping artifacts

Store mappings in `mappings/` as YAML, with a short README where rules need explanation. Git revisions identify changes during the POC; no separate mapping-version service is required. Before a mapping is used, specify:

| Item | Required content |
| --- | --- |
| Purpose | Mapping ID, question IDs, and ontology class/property or controlled-value IRIs |
| Inputs | Source keys from `data/sources.yaml`, schema/table/column names or release files, snapshot/release identity, selection filters, and scope |
| Identity | Node labels, canonical identifier properties, identifier normalization/validation, and deduplication keys |
| Joins | Join columns, expected cardinalities, relationship direction/type, endpoint keys, and treatment of missing or conflicting matches |
| Values | Source field, target property, semantic datatype, physical datatype, units, transformation, and null/sentinel policy |
| Evidence | Source-record key or reproducible row locator, source snapshot, mapping/Git revision, and build/run identifier |
| Exceptions | Duplicate/conflict handling, invalid values, excluded records, and the reason recorded for each omission |
| Verification | Representative input/output examples, graph test queries, applicable shapes, and supplemental checks |

Do not silently choose the first row of a conflicting join, merge entities on name alone, or create missing relationship endpoints without a documented identity rule. Preserve source evidence for disputed or omitted values in an appropriate extract or exception log, subject to the data exclusions in the use case and source inventory.

## 2. Identity and graph representation

- Keep vocabulary concepts, ontology elements, and instances distinct as specified in [the roadmap](roadmap.md#skos-to-ontology-mapping). A mapping must name the physical labels, relationship types, and properties; these are not inferred automatically from OWL.
- Store BBL and BIN as canonical strings, not numeric measures. Validate identifier structure and source placeholder values before creating parcel/building identities. Specify the accepted formats and exception cases in the mapping.
- For Q1, use `TaxParcel` nodes identified by BBL and `Building` nodes identified by BIN. If the graph later supports multiple jurisdictions, scope local identifiers by jurisdiction. Do not impose a universal one-building-per-parcel or one-parcel-per-building rule.
- Document relationship identity and replay behavior. Rerunning an interrupted batch must not create duplicate source records, entities, or associations. Different snapshots or runs must not be merged into one evidentiary assertion accidentally.
- Ordinary scalar values are node properties. Add observation or assertion nodes only when required for independently queryable history, conflicts, relationships, or evidence. An OWL class does not automatically require instances in the physical graph.
- Import Operational Networks and Owner Portfolios from the selected BOR release, with run, method, membership, and evidence context. Do not recompute them from co-location or confuse them with WoW's own grouping tables.

## 3. Accepted Q1 scalar mapping

All four values below are lot-wide projections from a selected PLUTO record onto `TaxParcel`. Do not copy them to every Building node. The mapping must name the row-selection rule and identify the selected source record and snapshot. Where rows conflict and no selection is justified, omit the affected projection and report the conflict.

| PLUTO field | Neo4j property | Physical encoding and policy |
| --- | --- | --- |
| `yearbuilt` | `plutoYearBuilt` | Integer source-reported year built; null/zero is unknown and omitted. Do not derive the first construction date or earliest building year |
| `bldgclass` | `plutoBuildingClassCode` | String source classification code; preserve its classification-system identity. Do not confuse this with a building-level assertion |
| `unitsres` | `plutoResidentialUnitCount` | Nonnegative integer count for the lot; zero is valid and is distinct from missing |
| `assesstot` | `plutoAssessedTotalValueCents` | Exact integer USD cents. Convert decimal source dollars without passing through binary floating point; reject unrepresentable precision or overflow rather than round silently |

Missing values are absent properties, not empty strings, invented zeros, or fabricated dates. Specify all other field-specific sentinels and parse failures in the mapping. Never guess an assessment period or roll status from the ingestion date; record unknown context explicitly in the applicable profile/evidence.

Use `TaxParcel` → `PLUTO_SOURCE_RECORD` → `SourceRecord` → `IN_SNAPSHOT` → `SourceSnapshot` as the Q1 evidence path. Field mappings identify which attributes that selected record supports. A shared source link must not be used to imply support for unrelated properties. If different fields use different rows, make their evidence attribution explicit.

## 4. Neo4j schema and write checks

Store schema Cypher in `scripts/neo4j-schema.cypher` when implementation begins. Apply it before loading and verify required indexes are online before bulk writes.

- Create uniqueness constraints for canonical node identity: for Q1, `TaxParcel.bbl`, `Building.bin`, and the chosen identifiers of SourceRecord and SourceSnapshot. Any additional canonical instance IRI used for lookup must also be unique within its intended scope.
- Require identity properties in extraction/staging and loader checks. Use native existence/type constraints where supported by the pinned Neo4j edition; document equivalent checks otherwise. Uniqueness alone is not an identity-presence check.
- Add indexes for accepted lookup, join, and evidence-path queries where not already supplied by constraints. Record their purpose and avoid redundant indexes.
- Check that every intended relationship resolves its endpoints and that loaded/deduplicated counts reconcile with staged counts. Record exclusions separately; do not hide dropped rows in aggregate totals.

Native constraints, indexes, and loader checks are explicit implementation artifacts, independent of shacl2cypher output. Neo4j Graph Type may be evaluated later; it is not a POC prerequisite and must not delay identity constraints or validation.

## 5. Validation and graph acceptance

Maintain a semantic SHACL profile and, where physical encoding differs, a documented derived Neo4j profile. For example, semantic decimal dollars and year values require explicit mapping to integer cents and integer years. Derived constraints must preserve the intended checks or identify a supplemental test; successful compilation alone is not proof of equivalent validation.

For each required constraint, record whether it is compiled and executed, guaranteed by an installed native constraint, or covered by a named supplemental check. Compile in strict mode. Unsupported constructs must be rewritten or covered explicitly, never silently dropped. Keep the supported-feature list tied to the pinned compiler version.

Graph acceptance requires:

1. Successful installation/verification of the schema and source-to-stage-to-graph count reconciliation.
2. Comparison of persisted values and evidence links with the mapped source expectations; shapes alone cannot detect an incorrect but well-typed value.
3. Complete execution of required shape and supplemental checks, with no unexplained skipped checks, errors, timeouts, or violations. If a required check cannot run, acceptance remains pending or failed.
4. Applicable question queries passing against frozen fixtures, including appropriate missing-data and ambiguity results.
5. Negative fixtures demonstrating that relevant bad data is rejected by the native schema, loader, or validation check responsible for it. Schema-guaranteed rules need rejection tests rather than bypassing constraints to inject bad data into the accepted graph.

Use bounded batches for loading and property reconciliation; avoid citywide sorts that materialize the entire graph's properties. Set explicit resource/time budgets, log progress, and retain completed-check results. A retry must identify the same target and unchanged input context; record its result without erasing the original failure. A timeout is not a pass.

## 6. Access to the source database and the graph

- **Scripts:** loads, reconciliation, graph tests, and the SQL that produces expected answers use the Python drivers with credentials from `.env`. They are committed to Git and run in bounded batches.
- **MCP servers:** interactive exploration and spot checks only. Nothing committed (fixtures, expected answers, graph data) comes from a chat session.
- **Source database:** read-only everywhere. The MCP connection uses a read-only role.
- **Graph writes:** only scripts write to the POC graph. The MCP entry for the graph is read-only, or points at the POC database and no other. A write-capable MCP must never point at a graph other than the designated POC target.
- **Expected answers:** produced by SQL against the frozen source database, independent of the graph and the loader.

## 7. Rebuild and environment

Keep source extraction read-only. After an accepted model change, rebuild only the designated POC Neo4j graph and rerun existing checks. A failed or partially validated build must not be presented as accepted. Support checkpointed loading where needed, binding a checkpoint to the target and input mapping context. Replaying a batch must be safe.

Retain source evidence outside any disposable graph container. Destructive reset commands must identify the POC target explicitly and must not affect the source database or other graphs. Changing snapshots requires an explicit decision, not an incidental side effect of rebuilding.

Use uv and a committed lockfile for Python dependencies. Pin the Neo4j version and edition, Cypher dialect, shacl2cypher version, and any address-resolution service image/version used by a test. Record the versions actually exercised with the test result. New dependency choices require a small compatibility fixture before use; this contract does not claim that every current tool feature is supported.

Implementations must stay within [the expected-answer policy](roadmap.md#expected-answer-policy) and [the lightweight POC rules](roadmap.md#lightweight-poc-iteration). This document specifies requirements; it does not claim that mapping files, schema scripts, or tests have already been implemented in this repository.
