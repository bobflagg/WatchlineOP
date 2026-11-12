# Stage 6 procedure: knowledge graph, per question

Run this for each competency question after its [stage 5](stage5-procedure.md) is accepted, one question at a time. Stage definition and exit criterion: [roadmap.md](roadmap.md#stages) (Stage 6 row, exit criterion 6), the [acceptance types](roadmap.md#acceptance-types-and-responsibility) and the [expected-answer policy](roadmap.md#expected-answer-policy). Tools: [tech-stack.md](tech-stack.md).

To run it in a fresh Claude Code session, start with: "Execute specs/stage6-procedure.md for QNN."

**Goal:** finish and prove the question's graph. The loaders, native constraints and per-sub-question checks were built test-first in stages 1 and 2; this stage adds the rules the ontology could not express (as shapes), shows that bad data is rejected, runs the whole build from scratch, and delivers fixtures for acceptance that runs downstream.

## Ground rules

- Check first that the question's stages 1 to 5 are accepted in `specs/decisions.md` and that `make profiles`, `make thesaurus` and `make ontology` pass. If not, stop and say so.
- Check the baseline: `data/README.md` must identify the frozen dump (filename, SHA-256, restore details). If it does not, you may write artifacts, but every acceptance result stays `pending` with that reason. Never report `passed` against an unidentified baseline.
- Read: `CLAUDE.md`, the question file and its `acceptance_types`, `profiles/qNN.yaml`, "Rules for Stage 6 shapes" in `ontology/ontology-notes.md`, the concept mapping, `decisions.md`, and the existing `scripts/`, `tests/` and `shapes/`.
- The schema is `profiles/qNN.yaml`, the loaders are `scripts/load_*.py`, and the checks are `tests/qN_M/`. Do not add a second description of the same things (no mapping files, no crosswalk).
- Access rules: scripts load, test and produce expected answers, using `.env` credentials. MCP servers are for exploration only. The source database and the Neo4j MCP are read-only. Only scripts write, and only to the POC database `watchline`. Never print or commit credentials.
- Write guard: every script that writes verifies the target database is the one named in `.env` and refuses otherwise. Destructive resets use `make rebuild CONFIRM=watchline`.
- Expected answers come from SQL against the frozen database, written independently of the graph and the loader. Live public data is never a test oracle.
- A skipped check, an error and a timeout are not passes. A retry targets the same input and is recorded without erasing the first failure.
- Do not weaken a check to make it pass. Do not commit to Git unless asked. Stop and ask when a decision is unsettled.

## One-time setup (first question only)

Confirm with the user, then log in [decisions.md](decisions.md):

- **Neo4j:** read the running version and edition with `CALL dbms.components()` and record them. Property existence and type constraints need Enterprise. Where the edition lacks a constraint, the loader enforces it and a named check covers it.
- **shacl2cypher:** it is a declared dependency. Build a small compatibility fixture first and record which SHACL constructs the pinned version compiles in strict mode. Where it cannot express a rule, write the equivalent Cypher check by hand, list it as a supplemental check, and do not call it SHACL validation.
- **Layout:** `shapes/qNN.ttl` (semantic SHACL), `shapes/qNN-neo4j.ttl` only if the physical encoding differs, `shapes/coverage.yaml`, `queries/checks/qNN-*.cypher` (supplemental checks), `tests/negative/qNN/`, `tests/results/qNN-<date>.yaml`.
- **Results format:** per acceptance type: `pending`, `passed` or `failed`, with the fixture version, the evidence, and the tool versions exercised (Neo4j version and edition, shacl2cypher, `uv.lock` revision, Geosupport image).
- **Make targets:** `shapes` (compile, run, report coverage) and `negative` (seeded bad data), added to `graph`.

## Per-question steps

1. **Collect the inputs.** List the question's rules from "Rules for Stage 6 shapes", the native constraints already installed, the sub-questions and their acceptance types, and the checks that already exist.
2. **Write the shapes.** Turn each rule into SHACL (`shapes/qNN.ttl`), using the ontology IRIs and the concept mapping's graph names. Compile with shacl2cypher in strict mode. Rules the compiler cannot express become named Cypher checks in `queries/checks/`.
3. **Write the coverage table** (`shapes/coverage.yaml`). For every required rule record whether it is compiled and run, guaranteed by a native constraint, or covered by a named supplemental check. Unsupported constructs are rewritten or covered, never dropped.
4. **Write the negative cases.** For each rule, seed a bad case and show the responsible layer rejects it: the native constraint, the loader or a shape. Run them inside a rolled-back transaction or against a separate, explicitly named scratch database. Never inject bad data into the accepted graph.
5. **Review the acceptance checks.** The per-sub-question checks (`tests/qN_M/`) already compare the graph with independent SQL. Confirm each sub-question with graph acceptance has one, that its fixtures hold the worked examples, missing-data cases and ambiguity cases, and that totals reconcile (source, stage, graph, with exclusions listed).
6. **Deliver downstream fixtures and contracts.** For `retrieval-extraction` and `investigation` acceptance, supply the cached inputs, fixture records and expected-result contracts (for Q1, the recorded Geosupport responses and the answer contract). WatchlineOP does not run these. Their results stay `pending` until the downstream consumer passes them, and are never reported as passed because the graph is ready. A fixture that needs the user's machine (the Geosupport image) is recorded by the user; say what is needed and mark it pending until it exists.
7. **Rebuild and run everything.** `make rebuild CONFIRM=watchline`, then `make graph` (load, profiles, test, shapes, negative), then `make ontology` and `make thesaurus`. Write the results file. Fix failures at their cause.
8. **Review and accept.** Check the exit criterion, log decisions in `decisions.md`, update `CLAUDE.md` (open points), and report results, anything pending and why.

## Exit criterion (per question)

- The graph rebuilds from scratch and every sub-question check passes against frozen fixtures, including missing-data and ambiguity cases.
- Source, stage and graph counts reconcile, with exclusions listed.
- Every rule in "Rules for Stage 6 shapes" is compiled and run, native, or covered by a named supplemental check, with no unexplained skipped check, error, timeout or violation.
- The shapes pass on the loaded graph and fail on seeded bad data; each negative case is rejected by the responsible layer.
- Downstream fixtures and contracts for `retrieval-extraction` and `investigation` are delivered. Their results are `pending` unless the downstream consumer has passed them.
- The results file records the fixture version, evidence and tool versions. A graph that was not fully validated is not presented as accepted.

## Deliverables (updated per question)

- `shapes/qNN.ttl`, `shapes/coverage.yaml`, `queries/checks/`
- `tests/negative/qNN/`, `tests/results/qNN-<date>.yaml`
- Downstream fixtures and contracts
- New entries in `decisions.md`

## After all questions

Consolidate: rebuild the whole graph and re-run every check, review the model for consistency across questions, and report per-question, per-acceptance-type results (pending, passed, failed). When a new snapshot is adopted, create new fixture versions, keep the previous baseline, and report differences as freshness or coverage limits, not failures. Report downstream execution results separately.
