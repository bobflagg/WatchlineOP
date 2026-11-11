# Competency questions

There are 28 questions the graph and its downstream research agent must support each stated with details and examples in its own file in [questions/](questions/). They drive the ontology and become the evaluation dataset. Each question declares its `acceptance_types`; graph readiness and full question acceptance are tracked separately as defined in [the roadmap](roadmap.md#acceptance-types-and-responsibility).  The count is a result of coverage, not a target: a question was added when a need cannot be tested by the existing ones.  The graph consumes [BOR](dependencies.md#bor-beneficial-owner-resolution)'s output and [BOR](dependencies.md#bor-beneficial-owner-resolution) will export edge-level evidence.
 
Each question file contians a real example on a neutral building, the shape of the answer, who asks it and why, and the sources needed to answer it.

For each question there is reliability its answer can reach: **I** (recorded assertion: a public record states it, or it follows from joining records on an official identifier), **II** (derived conclusion: a method links or classifies where the records do not say so), or **I+II** (a recorded chain with derived links).

## Vocabulary used in the questions

Working terms, to be settled when building the controlled vocabulary. They follow the layers BOR already implements.

| Term | Meaning | Reliability |
| --- | --- | --- |
| **Title / registration facts** | Who a deed conveys to (ACRIS); who HPD lists as owner, agent or contact (HPD); what DOS records for an entity | I |
| **Management relationship** | A building's *disclosed* managing agent (`MANAGED_BY`). A relationship, not a grouping and not a rung in an ownership hierarchy | I |
| **Operational Network** | Buildings that connect through registration infrastructure: shared names, business addresses or resolved identities, with aggregator addresses masked. Connected components; components over 300 lots are cut into communities by Louvain | II |
| **Owner Portfolio** | Buildings *attributed* to one apparent owner from ownership signals only: resolved shared identity, or a qualifying shared deed. BOR also calls it the Owner Portfolio (it was a "beneficial owner group" before 2026-10-21). Connected components of those edges; co-op/condo buildings are excluded | II |

Two cautions apply to the last two terms in every answer. Both are derived partitions, so each is a lead to verify, never a finding of legal ownership. And a group's "person anchor" in BOR's export is a display choice, not a named owner.

## How the examples were chosen

- **Neutral buildings.** Ordinary rental buildings in one Brooklyn neighborhood (Sunset Park), picked by querying the data. They are not landlords from the news, and this file does not repeat individuals' names, to keep the examples neutral. Where a record names a person, the block says "a person (name not repeated)". The agent shows names with their role and source.
- **Expected-answer authority.** The frozen local JustFix/WoW PostgreSQL snapshot is the sole authority for database-backed graph test inputs and expected answers. Newer public records do not override the chosen snapshot or determine whether its graph tests pass. Differences from newer records are coverage or freshness limits, not test failures.
- **Snapshot identity and dates.** Record the frozen snapshot identifier and checksum, the source tables/releases used, and the query parameters and as-of date for each fixture. Tables can cover different periods; a database query date is not an upstream publication or coverage date. See [the expected-answer policy](roadmap.md#expected-answer-policy).
- **Example status.** All examples remain provisional acceptance fixtures until verified against the chosen frozen evidence and assigned a fixture version. The per-question local checks dated 2026-11-10 are useful observations, not a frozen baseline by themselves. Preserve their values and dates; do not refresh them from live services. Items marked **pending** still need evidence.
- **Other evidence.** Derived-layer fixtures use a separately pinned BOR/NLR release and its manifest/checksums. Retrieval/extraction and investigation fixtures use versioned cached documents, pages, or service responses. Their results do not silently replace database-backed facts.

### Anchor properties

| Short name | Address | BBL | What it is |
| --- | --- | --- | --- |
| **A** | 5413 7 Avenue, Brooklyn | `3008260002` | Class C1, 32 residential units, 1 building (BIN `3014788`), built 1911. HPD registration `316103`, owner `5413 PLAZA LLC`, last registered 2025-09-30, period ends 2026-09-01 |
| **B** | 702 54 Street, Brooklyn | `3008260005` | Class C7, 39 units, BIN `3014789`. HPD registration `300258`, owner `702 Plaza LLC`, last registered 2025-10-24 |
| **C** | 438 52 Street, Brooklyn | `3008070024` | Class C1, 32 units, BIN `3013901`, built 1931. A co-op: PLUTO owner `438 52ND ST OWNERS CORP`. HPD registration `350423` |
| **D** | 218, 220 and 224 54 Street, Brooklyn | `3008210012` | One lot, 3 buildings, 18 units, each registered separately with HPD: 218 (BIN `3324448`, registration `302437`), 220 (BIN `3324450`, `344220`), 224 (BIN `3324451`, `331116`). Owner is a housing development fund company |
| **E** | 234 54 Street, Brooklyn | `3008210019` | 6 units. Last registered 2020-08-31, period ended 2021-09-01, but a deed was recorded 2026-04-21 |
| **F** | 259 22 Street, Brooklyn | `3008970014` | 40 units, built 2025, class D7. No HPD registration found |
| **G** | 548 52 Street, Brooklyn | `3008080025` | Class C1, 23 units. HPD owner spelled `KS Turnpike LLC`, deed and DOS spell it `K S TURNPIKE LLC` |

A and B are linked by records: the same business address in HPD (a street address in Brooklyn, 11220), a joint mortgage, and DOS filings one day apart. That is the trail used for Q7, Q11 and Q20. The records do not say the two are owned together, and the examples do not assert it.

