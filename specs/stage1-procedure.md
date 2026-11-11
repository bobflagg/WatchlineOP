# Stage 1 procedure: controlled vocabulary, per question

Run this for each competency question, one at a time, as the roadmap's "one question at a time" principle requires. Stage definition and exit criterion: [roadmap.md](roadmap.md#stages). Tools: [tech-stack.md](tech-stack.md).

## One-time setup (first question only)

- Record the base IRIs for concepts, ontology elements and instances.
- Choose the concept ID style (readable or opaque). IDs stay stable once minted.
- Fix the file layout: `vocabulary/watchline.ttl` for the POC.
- Run `validate_skos` on a tiny file to confirm the tool works.
- Log each choice in [decisions.md](decisions.md).

## Per-question steps

1. **Clean up the question (CLaRO-style).**
   - Split compound questions into atomic sub-questions.
   - Remove identifiers, source names and implementation detail from the question text. They belong in the vocabulary and the answer requirements.
   - Surface hidden assumptions, such as lot-level versus building-level values.
   - Keep the original sentence as the parent. If split, number the parts `Qn.1`, `Qn.2`, and so on, in a "Sub-questions" table in the question file. The parent keeps its ID and passes when all parts pass. A question that is already atomic needs no split.
2. **Mine candidate terms.** Sources: the cleaned questions, answer requirements, caveats, worked examples, and the source column names. List each candidate with where it appears.
3. **Reuse before minting.** Check the existing vocabulary. Reuse a concept when its meaning fits. Mint a new one only when no existing concept does, and do not reuse an identifier for a different meaning.
4. **Reconcile synonyms and homonyms.** Settle preferred labels, alternative labels and distinctions between look-alike terms (for example owner, registrant, grantee).
5. **Draft concepts.** Give each one a preferred label, a definition and a scope note, plus alternative labels where needed. Put controlled values in their own concept scheme.
6. **Validate.** Run `validate_skos`. Review warnings in context, per the [taxonomy review policy](roadmap.md#taxonomy-review-policy), and write a one-line reason for each intentional exception.
7. **Pilot test.** Restate the question, its sub-questions and its worked examples using only approved terms. Record a phrase-to-concept table and close any gaps.
8. **Review and accept.** Check the exit criterion below, log new decisions, and update the term-to-question trace table.

## Exit criterion (per question)

- Every domain term in the question resolves to an approved concept.
- Each concept has at most one preferred label per language.
- Preferred labels distinguish concepts, or an ambiguity is qualified or documented.
- `validate_skos` warnings are resolved or explained.
- The pilot restatement has no gaps.

## Deliverables (updated per question)

- `vocabulary/watchline.ttl`
- Term-to-question trace table
- Pilot table for the question
- New entries in `decisions.md`

## After all questions

Consolidate the vocabulary and re-run validation across it, as in the roadmap's order of work.
