# Stage 2 procedure: metadata schema, per question

Run this for each competency question after its [stage 1](stage1-procedure.md) is accepted, one question at a time. Stage definition and exit criterion: [roadmap.md](roadmap.md#stages). Tools: [tech-stack.md](tech-stack.md).

To run it in a fresh Claude Code session, start with: "Execute specs/stage2-procedure.md for QNN."

**Goal:** every field in the question's answer shape has a profile entry with source, type and allowed values, and every source column used is crosswalked to a profile field and a vocabulary concept.

## Ground rules

- Read first: `CLAUDE.md` (auto-loaded), the question file, `vocabulary/watchline.ttl` and `vocabulary/term-trace.md`, `specs/decisions.md`, [roadmap.md](roadmap.md) (Stage 2 row, exit criterion 2), [physical-implementation.md](physical-implementation.md) (sections 1 to 3 and 6), and the entries in `data/sources.yaml` for this question's sources.
- Inspect database sources with the read-only `postgres-justfix` MCP. Never guess a type, sentinel or format. Record what you find with the query date. Nothing committed comes from a chat session; checks are scripts.
- Non-database sources (BOR/NLR releases, cached Geosupport and web responses, the mail-drop list) are profiled from their release files, manifests or cached responses, not from Postgres. If those are not available, mark the affected fields `pending` with the reason. Do not invent them.
- If you change `vocabulary/watchline.ttl`, run `validate_skos` and report findings. Do not claim validity without running it.
- Do not commit to Git unless asked. Stop and ask when a decision is unsettled.
- Reuse before creating. Extend an existing source profile rather than starting a second one.

## One-time setup (first question only)

Confirm with the user (recommended defaults apply if they say "go"), then log in [decisions.md](decisions.md):

- **Layout:** `profiles/evidence.yaml` (shared provenance fields), `profiles/<source_key>.yaml` per source, `profiles/qNN-answer.yaml` and `profiles/crosswalk-qNN.yaml` per question.
- **Naming:** `snake_case` field names. Allowed values reference a SKOS scheme IRI where one exists, otherwise an enum or range in the YAML.
- **`source_category` spelling:** decided 2026-11-11: `project_derived` everywhere (see decisions.md).
- **Shared evidence profile:** write `profiles/evidence.yaml` once, with the fields from the roadmap: `source_key`, `snapshot_id`, `snapshot_date` (ISO 8601), `run_id`, `source_category`, `assertion_type` (I, II, reported claim), `review_status` (`unreviewed`, `confirmed`, `refuted`, `inconclusive`, `contested`), plus `source_record_locator` and `mapping_git_revision` (physical-implementation section 1, Evidence). Map each to Dublin Core, DCAT or PROV-O terms.
- **Check script:** add `scripts/check_profiles.py` (`pyyaml`, `rdflib`, added with `uv add`) and implement `make profiles` (see step 7).

## Per-question steps

1. **List the question's inputs.** From the question file, list its sources and the answer-shape fields (sub-questions included). Note which fields the stage 1 vocabulary already names.
2. **Inspect the real data.** For each source column used, record the Postgres type, null and sentinel behaviour, units, precision, identifier formats and the shape of distinct values. Flag any column the question uses that is missing from `columns_used` in `data/sources.yaml`, and add it.
3. **Source profiles.** For each source column give: name, semantic type, physical type, units, allowed values or range, null/sentinel policy, vocabulary concept IRI, and the question or sub-question that uses it. Include any physical encodings already accepted in physical-implementation.
4. **Answer-shape profile.** One entry per answer field, naming its source profile field or saying it is derived, with allowed values. Counts name their counting unit. Fields that carry uncertainty, outcomes or assertion type say so.
5. **Crosswalk.** Source column, profile field, vocabulary concept IRI, physical Neo4j property (the accepted name, or `TBD stage 6`).
6. **Concept-level provenance (ask once, then follow the answer).** If accepted, add `dct:source` to the concepts new in this question's stage 1, pointing to the question file, source data dictionary or service guide that supports the definition. Run `validate_skos`.
7. **Check.** Run `make profiles`. The script fails nonzero if: a YAML file is malformed or lacks required keys; a concept IRI is not in `watchline.ttl`; an answer field has no profile entry with source, type and allowed values; a crosswalked column is missing from `data/sources.yaml` `columns_used`; an enum differs from the specs. A missing or skipped check is a failure.
8. **Review and accept.** Check the exit criterion below, log new decisions in `decisions.md`, and update `CLAUDE.md` (open points) and `tech-stack.md` if they changed. Report results and anything left open.

## Exit criterion (per question)

- Every field in the question's answer shape has a profile entry with source, type and allowed values.
- Every source column used is in the crosswalk and in `data/sources.yaml` `columns_used`.
- Every concept IRI referenced exists in the vocabulary.
- `make profiles` passes, with nothing skipped.
- Fields that cannot be completed yet (for example BOR or cached-response fields) are marked `pending` with a reason, not filled in.

## Deliverables (updated per question)

- `profiles/<source_key>.yaml` (new or extended)
- `profiles/qNN-answer.yaml`
- `profiles/crosswalk-qNN.yaml`
- Updated `data/sources.yaml` where columns were missing
- New entries in `decisions.md`

## After all questions

Review the profiles for consistency across questions (the same column typed the same way everywhere) and re-run `make profiles`, as in the roadmap's order of work.
