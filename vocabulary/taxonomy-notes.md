# Taxonomy notes

Stage 3 record for `vocabulary/watchline.ttl`. One section per hierarchy branch. Prefix `vocab:` is `https://watchline.example/vocab/`. Policy: [taxonomy review policy](../specs/roadmap.md#taxonomy-review-policy); procedure: [stage3-procedure.md](../specs/stage3-procedure.md).

`scripts/check_taxonomy.py` (`make taxonomy`) reads the **Links** tables below. Each row is `| child | parent | meaning | justification |`, with child and parent as backticked concept slugs. Every `skos:broader` link in the vocabulary needs exactly one row. Sections titled **Exceptions** hold one line per intentional exception, naming the concept slug.

Hierarchy here is not ontology. No link becomes a subclass axiom, and no sibling disjointness is declared (Stage 5 decisions).

## Branch: street address (Q1.1, Q1.3)

Meaning: **is-a** (a kind of street address).

| Child | Parent | Meaning | Justification |
| --- | --- | --- | --- |
| `alternate-address` | `street-address` | is-a | Every alternate address is a street address. It is defined by its form (a street-name variant or corner address under which the lot is recorded), not by a role in one answer. |

### Exceptions

- `street-address` scope note calls an *input address* a role. That role is not a concept in the vocabulary and has no link.

## Branch: source-reported characteristic (Q1.4)

Meaning: **is-a** (a kind of characteristic that a source states about a tax lot or building). The four children are the characteristics Q1 asks for. They are kinds of characteristic, not values and not columns.

| Child | Parent | Meaning | Justification |
| --- | --- | --- | --- |
| `year-built` | `source-reported-characteristic` | is-a | A year of construction as a source states it is a source-stated property of a lot or building. |
| `building-class` | `source-reported-characteristic` | is-a | The city's use/type class code as a source states it is a source-stated property. |
| `residential-units` | `source-reported-characteristic` | is-a | The residential unit total as a source states it is a source-stated property (lot-wide). |
| `assessed-value` | `source-reported-characteristic` | is-a | The city's total assessed value as a source states it is a source-stated property. |

### Exceptions

- None. No concept has a second parent. The children are not exclusive of each other and no disjointness is claimed.

## Branch: reported count (Q1.2, Q1.4)

Meaning: **is-a** (a kind of tally, distinguished by its counting unit). The children differ only in the unit counted, so they are siblings by unit and are never converted into one another.

| Child | Parent | Meaning | Justification |
| --- | --- | --- | --- |
| `parcel-count` | `reported-count` | is-a | A tally whose counting unit is the tax lot. |
| `building-count` | `reported-count` | is-a | A tally whose counting unit is the building. |
| `unit-count` | `reported-count` | is-a | A tally whose counting unit is the residential unit. |

### Exceptions

- `unit-count` is `skos:related` to `residential-units` (a different branch). The count is the answer tally, the characteristic is the source value. This is an association, not a hierarchy.

## Concepts left without hierarchy, by intent

| Concept(s) | Reason |
| --- | --- |
| `bbl`, `bin` | Top concepts on purpose. An identifier is not a kind of its subject (tax lot, building). Each is `skos:related` to its subject. |
| `addressed-building` | Stage 1 had `skos:broader building`. Its scope note says it is a role a building plays in one answer, not a kind of building, so the is-a test fails. Stage 3 replaced the link with `skos:related building` and made it a top concept (decided 2026-11-11). The ID is unchanged. |
| `matched-exactly`, `matched-by-variant`, `ambiguous`, `not-found` | Flat value set in its own scheme (`address-resolution-outcomes`). Q1 needs one outcome per resolution and no grouping of outcomes. Do not group "matched" outcomes under a parent merely because two of them resolve a lot. |
| `geosupport-return-code`, `geosupport-reason-code` | Separate concepts, not a hierarchy. Q1 classifies by code, but the individual code values are not minted as concepts, so there is nothing to nest. Revisit if a later question mints code values. |
| `tax-lot`, `building`, `address-resolution`, `address-resolution-outcome`, `address-candidate`, `street-name-variant`, `hpd-registration`, `inferred-resolution`, `source-snapshot`, `source-record` | Different kinds of thing, no is-a between them. Related links already carry the associations. |
| Building class codes (PLUTO `bldgclass`) | Q1 reports the code as a recorded value. It does not group by class family, so the source code list is not minted or nested. Revisit when a question needs "all residential buildings" or similar. |

## Grouping-to-concept table (pilot)

Each grouping Q1 needs, and how the vocabulary expresses it.

| Grouping the question needs | Expressed by |
| --- | --- |
| The four characteristics asked for in Q1.4 | Narrower concepts of `source-reported-characteristic` |
| Parcel, building and unit tallies, each with its unit | Narrower concepts of `reported-count` |
| The four resolution outcomes | Top concepts of the `address-resolution-outcomes` scheme |
| Input address versus the address under which the lot was found | `street-address` and its narrower `alternate-address` |
| Addressed building versus other buildings on the lot | Role concept `addressed-building` (related to `building`), not a hierarchy |

## Disjointness candidates for Stage 5

Recorded only. Not declared here and not implied by sibling placement.

- `parcel-count`, `building-count`, `unit-count`: differ by counting unit, never converted. A candidate for pairwise distinctness.
- `tax-lot` and `building`: Q1 treats them as different things (a lot is not necessarily one building). A candidate to confirm in Stage 5.
- `bbl` and `bin`: identifiers of different things.
