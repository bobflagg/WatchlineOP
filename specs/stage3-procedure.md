# Stage 3 procedure: taxonomy, per question

Run this for each competency question after its [stage 2](stage2-procedure.md) is accepted, one question at a time. Stage definition and exit criterion: [roadmap.md](roadmap.md#stages) (Stage 3 row, exit criterion 3) and the [taxonomy review policy](roadmap.md#taxonomy-review-policy). Tools: [tech-stack.md](tech-stack.md).

To run it in a fresh Claude Code session, start with: "Execute specs/stage3-procedure.md for QNN."

**Goal:** add broader/narrower structure only where an answer needs a hierarchy, with every link justified. A flat vocabulary is a valid result, and "no hierarchy needed" is recorded with its reason.

## Ground rules

- Read first: `CLAUDE.md` (auto-loaded), the question file, `vocabulary/watchline.ttl`, `vocabulary/term-trace.md`, `vocabulary/taxonomy-notes.md` (if it exists), this question's `profiles/` files (enums and allowed values often suggest hierarchies), `specs/decisions.md`, and the roadmap sections linked above.
- Run `validate_skos` (the `skos` MCP server) after every change to `vocabulary/`, and report its findings before moving on. Never validate by hand or claim validity without running it. Send only vocabulary files to the server.
- Concept IDs stay stable. Changing a hierarchy link or a label never changes or reuses an ID.
- Hierarchy is not ontology. Do not turn broader/narrower links into subclass axioms, and do not declare sibling disjointness here; both are Stage 5 decisions.
- A hierarchy exists for the agent and the answer, not for tidiness. The graph does not store hierarchy links; they live in the vocabulary only.
- Do not invent structure to silence a validator warning. Do not commit to Git unless asked. Stop and ask when a decision is unsettled.

## One-time setup (first question only)

Confirm with the user, then log in [decisions.md](decisions.md):

- **File layout:** keep hierarchies in `vocabulary/watchline.ttl`. Give a code list its own `skos:ConceptScheme` only when it is a standalone value set (as the address resolution outcomes are).
- **Notes file:** create `vocabulary/taxonomy-notes.md`, one section per hierarchy branch or grouping, recording: its meaning, each link's justification, intentional exceptions, and disjointness candidates for Stage 5. Also list the concepts left flat on purpose, with the reason.
- **Grouping without hierarchy:** use `skos:Collection` for groupings that fail the is-a test (for example a set of fields the question asks for together).
- **Check script:** `scripts/check_taxonomy.py` (`rdflib`) behind `make taxonomy`, added when the first question has a link or collection to check. Until then the stage records "no hierarchy needed" and `make taxonomy` stays a stub. The script fails nonzero if: a `skos:broader` cycle exists; a broader/narrower endpoint is missing or outside its scheme without a note; a link or collection has no entry in `taxonomy-notes.md`; a branch mixes hierarchy meanings without a note. A skipped check is a failure. `validate_skos` stays the authority on SKOS validity.

## Per-question steps

1. **Find the candidates.** From the question, its sub-questions, the `term-trace.md` and the enums in `profiles/qNN.yaml`, list:
   - value sets (an outcome scheme, a class code list) that might nest;
   - groupings the question asks for together ("the characteristics of a lot");
   - concepts whose definitions say they are a kind of another concept.

   For each, decide whether an answer or the agent's retrieval needs the structure. If not, leave it flat and record why. Most concepts stay flat.
2. **Fix the meaning of each hierarchy.** Default is is-a (kind-of). If a source scheme organizes concepts by part-whole or another documented relation, state that meaning and do not mix meanings within a branch. Severity order and workflow sequence alone never justify broader/narrower. A role a thing plays in one answer, and an identifier of a thing, are not kinds of that thing.
3. **Prefer the source's own structure.** If the source (a code table, a data dictionary) groups its codes, follow that grouping and cite it with `dct:source`. Otherwise derive the structure from the concept definitions. Do not invent groupings.
4. **Add the links.** Follow the file's existing convention for broader/narrower (check before adding). Prefer shallow hierarchies with no fixed depth. Multiple parents and overlapping siblings are allowed when each link is valid. Set top concepts for each scheme. Use collections for non-hierarchical groupings.
5. **Review existing links.** Re-test every existing broader link on this question's concepts with the is-a test. Fix, replace with a collection or a related link, or justify.
6. **Run `validate_skos` and review.** Treat orphan, cycle, multiple-parent and disconnected-concept warnings as prompts for review in context. Resolve real problems. For each intentional exception, write a one-line explanation in `taxonomy-notes.md`.
7. **Pilot the groupings.** Confirm each grouping the question needs can be expressed through the hierarchy or a collection. Record a grouping-to-concept table in `taxonomy-notes.md`. If the question needs none, record "no hierarchy needed" with the reason.
8. **Re-run the earlier checks.** `make profiles` must still pass (the schema references concept IRIs), then `make taxonomy` once it exists.
9. **Review and accept.** Check the exit criterion, log decisions in `decisions.md`, update `vocabulary/term-trace.md` and `CLAUDE.md` (open points), and report results and anything left open.

## Exit criterion (per question)

- Every broader/narrower link and collection has a stated meaning and a justification in `taxonomy-notes.md`.
- Multiple parents are valid link by link. Sibling disjointness is not assumed.
- Hierarchies are shallow unless depth is justified. Cycles and mixed meanings are resolved or explained.
- `validate_skos`: 0 violations; every remaining warning is reviewed and, if kept, explained in one line.
- No SKOS link is translated into an ontology axiom.
- Concepts left flat are flat by intent, listed in the notes.
- `make profiles` passes, and `make taxonomy` passes once it exists, with nothing skipped.

## Deliverables (updated per question)

- `vocabulary/watchline.ttl` (hierarchies, collections, if any)
- `vocabulary/taxonomy-notes.md`
- `vocabulary/term-trace.md` (if concepts changed)
- `scripts/check_taxonomy.py` (first question that has links or collections)
- New entries in `decisions.md`

## After all questions

Consolidate the taxonomy across questions, check that the same concept has one place in the hierarchy, and re-run `validate_skos`, `make profiles` and `make taxonomy`, as in the roadmap's order of work.
