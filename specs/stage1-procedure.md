# Stage 1 procedure: question, terms and the smallest graph, per question

Run this for each competency question, one at a time. Stage definition and exit criterion: [roadmap.md](roadmap.md#stages). Tools: [tech-stack.md](tech-stack.md).

Each sub-question is worked end to end on the smallest graph that answers it, and the vocabulary is built from the terms that survive.

## Principles

1. **Smallest graph that answers the sub-question.** A node, property or relationship exists only because an answer needs it. Prefer a property to a node, and a node to a relationship chain.
2. **The goal is a better agent answer**, not a faithful copy of the source. If the agent can get something from a tool, the contract or a definition, it stays out of the graph.
3. **Dataset-level provenance by default.** The graph is built from one frozen snapshot, so source, release and date are recorded once (`data/sources.yaml`, `data/README.md`), not per record. Instance-level evidence (a source record, snapshot or document node) is used only for derived edges, claims, documents and cached responses, which have no row in the snapshot to point to.
4. **Caveats live in definitions and property descriptions**, and the answer contract says which ones to repeat.
5. **Prove it on data before modeling it.** Profile the source first. Every sub-question gets expected-answer SQL and a check that re-derives each fixture from the source.
6. **Disagreement between sources is reported, not reconciled.** Show both values labelled by source.

## One-time setup (first question only)

- Record the base IRIs for concepts, ontology elements and instances. Choose the concept ID style (readable or opaque); IDs stay stable once minted.
- Fix the layout: `vocabulary/watchline.ttl`, `data/sources.yaml`, one `tests/qN_M/` folder per sub-question, loaders in `scripts/`.
- Freeze the source (dump ID, checksum, date) and set the scope rule (for Q1: the rental market, meaning HPD-registered lots plus unregistered lots with 3 or more residential units).
- Run `validate_skos` on a tiny file to confirm the tool works. Log each choice in [decisions.md](decisions.md).

## Per-question steps

1. **Clean up the question (CLaRO-style).** Split compound questions into atomic sub-questions. Remove identifiers, source names and implementation detail from the text. Surface hidden assumptions (lot-level versus building-level values, which source decides). Keep the original sentence as the parent; number the parts `Qn.1`, `Qn.2` in a "Sub-questions" table in the question file. The parent passes when all parts pass.
2. **Mine candidate terms** from the sub-question, answer requirements, caveats, worked examples and source columns.
3. **Tag every term with where it lives**: node, property, relationship, tool output, answer contract, or not needed. Only the first three enter the graph. A term tagged "not needed" is dropped, not parked. Reuse an existing concept when its meaning fits; never reuse an identifier for a different meaning.
4. **Profile the source for each term that enters the graph.** Check counts, nulls, zeros, placeholders, duplicates, ties and format, on the scoped rows. Write down what each odd value means and decide per case: absent, kept as recorded, or excluded. Record the decision and the counts.
5. **Define sources and scope.** Name each source in `data/sources.yaml` with its key, grain, caveats and date. For a service that is not in the database (Geosupport), record the pinned version and keep recorded responses as test inputs.
6. **Choose the answer contract.** List the fields the agent returns for the sub-question, including outcomes such as exact, variant, ambiguous, not found or unavailable. An outage is never an answer about the data.
7. **Write the test before the loader.** For each sub-question create `tests/qN_M/` with:
   - `expected.sql`: the answer derived from the frozen source, independent of the graph.
   - `lookup.cypher`: the query the agent would run.
   - `fixtures.yaml`: anchor examples plus an edge case for every odd value found in step 4, and one out-of-scope case that must be absent.
   - `check_*.py`: re-derives each fixture from the source (so a stale fixture fails), compares the graph, and reconciles totals. Any error counts as a failure.
8. **Load and run.** Write an idempotent loader (`MERGE` on the key, guarded to the POC database, source read-only). Run it, then the check. Fix the loader, the fixture or the rule, whichever is wrong, and log what changed. If the first run reveals a data issue, go back to step 4.
9. **Draft the vocabulary for the surviving terms.** Preferred label, definition and scope note, plus alternative labels. Put the caveats from step 4 into the definitions. Controlled values go in their own concept scheme. The vocabulary is the single source of definitions: node and property descriptions in the graph schema are generated from concept definitions and scope notes, never written separately, so the two cannot drift apart. Run `validate_skos` and explain each intentional exception.
10. **Pilot restatement.** Restate the question, its sub-questions and worked examples using only approved terms; close any gaps.
11. **Review.** Check the exit criterion, log decisions, and update the term trace table.

## Exit criterion (per question)

- Every sub-question has a passing check on the frozen source: fixtures re-derived from SQL, graph matching, totals reconciled.
- Every term the graph uses is tagged, defined and resolves to an approved concept; every other term is tagged "not needed" or lives elsewhere.
- Each concept has at most one preferred label per language; look-alike terms are distinguished.
- Each odd source value has a recorded rule, a count and a fixture.
- `validate_skos` warnings are resolved or explained; the pilot restatement has no gaps.

## Deliverables (updated per question)

- `tests/qN_M/` per sub-question, and the loaders in `scripts/`
- `vocabulary/watchline.ttl` and the term trace table
- Graph schema descriptions generated from the vocabulary (Stage 6 uses them)
- Source and scope entries in `data/sources.yaml`; new entries in `decisions.md`

## Worked example: Q1

"Which tax lot does this address resolve to?" splits into four sub-questions (lot, buildings, outcome, characteristics) and needs a graph of two node labels and one relationship:

- `Lot {bbl, address, hpdRegistered, plutoNumBuildings, yearBuilt, buildingClass, unitsRes, assessedTotal}`
- `Building {bin, address}` and `(:Lot)-[:HAS_BUILDING]->(:Building)`
- Address resolution is a tool (Geosupport) plus an answer contract `{outcome, bbl, bin, inGraph, relatedLots, candidates}`; nothing about it is stored in the graph.

Findings and the rules they set:

| Finding | Rule it produced |
| --- | --- |
| The graph comes from one frozen snapshot, so per-record snapshot edges and source-record nodes would add nothing | Dataset-level provenance by default (principle 3) |
| PLUTO covers every lot; the question is about the rental market | Scope from the question's domain; HPD registrations decide the lot set |
| `registrationid` repeats; registrations tie on date and disagree on address | Most recent wins; if tied registrations disagree the value is absent, never picked |
| Placeholder BINs (`x000000`) and one BIN on two lots | Placeholders excluded and counted; shared BINs kept and surfaced as `relatedLots` |
| PLUTO year built `0`, blank class, `0` units, `0` assessed value | `0` year and blank class are absent; `0` units and `0` value kept as recorded, defined as "PLUTO records none" |
| PLUTO and HPD disagree on building counts for about 14% of registered lots (17 Battery Place: 2 vs 1) | Report both counts, labelled by source |
| A condominium returns the billing lot; its unit lot has a different BIN | Documented limit of `relatedLots` |
| Geosupport decides exact vs variant, and a service outage looks like "not found" | Classify from the recorded response; `unavailable` is its own outcome |
| Data problems show up when a sub-question is loaded and checked against the source | Prove each sub-question end to end (steps 7 and 8) before drafting the vocabulary |

## After all questions

Consolidate the vocabulary and re-run validation across it, as in the roadmap's order of work.
