# Thesaurus notes

Stage 4 record for `vocabulary/watchline.ttl`. Prefix `vocab:` is `https://watchline.example/vocab/`. Procedure: [stage4-procedure.md](../specs/stage4-procedure.md); policy: [taxonomy review policy](../specs/roadmap.md#taxonomy-review-policy).

`scripts/check_thesaurus.py` (`make thesaurus`) reads the **Related links** table and the **Association kinds** list below. Each row is `| concept | concept | kind | justification |`, concepts as backticked slugs, each unordered pair once. In the file every pair is written in both directions with plain `skos:related`; the kind lives only here (ISO 25964 style). A related link is an association, not a hierarchy and not equivalence.

## Association kinds

- `identifier-of`: the identifier and the thing it identifies.
- `output-of`: a result and the act or classification that produces it.
- `input-to`: a thing used by a process or classification.
- `source-of`: a record, code or document that evidences or supplies another concept.
- `contrasts-with`: look-alike concepts the question insists on keeping apart.
- `same-subject-different-role`: the same real-world thing in a different role.
- `tally-of`: a reported count and what it counts or draws on.
- `part-of`: a component and its whole (not a hierarchy here).
- `characteristic-of`: a kind of characteristic and the thing it describes.
- `qualifies`: a code that refines another code.

## Related links

| Concept | Concept | Kind | Justification |
| --- | --- | --- | --- |
| `bbl` | `tax-lot` | identifier-of | The BBL identifies a tax lot; it is not the lot. (Stage 1 link.) |
| `bin` | `building` | identifier-of | The BIN identifies a building; it is not the building. (Stage 1 link.) |
| `addressed-building` | `building` | same-subject-different-role | The addressed building is a building playing a role in one answer. (Stage 1 link, kept as related at Stage 3.) |
| `address-resolution` | `address-resolution-outcome` | output-of | The outcome classifies the result of a resolution. (Stage 1 link.) |
| `street-name-variant` | `matched-by-variant` | contrasts-with | Scope notes insist these differ: a spelling of one street name versus the classification of a whole resolution. (Stage 1 link.) |
| `hpd-registration` | `bin` | source-of | In Q1 an HPD registration is the only source of BINs. (Stage 1 link.) |
| `unit-count` | `residential-units` | tally-of | The tally given in an answer versus the source characteristic it draws on. (Stage 1 link.) |
| `tax-lot` | `building` | contrasts-with | Q1 requires that a lot is not necessarily one building; lot and building counts differ. |
| `source-record` | `source-snapshot` | part-of | A record is a row of a snapshot. Whole-part, not is-a, so not a hierarchy. |
| `address-candidate` | `ambiguous` | output-of | Candidates are what an ambiguous outcome returns instead of a chosen lot. |
| `inferred-resolution` | `alternate-address` | input-to | An inferred resolution is reached through an alternate address. |
| `geosupport-return-code` | `address-resolution` | source-of | The return code is service evidence of how a resolution went. |
| `geosupport-reason-code` | `address-resolution` | source-of | The reason code is service evidence qualifying a resolution. |
| `geosupport-return-code` | `geosupport-reason-code` | qualifies | The reason code qualifies the return code; the two are kept separate. |
| `geosupport-return-code` | `address-resolution-outcome` | input-to | The outcome is decided from the return code (never message text). |
| `street-address` | `address-resolution` | input-to | An input street address is what a resolution maps to a tax lot. |
| `hpd-registration` | `building` | source-of | A registration is how a building is known in Q1. |
| `source-reported-characteristic` | `tax-lot` | characteristic-of | Characteristics are stated about a tax lot (residential units are lot-wide). |
| `source-reported-characteristic` | `building` | characteristic-of | Characteristics may also be stated about a building. |
| `parcel-count` | `tax-lot` | tally-of | The counting unit of a parcel count is the tax lot. |
| `building-count` | `building` | tally-of | The counting unit of a building count is the building. |
| `source-reported-characteristic` | `source-record` | source-of | Each characteristic value is tied to the source record it came from. |

## Labels

All alternative labels were checked against every label in the vocabulary. No label is shared by two concepts.

| Label | Concept | Decision |
| --- | --- | --- |
| `parcel`, `lot` | `tax-lot` | Kept as alternative labels. `parcel` was decided 2026-11-11; `lot` is the specs' own shorthand. Neither collides with another label (`parcel count` is a different concept). `lot` is also the last component of a BBL, which is not a concept here. |
| `structure` | `building` | Moved to a hidden label. Too generic to display (lot improvements, constructions). Still finds `building` in search. |
| `address` | `street-address` | Moved to a hidden label. Q2 adds business and registered addresses, so a bare "address" would become ambiguous. Still finds the concept in search. |
| `apartments` | `residential-units` | Moved to a hidden label. Colloquial and easily read as a kind of building. Still finds the concept in search. |
| `borough-block-lot`, `building identification number`, `GRC`, `construction year`, `dwelling units`, `assessed total value`, `input address`, `match outcome`, `no match` | various | Reviewed; unambiguous, kept. `no match` (alt of `not found`) is not an outcome of its own. |

The label changes alter no concept ID.

## External mappings

Schemes checked, definitions read: schema.org, PROV-O, W3C ORG. Wikidata was not chosen. The SSSOM file `mappings/external.sssom.tsv` is the record.

| Concept | Result |
| --- | --- |
| `street-address` | `skos:closeMatch` schema:PostalAddress (not exact: a mailing address need not name a place; ours has no postal code). |
| `source-snapshot`, `source-record` | `skos:broadMatch` prov:Entity. Not closer: PROV-O has no snapshot or record term. `prov:Collection` was considered for a snapshot and rejected (a snapshot is a version of a dataset, not defined as a collection of constituents here). |
| `alternate-address` | None found in schema.org. |
| All other concepts | None found in schema.org, PROV-O or W3C ORG. ORG has `org:Site` and `org:siteAddress` but no term for a building, tax lot, BBL, BIN or source record. ORG becomes relevant from Q2. |

## Exceptions

- `matched-exactly`: no related link; it is a value of the outcome scheme, reachable through that scheme.
- `not-found`: no related link; as `matched-exactly`.
- `year-built`, `building-class`, `assessed-value`, `residential-units` (apart from `unit-count`): no direct related link; each is reached through its parent `source-reported-characteristic`.
- `address-resolution-outcome` to its four values: not linked with related; the scheme carries that relation.
- `street-address` and `street-name-variant`: not linked directly; the variant concept is reached through `matched-by-variant`. No defensible extra association.
