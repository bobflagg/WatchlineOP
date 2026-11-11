# Stage 3 procedure: taxonomy, per question

Run this for each competency question after its [stage 2](stage2-procedure.md) is accepted, one question at a time. Stage definition and exit criterion: [roadmap.md](roadmap.md#stages) (Stage 3 row, exit criterion 3) and the [taxonomy review policy](roadmap.md#taxonomy-review-policy). Tools: [tech-stack.md](tech-stack.md).

To run it in a fresh Claude Code session, start with: "Execute specs/stage3-procedure.md for QNN."

**Goal:** add broader/narrower structure only where the question needs a hierarchy, with every link justified. Flat vocabulary is a valid result.

## Ground rules

- Read first: `CLAUDE.md` (auto-loaded), the question file, `vocabulary/watchline.ttl`, `vocabulary/term-trace.md`, `vocabulary/taxonomy-notes.md` (if it exists), this question's `profiles/` files (code lists and allowed values often suggest hierarchies), `specs/decisions.md`, and the roadmap sections linked above.
- Run `validate_skos` (the `skos` MCP server) after every change to `vocabulary/`, and report its findings before moving on. Never validate by hand or claim validity without running it. Send only vocabulary files to the server.
- Concept IDs stay stable. Changing a hierarchy link or a label never changes or reuses an ID.
- Hierarchy is not ontology. Do not turn broader/narrower links into subclass axioms, and do not declare sibling disjointness here; both are Stage 5 decisions.
- Do not invent structure to silence a validator warning. Do not commit to Git unless asked. Stop and ask when a decision is unsettled.

## One-time setup (first question only)

Confirm with the user (recommended defaults apply if they say "go"), then log in [decisions.md](decisions.md):

- **File layout:** keep hierarchies in `vocabulary/watchline.ttl`. Give a code list its own `skos:ConceptScheme` only when it is a standalone value set (as the address resolution outcomes are). This settles the open "one file or one per scheme" question for the POC.
- **Notes file:** create `vocabulary/taxonomy-notes.md`, one section per hierarchy branch, recording: the hierarchy's meaning, each link's justification, intentional exceptions, and disjointness candidates for Stage 5.
- **Grouping without hierarchy:** use `skos:Collection` for groupings that fail the is-a test (for example a set of related values with no kind-of relation).
- **Check script:** add `scripts/check_taxonomy.py` (`rdflib`) and implement `make taxonomy`. It fails nonzero if: a `skos:broader` cycle exists; a broader/narrower endpoint is missing or outside the intended scheme without a note; a broader link has no justification entry in `taxonomy-notes.md`; a concept has more than one hierarchy meaning in one branch without a note. A skipped check is a failure. `validate_skos` stays the authority on SKOS validity.

## Per-question steps

1. **Find the candidates.** From the question, its answer shape and its profiles, list the code lists and value sets (party roles, document types, violation classes, complaint types, case types, stop reasons, absence reasons) and any grouping the question asks for ("all financing documents"). Add the `skos:broader` links Stage 1 already made for this question's concepts. For each candidate decide: does the question need a hierarchy to answer it? If not, leave it flat and record why. Not every source code list needs a hierarchy.
2. **Fix the meaning of each hierarchy.** Default is is-a (kind-of). If a source scheme organizes concepts by part-whole or another documented relation, state that meaning explicitly and do not mix meanings within a branch. Severity order and workflow sequence alone never justify broader/narrower.
3. **Prefer the source's own structure.** If the source scheme (a code table, a data dictionary) groups its codes, follow that grouping and cite it with `dct:source`. Otherwise derive the structure from the concept definitions. Do not invent groupings.
4. **Add the links.** Follow the file's existing convention for broader/narrower (check before adding). Prefer shallow hierarchies with no fixed depth; add depth only when it helps the question or the source classification. Multiple parents and overlapping siblings are allowed when each link is valid. Set top concepts for each scheme. Use collections for non-hierarchical groupings.
5. **Review Stage 1 links.** Re-test every existing broader link for this question's concepts with the is-a test, including any whose scope note says the concept is a role or an instance type. Fix, replace with a collection or related link, or justify.
6. **Run `validate_skos` and review.** Treat orphan, cycle, multiple-parent and disconnected-concept warnings as prompts for review in context. Resolve real problems. For each intentional exception, write a one-line explanation in `taxonomy-notes.md`.
7. **Pilot the groupings.** Confirm each grouping the question needs can be expressed through the hierarchy or a collection. Record a grouping-to-concept table in `taxonomy-notes.md`. If the question needs no hierarchy, record "no hierarchy needed" with the reason.
8. **Re-run the earlier checks.** `make profiles` must still pass (profiles reference concept IRIs), then `make taxonomy`.
9. **Review and accept.** Check the exit criterion below, log decisions in `decisions.md`, update `vocabulary/term-trace.md` and `CLAUDE.md` (open points), and report results and anything left open.

## Exit criterion (per question)

- Every broader/narrower link has a stated hierarchical meaning and a justification in `taxonomy-notes.md`.
- Multiple parents are valid link by link. Sibling disjointness is not assumed.
- Hierarchies are shallow unless depth is justified. Cycles and mixed meanings are resolved or explained.
- `validate_skos`: 0 violations; every remaining warning is reviewed and, if kept, explained in one line.
- No SKOS link is translated into an ontology axiom.
- Concepts left flat or isolated are flat by intent.
- `make profiles` and `make taxonomy` pass, with nothing skipped.

## Deliverables (updated per question)

- `vocabulary/watchline.ttl` (hierarchies, collections)
- `vocabulary/taxonomy-notes.md`
- `vocabulary/term-trace.md`
- `scripts/check_taxonomy.py` (first question)
- New entries in `decisions.md`

## Carry-over from Q1

Review these Stage 1 links when running this procedure for Q1:

- `addressed-building` is `skos:broader building`, but its scope note calls it a role a building plays in one answer, not a kind of building. Test it, then keep, replace or justify.
- The four characteristics (`year-built`, `building-class`, `residential-units`, `assessed-value`) under `source-reported-characteristic`, and the count concepts under `reported-count`, need a stated meaning (kinds of characteristic or count).
- `bbl` and `bin` are top concepts on purpose (an identifier is not a kind of its subject). Record that in the notes.
- The outcome values in the address resolution outcomes scheme are a flat value set unless the question needs grouping. Say so in the notes.

## After all questions

Consolidate the taxonomy across questions, check that the same concept has one place in the hierarchy, and re-run `validate_skos`, `make profiles` and `make taxonomy`, as in the roadmap's order of work.
