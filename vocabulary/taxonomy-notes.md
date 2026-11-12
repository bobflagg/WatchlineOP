# Taxonomy notes

One section per question. Records which concepts nest, why, and which stay flat on purpose. Hierarchy links live in `watchline.ttl` only; the graph does not store them. Stage 3 procedure: `specs/stage3-procedure.md`.

## Q1

**Result: no hierarchy needed.** The vocabulary has no `skos:broader` or `skos:narrower` links and no collections. Reviewed 2026-11-12; `watchline.ttl` was not changed in this stage.

### Concepts left flat, and why

| Concepts | Reason |
| --- | --- |
| `tax-lot`, `building` | No definition says one is a kind of the other. Their relationship is `has-building`, a relationship, not a hierarchy. |
| `bbl`, `bin` | An identifier is not a kind of the thing it identifies. Top concepts by intent. |
| `address` | One concept covers lot and building addresses (Stage 1 decision). Splitting it would add two narrower concepts that no answer field distinguishes. |
| `hpd-registered`, `pluto-building-count`, `year-built`, `building-class`, `residential-units`, `assessed-total-value` | Each is a single source-reported fact about a lot. No answer groups them by kind. |
| `address-resolution-outcome`, `candidate-street-name`, `related-lot`, `in-graph` | Answer-contract terms. They relate to each other by `skos:related`, not by kind. |
| `matched-exactly`, `matched-by-variant`, `ambiguous`, `not-found`, `service-unavailable` | A flat value set in the scheme `address-resolution-outcomes`. Grouping them (for example found versus not found) would add a layer that no field or caveat uses. |

### Groupings the question asks for

| Grouping | Where it appears | Expressed as |
| --- | --- | --- |
| The characteristics of a lot (year built, building class, residential units, assessed total value) | Q1.4 | No collection. Each is read as its own field; nothing in the schema, graph or answer uses the set as a unit. Decided 2026-11-12. |
| The two building counts | Q1.2 | Not a grouping. `pluto-building-count` is a concept; the HPD count is the field `buildingsListed` (concept `building`). Both are reported, labelled by source. |

### Disjointness candidates for Stage 5

- `tax-lot` and `building`: a lot is not a building. Record as a candidate only; the decision is Stage 5's.

## Q2

**Result: no hierarchy needed.** Still no `skos:broader`, `skos:narrower` or collections. Reviewed 2026-11-12; `watchline.ttl` was not changed in this stage.

### Concepts left flat, and why

| Concepts | Reason |
| --- | --- |
| `registration`, `owner-contact` | No definition says one is a kind of the other. A registration has owner contacts; that is `has-owner-contact`, a relationship. |
| `registration`, `building` | A building has registrations (`has-registration`). A registration is not a kind of building. |
| `registration-id` | An identifier is not a kind of the thing it identifies. |
| `last-registered-date`, `registration-end-date` | Both are dates of a registration, a part-whole relation at most, not is-a. Not grouped under a broader "registration date": no answer field uses the pair as a unit. |
| `contact-type`, `owner-name` | Properties of an owner contact. Neither is a kind of the other. |
| `corporate-owner`, `individual-owner`, `joint-owner` | A flat value set in the scheme `owner-contact-types`. Grouping persons (individual, joint) apart from entities (corporate) would add a layer that no field uses, and the project does not yet say whether a joint owner is a kind of individual owner. |

### Groupings the question asks for

| Grouping | Where it appears | Expressed as |
| --- | --- | --- |
| The two registration dates | Q2.1 | No collection. Each is its own field; same reasoning as the four lot characteristics in Q1.4. |
| The three owner types as "registered owner" | Q2.2 | The scheme `owner-contact-types` is the grouping. Other HPD contact types are not in it by decision (2026-11-12). |

### Disjointness candidates for Stage 5

- `corporate-owner` and `individual-owner`: an owner contact has one type. Candidate only; the decision is Stage 5's.
- `registration` and `building`: a registration is not a building. Candidate only.

## Q3

**Result: no hierarchy needed.** Still no `skos:broader`, `skos:narrower` or collections. Reviewed 2026-11-12; `watchline.ttl` was not changed in this stage.

### Concepts left flat, and why

| Concepts | Reason |
| --- | --- |
| `deed`, `grantee` | A deed has grantees (`has-grantee`), a relationship. A grantee is a party on a deed, not a kind of owner contact, owner or entity. |
| `tax-lot`, `deed` | A lot has deeds (`has-deed`). Neither is a kind of the other. |
| `grantee`, `owner-contact` | Both are named parties, but one is a deed role and the other an HPD contact. Grouping them under "party" would suggest they are interchangeable, which the project forbids. |
| `document-id`, `document-type`, `document-date`, `recorded-date`, `document-amount` | Single source-reported facts of a deed. `document-date` and `recorded-date` are not grouped as "date"; the answer must keep them apart. |
| `document-type` | The eight deed codes are values of a property, not concepts. Not made a scheme: no answer filters or groups by kind of deed, and the type is only reported. Revisit if a question needs correction versus sale deeds. |
| `grantee-name`, `owner-name` | Properties of different parties. Neither is a kind of the other. |
| `mailing-address`, `address-line-two`, `zip-code` | Parts of an address, a part-whole relation at most. `mailing-address` is not narrower than `address`: `address` is the address of a lot or building, and a party's mailing address is not the property's. |
| `name-agreement`, `address-agreement`, `comparison-rule` | Answer-contract terms, computed at answer time. Not kinds of one another. |

### Value sets (flat by intent)

| Scheme | Values | Reason |
| --- | --- | --- |
| `name-agreement-outcomes` | `exact-normalized`, `normalization-match`, `different`, `not-comparable` | Grouping `exact-normalized` and `normalization-match` as "match" would let a reader treat both as a match finding; they carry different rules and the answer reports each with its rule. `not-comparable` is not a kind of `different`. |
| `address-agreement-outcomes` | `same`, `differs`, `address-absent` | `address-absent` is not a kind of `differs`. Same reasoning. |

### Groupings the question asks for

| Grouping | Where it appears | Expressed as |
| --- | --- | --- |
| The dates and amount of a deed | Q3.1 | No collection. Each is its own field; same reasoning as Q1.4. |
| The three agreement fields (name, address, rule) | Q3.4, Q3.5 | No collection. Each is its own answer field. |
| The address parts of a party | Q3.2, Q3.5 | No collection. The parts are separate fields on the grantee and owner contact, and the match uses two while the third is reported apart. |

### Disjointness candidates for Stage 5

- `grantee` and `owner-contact`: a deed party is not an HPD contact. Candidate only.
- `deed` and `registration`: a recorded document is not a registration. Candidate only.
