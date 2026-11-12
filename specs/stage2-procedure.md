# Stage 2 procedure: metadata schema, per question

Run this for each competency question after its [stage 1](stage1-procedure.md) is accepted, one question at a time. Stage definition and exit criterion: [roadmap.md](roadmap.md#stages). Tools: [tech-stack.md](tech-stack.md).

To run it in a fresh Claude Code session, start with: "Execute specs/stage2-procedure.md for QNN."

**Goal:** declare, once, the contract between source, graph and answer. Every graph element and answer field has a name, a vocabulary concept, a source, a type, allowed values and a null policy. A check then confirms that the graph holds exactly what is declared and nothing more.

## Ground rules

- Read first: `CLAUDE.md` (auto-loaded), the question file, `vocabulary/watchline.ttl` and `vocabulary/term-trace.md`, `specs/decisions.md`, the `tests/qN_M/` folders (their `expected.sql` and fixtures hold the rules already proved on data), and the entries in `data/sources.yaml` for this question's sources.
- The schema records rules already proved in Stage 1; it does not invent new ones. If writing it exposes a gap, fix the rule in Stage 1 (test first), then return here.
- Never guess a type, sentinel or format. Inspect database columns with the read-only `postgres-justfix` MCP and record the query date. Nothing committed comes from a chat session; checks are scripts.
- Non-database sources (cached Geosupport responses, release files) are profiled from their recordings or manifests. Mark a field `pending` with a reason if they are not available. Do not invent them.
- If you change `vocabulary/watchline.ttl`, run `validate_skos` and report findings.
- Do not commit to Git unless asked. Stop and ask when a decision is unsettled.
- Reuse before creating. Extend an existing source profile rather than starting a second one.

## One-time setup (first question only)

Confirm with the user, then log in [decisions.md](decisions.md):

- **Layout:** `profiles/<source_key>.yaml` per source (shared across questions) and `profiles/qNN.yaml` per question, holding graph elements and answer fields.
- **Naming:** `snake_case` for profile field names; graph labels, relationship types and properties exactly as the loader writes them. Allowed values reference a SKOS scheme IRI where one exists, otherwise an enum or range.
- **Check script:** `scripts/check_profiles.py` (`pyyaml`, `rdflib`, `neo4j`) behind `make profiles` (step 6).
- **Evidence fields:** per-record evidence (source key, snapshot, run, assertion type, review status) is defined only when a question first needs derived edges, claims, documents or cached responses stored in the graph. Database-row facts carry dataset-level provenance only (`data/sources.yaml`).

## Per-question steps

1. **List the question's inputs.** From the question file and `term-trace.md`, list its sources, graph elements and answer fields.
2. **Inspect the real data.** For each source column used, record the Postgres type, null and sentinel behaviour, units, precision and identifier formats. Flag any column missing from `columns_used` in `data/sources.yaml`, and add it.
3. **Source profiles** (`profiles/<source_key>.yaml`). For each column used: name, physical type, units, allowed values or range, sentinels and their meaning, and the question that uses it. Record only facts about the source.
4. **Question schema** (`profiles/qNN.yaml`), in three parts:
   - **Graph elements:** each label, relationship type (with endpoints) and property: vocabulary concept IRI, semantic and physical type, units, allowed values or range, null policy (absent versus kept as recorded), and its source column or derivation rule with a pointer to the proving `expected.sql`.
   - **Answer fields:** each field the agent returns, its source (a graph property, a tool output or derived), allowed values (outcomes reference their SKOS scheme), and the counting unit for any count. Fields that carry uncertainty or an outcome say so.
   - **Not stored:** terms tagged as tool output or answer contract in Stage 1, so the schema shows what the graph deliberately omits.
5. **Concept-level provenance (ask once, then follow the answer).** If accepted, add `dct:source` to concepts new in this question, pointing to the question file or source documentation. Run `validate_skos`.
6. **Check.** Run `make profiles`. The script fails nonzero if:
   - a YAML file is malformed or lacks required keys;
   - a concept IRI is not in `watchline.ttl`;
   - a source column named in a schema is missing from `data/sources.yaml` `columns_used` or from the source profile;
   - a graph property or answer field lacks a concept, source or type (and a property a null policy), or an enum differs from its SKOS scheme;
   - a file named in `proved_by`, `lookup` or `recorded` does not exist;
   - the graph holds a label, relationship type or property the schema does not declare, or lacks one it declares, or a property's stored type differs from the declared one.

   A missing or skipped check is a failure.
7. **Review and accept.** Check the exit criterion, log new decisions in `decisions.md`, and update `CLAUDE.md` (open points) and `tech-stack.md` if they changed. Report results and anything left open.

## Exit criterion (per question)

- Every graph element and answer field has a schema entry with concept, source and type; every property has a null policy; every enum equals its SKOS scheme.
- Every source column used is in its source profile and in `data/sources.yaml` `columns_used`.
- Every concept IRI referenced exists in the vocabulary.
- `make profiles` passes, with nothing skipped, and the graph has no undeclared label, relationship type or property.
- Fields that cannot be completed yet are marked `pending` with a reason, not filled in.

## Deliverables (updated per question)

- `profiles/<source_key>.yaml` (new or extended)
- `profiles/qNN.yaml`
- `scripts/check_profiles.py` and the `make profiles` target
- Updated `data/sources.yaml` where columns were missing
- New entries in `decisions.md`

## After all questions

Review the profiles for consistency across questions (the same column typed the same way everywhere) and re-run `make profiles`, as in the roadmap's order of work.
