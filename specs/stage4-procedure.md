# Stage 4 procedure: thesaurus, per question

Run this for each competency question after its [stage 3](stage3-procedure.md) is accepted, one question at a time. Stage definition and exit criterion: [roadmap.md](roadmap.md#stages) (Stage 4 row, exit criterion 4) and the [taxonomy review policy](roadmap.md#taxonomy-review-policy). Tools: [tech-stack.md](tech-stack.md).

To run it in a fresh Claude Code session, start with: "Execute specs/stage4-procedure.md for QNN."

**Goal:** add the links that help a reader move between concepts in different branches (related links), review labels so user wording finds the right concept, and map concepts to external schemes where a true mapping exists. A concept with no justified association stays unlinked.

## Ground rules

- Read first: `CLAUDE.md` (auto-loaded), the question file, `vocabulary/watchline.ttl`, `vocabulary/term-trace.md`, `vocabulary/taxonomy-notes.md`, `vocabulary/thesaurus-notes.md` (if it exists), this question's `profiles/` files, `specs/decisions.md`, and the roadmap sections linked above.
- Run `validate_skos` (the `skos` MCP server) after every change to `vocabulary/`, and report its findings before moving on. Never validate by hand or claim validity without running it. Send only vocabulary files to the server.
- Concept IDs stay stable. A new link or label never changes or reuses an ID.
- A related link is an association. It is not a hierarchy (Stage 3), not equivalence, and not lexical similarity. Do not invent links to silence a disconnection warning.
- **Do not repeat what the schema already says.** Which property belongs to which node is declared in `profiles/qNN.yaml` and checked against the graph. A related link earns its place only where it helps a reader reach a concept the schema does not connect to the one in hand.
- Do not mint new properties or ontology axioms; that is Stage 5. Use SKOS properties only.
- External IRIs must be checked, not recalled. Do not assert a mapping to an IRI whose definition you have not read.
- Do not commit to Git unless asked. Stop and ask when a decision is unsettled.

## One-time setup (first question only)

Confirm with the user, then log in [decisions.md](decisions.md):

- **Related links are written in both directions** in the file (each pair has two `skos:related` triples).
- **Notes file:** create `vocabulary/thesaurus-notes.md` with four sections: **Related links** (table `| concept | concept | kind | justification |`, each unordered pair once, concepts as backticked slugs), **Labels** (shared and ambiguous labels reviewed), **External mappings** (summary, with the SSSOM file as the record), **Exceptions** (one line per concept left unlinked on purpose, naming its slug).
- **Association kinds:** a short list in the notes file, used in the `kind` column (for example identifier-of, output-of, input-to, source-of, contrasts-with, same-subject-different-role). Extend it as questions need. Plain `skos:related` goes in the file; the kind lives in the notes.
- **Labels:** keep plain SKOS labels. Use hidden labels for source spellings or common user wording that should find a concept but not be displayed. Adopt SKOS-XL only for a label that needs its own metadata, and only for that label.
- **External schemes:** ask the user which schemes to target, and map only where it helps the agent or interoperability. Candidates, each verified before use: PROV-O, schema.org, W3C ORG, Wikidata, and the BOR release's own vocabulary. Record the choice.
- **Mappings file:** `vocabulary/mappings/external.sssom.tsv` (SSSOM), created with the first mapping, one row per mapping: `subject_id`, `predicate_id`, `object_id`, `mapping_justification` (for example `semapv:ManualMappingCuration`), `author_id`, `mapping_date`.
- **Check script:** `scripts/check_thesaurus.py` (`rdflib`) behind `make thesaurus` (step 8).

## Per-question steps

1. **Find the candidate associations.** From the question, its caveats, `term-trace.md` and the existing `skos:related` links, list pairs of concepts that a reader would need to move between and that the schema does not already connect: a concept and its identifier, an answer term and the concept it reports, look-alike concepts the question insists on keeping apart. Test each: is it meaningful for this question, neither hierarchy, nor equivalence, nor a repeat of the schema? If not, drop it, including existing links that fail the test.
2. **Name the kind of each association** from the notes file's list, and write the one-line justification.
3. **Make the links symmetric.** Add the inverse of every one-way related link, and remove links dropped in step 1 in both directions.
4. **Review labels.** For this question's concepts and any they touch, check each alternative label against the whole vocabulary. Shared labels are allowed when definitions and scope make the meanings clear; otherwise qualify or remove. Add hidden labels for the wording users and sources actually use. Record the review in **Labels**.
5. **Map to external schemes.** For each concept, look in the chosen schemes and read the external definition. Use the weakest predicate that is true: `skos:exactMatch` only when the definitions are equivalent, otherwise `closeMatch`, `broadMatch`, `narrowMatch` or `relatedMatch`. No match is a valid result; record "none found in <schemes>". Add rows to the SSSOM file, never to the vocabulary file by guesswork.
6. **Review connectivity.** Run `validate_skos`. Review disconnected concepts, cycles and mixed hierarchy meanings in context. Resolve real problems. For each concept left unlinked on purpose, add a line to **Exceptions**.
7. **Pilot the navigation.** For the question's worked examples, confirm that the terms a reader would move between are reachable through hierarchy, related links, collections or the schema. Record any gap as a link to add or a justified exception.
8. **Check.** `make thesaurus` must pass: every `skos:related` has its inverse; no related pair is also connected by `skos:broader`; every related pair has a notes row with a kind and justification; every concept belongs to an intended scheme; every SSSOM row has a known subject concept, an allowed SKOS predicate, a well-formed object IRI and a justification. A skipped check is a failure. Then re-run `make profiles`.
9. **Review and accept.** Check the exit criterion, log decisions in `decisions.md`, update `vocabulary/term-trace.md` and `CLAUDE.md` (open points), and report results and anything left open.

## Exit criterion (per question)

- Related links are symmetric, each with a kind and justification in the notes, and none repeats what the schema already carries.
- No related link duplicates a hierarchical path.
- Each concept belongs to an intended scheme. Isolated concepts remain where no defensible link exists, with an Exceptions line.
- Label review is recorded. Shared labels are documented or removed.
- Every external mapping uses the weakest true predicate and has a justification. Concepts with no match are recorded as such.
- `validate_skos`: 0 violations; remaining warnings reviewed and explained.
- `make thesaurus` and `make profiles` pass, with nothing skipped.

## Deliverables (updated per question)

- `vocabulary/watchline.ttl` (related links, label changes)
- `vocabulary/thesaurus-notes.md`
- `vocabulary/mappings/external.sssom.tsv` (once there is a mapping)
- `vocabulary/term-trace.md` (if concepts changed)
- `scripts/check_thesaurus.py` (first question)
- New entries in `decisions.md`

## After all questions

Consolidate across questions: one association per concept pair, consistent kinds, consistent label policy, and a single mappings file. Re-run `validate_skos`, `make thesaurus` and `make profiles`, as in the roadmap's order of work.
