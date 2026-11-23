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
| `registration`, `owner-contact` | No definition says one is a kind of the other. A registration has owner contacts; that is `has-contact`, a relationship. |
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

## Q4

**Result: no hierarchy needed.** Still no `skos:broader`, `skos:narrower` or collections. Reviewed 2026-11-12; `watchline.ttl` was not changed in this stage.

### Concepts left flat, and why

| Concepts | Reason |
| --- | --- |
| `contact`, `registration` | A registration has contacts (`has-contact`), a relationship. |
| `contact-type` | One property of `contact`; its values are all nine types in `contact-types`, which `owner-contact-types` and `role-contact-types` split. The schemes stay flat. |
| `contact-title`, `corporation-name`, `person-name` | Single recorded facts of a contact. `corporation-name` and `person-name` are not kinds of `owner-name`, which belongs to owner contacts. |

### Value set (flat by intent)

| Scheme | Values | Reason |
| --- | --- | --- |
| `role-contact-types` | `agent` (managing agent), `head-officer`, `officer`, `shareholder`, `site-manager`, `lessee` | HPD lists them as separate types. `head-officer` is not narrower than `officer`: HPD records them as different types and a title never changes the role. Grouping officers apart from agent or site manager would add a layer no field uses, and could read as ranking or control. `agent` stays distinct from ownership: a managing agent is a management relationship. |
| `role-contact-types`, `owner-contact-types` | (two schemes) | Not nested or merged. The owner types are the registered owner (Q2); the role types are every other recorded role. |

### Groupings the question asks for

| Grouping | Where it appears | Expressed as |
| --- | --- | --- |
| "Managing agent, head officer or site manager" | Q4 | Not a grouping. Three of the six values of `role-contact-types`; the answer lists every role contact with its type and does not filter. |
| The business address parts of a role contact | Q4.2 | No collection. Separate fields, as in Q3.2. |
| Owner and role contacts together on a registration | Q4 | Not a vocabulary grouping. The answer combines Q2.2 and Q4.1 through `registration`. |

### Disjointness candidates for Stage 5

- `role-contact` and `owner-contact`: a contact is one or the other by type. Both stay narrower than `contact`. Candidate only; the decision is Stage 5's.

## Contact merge (2026-11-15)

**Result: one hierarchy, `contact`.** `OwnerContact` and `RoleContact` became one `Contact` node (decision 2026-11-15), so the concept `contact` is the broader concept of the two kinds. Reviewed 2026-11-15; this supersedes "no hierarchy needed" for Q2 and Q4.

### The hierarchy

| Broader | Narrower | Justification |
| --- | --- | --- |
| `contact` | `owner-contact`, `role-contact` | A contact is an owner contact when its HPD type is corporate owner, individual owner or joint owner, and a role contact for the other six types. The kinds are told apart by type only. Reports keep them apart; the broader concept does not invite merging them in an answer. |

Each narrower concept has exactly one broader concept. Depth is one level. The graph stores the HPD type on `Contact`; the hierarchy lives only in the vocabulary.

## Q5

**Result: no hierarchy needed.** Still no `skos:broader`, `skos:narrower` or collections. Reviewed 2026-11-13; `watchline.ttl` was not changed in this stage.

### Concepts left flat, and why

| Concepts | Reason |
| --- | --- |
| `dos-entity`, `owner-contact`, `grantee` | A DOS entity is a state filing record. An owner contact and a grantee are names on other records. A name match is a lead, not a kind-of; grouping them under "party" or "owner" would suggest identity. |
| `dos-id` | An identifier is not a kind of the thing it identifies. |
| `dos-entity-name`, `owner-name`, `grantee-name` | Names on different records. Not kinds of one another. |
| `entity-type`, `jurisdiction`, `initial-filing-date` | Single recorded facts of a DOS entity. The entity types are free-text DOS values (a property, not concepts); no answer filters or groups by kind of entity. Not made a scheme. Revisit if a question needs LLC versus corporation. |
| `dos-process-name`, `dos-process-address` | Where the state forwards legal papers. Neither is a kind of `registered-agent-name` or `mailing-address`; the project keeps these roles apart. |
| `registered-agent-name`, `registered-agent-address` | A registered agent is a DOS role, distinct from a managing agent (`role-contact-types` `agent`). Not nested under it or under any "agent" parent. |
| `dos-process-address`, `registered-agent-address`, `mailing-address`, `address` | Addresses of different parties and purposes. Parts of an address are part-whole at most. No "address" parent: it would invite treating co-location as identity. |

### Groupings the question asks for

| Grouping | Where it appears | Expressed as |
| --- | --- | --- |
| Record attributes (type, jurisdiction, filing date) | Q5.1 | No collection. Each is its own field, as in Q1.4. |
| Process name and address; registered agent name and address | Q5.2, Q5.3 | No collection. Separate answer fields in separate sub-questions. |
| Name agreement outcomes and rules | Q5.1 | Reuse the flat scheme `name-agreement-outcomes` (Q3). N3 is a value of `comparison-rule`; no change. |

### Disjointness candidates for Stage 5

- `dos-entity` and `owner-contact`, `grantee`: a state filing record is not an HPD contact or a deed party. Candidate only (already separate classes; no edge between them by decision 2026-11-12).

## Q8 (Operational Network): Stage 3, 2026-11-13

**Result: one hierarchy, `network-absence-reasons`.** The first `skos:broader`/`skos:narrower` links in the vocabulary.

### The hierarchy

Meaning: **is-a** between a specific reason a lot is in no network and the kind of reason it is. Source: BOR release v0.3.0 `DATA.md`, which gives each reason code a level (the five top-level reasons are its levels); the links follow that table and nothing is invented.

| Broader | Narrower (stored code) | Justification |
| --- | --- | --- |
| `no-qualifying-linkage` | `no-linkage` (`no_linkage`) | No accepted link connected the record to another: a kind of "no qualifying linkage". |
| `outside-source-coverage` | `no-registration` | No HPD registration: the source has nothing for the lot. |
| `outside-method-input` | `no-owner-contact` | Registered, but the method had no owner contact to use. |
| `excluded-by-policy` | `aggregator-address-masked`, `address-evidence-masked` | Each is a mask rule applied on purpose. |
| `below-eligibility-rule` | `first-name-veto`, `common-name-veto`, `shared-company-degree-unknown`, `shared-company-name-not-rare`, `shared-company-first-name-conflict`, `shared-company-degree-cap` | Each is a guard or threshold the candidate evidence failed. |

Each detail concept has exactly one broader concept. Depth is two levels. The graph stores both codes on the lot (`networkAbsence`, `networkAbsenceDetail`); the hierarchy lives only in the vocabulary, so the agent can answer at either level.

The Operational Network layer uses 11 of BOR's detail codes. The Owner Portfolio layer adds 8 more (see Q9 below). The scheme is shared, so a detail concept is not tied to one layer; each layer's profile lists the subset it uses. BOR's other 5 codes occur in neither layer and are not concepts.

### Concepts left flat, and why

| Concepts | Reason |
| --- | --- |
| `whole-component`, `louvain-community` | Two values of a split, not kinds of one another. "Louvain community" is a cut of a component, not a kind of component. |
| `operational-network`, `landlord` | A network groups lots through landlord records; neither is a kind of the other, and `landlord` is not a kind of owner. Related links are Stage 4. |
| `landlord-name`, `business-address`, `anchor-landlord` | A name and an address are properties of a landlord record, and the anchor is one record picked by a rule; none is a kind of the others or of `landlord`. |
| `connected-by-name`, `connected-by-address`, `connected-by-identity`, `connected-by-deed`, `link-weight`, `edge-id`, `evidence-type`, `evidence-id`, `masked-address-edges` | Relationships and properties of the link graph. The four link kinds are kinds of evidence, not kinds of one another; the layer a link serves is derived from its kind, so no parent concept is needed. |
| `network-split`, `network-group-id`, `in-network`, `covers` | Single properties or relationships. An identifier is not a kind of the thing it identifies. |
| `network-absence`, `network-absence-detail` | Properties naming the two levels of one scheme; they are not parent and child of each other (the values are). |

### Groupings the question asks for

| Grouping | Where it appears | Expressed as |
| --- | --- | --- |
| Absence at top level or in detail | Q8.4 | The hierarchy above. |
| The three weights of a link | Q8.3 | No collection: separate answer fields; the sum is `link-weight`. |

### Disjointness candidates for Stage 5

- The five top-level absence reasons are mutually exclusive for a lot (the release gives one reason per lot). Candidate only; the graph stores values, not classes.
- `landlord` and `owner-contact`: a Who Owns What landlord record is built from owner contacts but is not one. Candidate only.

Checked by `make taxonomy` (`scripts/check_taxonomy.py`, 49/49): no cycle, inverses match, one parent, shallow, sourced, no hierarchy link in the ontology file.

## Q9 (Owner Portfolio): Stage 3, 2026-11-13

### The hierarchy

Q9 adds no new branch. It extends the shared absence-reason scheme (`network-absence-reasons`) with 8 detail concepts, each with one broader concept among the existing five tops. Meaning is unchanged: a detail reason is a kind of its top-level reason. Source: BOR release v0.3.0 `bbl_status` reason codes, grouped by BOR's own top-level reason.

| Broader | New narrower concepts | Justification |
| --- | --- | --- |
| `outside-method-input` | `unmatched-node` | A landlord record the method never received as input. |
| `excluded-by-policy` | `coop-condo-excluded`, `coop-condo-dominated`, `institutional-screen` | Each is a rule applied on purpose: co-ops and condos are left out of the footprint, and institutional owners are screened out. |
| `below-eligibility-rule` | `deed-not-latest`, `deed-parcels-out-of-range`, `successor-not-shell`, `successor-transfer-not-nominal` | Each is a deed-bridging guard or threshold the candidate failed. |

Depth stays at two levels. The graph stores both codes on the lot (`portfolioAbsence`, `portfolioAbsenceDetail`); the hierarchy lives only in the vocabulary.

### Concepts left flat, and why

| Concepts | Reason |
| --- | --- |
| `portfolio-compositions` values (`identity-based`, `deed-only`, `deed-bridged`) | Three ways a portfolio was built, not kinds of one another. `deed-bridged` is not a kind of `identity-based`. |
| `ownership-signals` values (six stage codes) | The dotted codes (`identity.*`, `deed.*`) look like a hierarchy, but they are BOR's stage labels. An identity signal and a deed signal are not kinds of one signal, and `identity.curated` is a source of the link, not a kind of Splink link. Stays flat. |
| `owner-portfolio`, `operational-network` | Two groupings of the same landlord records; neither is a kind of the other. Related links are Stage 4. |
| `portfolio-group-id`, `portfolio-composition`, `in-portfolio`, `ownership-signal`, `portfolio-absence`, `portfolio-absence-detail` | Properties and relationships. `portfolio-absence` and `portfolio-absence-detail` name the two levels of one scheme; they are not parent and child of each other. |

### Groupings the question asks for

| Grouping | Where it appears | Expressed as |
| --- | --- | --- |
| Absence at top level or in detail | Q9.5 | The shared hierarchy above. |
| Signals along a portfolio's links | Q9.3 | No grouping: a list of links, each with one signal. |

### Disjointness candidates for Stage 5

- The three portfolio compositions are mutually exclusive for a portfolio (one value per group). Candidate only.
- `owner-portfolio` and `operational-network`: both group lots, but a lot can be in both, so they are not disjoint as groupings of lots. Candidate rejected.

Checked by `make taxonomy` (`scripts/check_taxonomy.py`, 81/81).

## Q6 (Aggregator or mail-drop address): Stage 3, 2026-11-13

### The hierarchy

No hierarchy needed. Q6 adds two classifications of an address and their values, and none of the answers needs a broader or narrower step. The Q6 concepts are left flat on purpose.

### Concepts left flat, and why

| Concepts | Reason |
| --- | --- |
| `listed-registered-agent`, `listed-law-firm`, `listed-management-office`, `listed-unknown` (scheme `mail-drop-kinds`) | Four kinds the list assigns, one per address. A law firm and a registered agent can both act as an agent, but the list does not say one is a kind of the other, and `listed-unknown` is the absence of a finding, not a parent. The answer gives the list's own code. |
| `unreviewed` (scheme `list-review-statuses`) | One value today. A `reviewed` value would sit beside it, not under it. |
| `network-masked-address`, `portfolio-masked-address`, `mail-drop-address` | Two classifications of an address by different authorities (a method's mask and a project's curated list). Neither is a kind of the other; a masked address need not be listed and the reverse. Related links, if any, are Stage 4. |
| `portfolio-masked-address-text`, `portfolio-masked-address-degree`, `masked-identities`, `masked-address-id`, `masked-address-text`, `masked-address-degree`, `mail-drop-address-key`, `zip-five`, `mail-drop-kind`, `mail-drop-basis`, `list-review-status` | Properties of the two nodes. An identifier or a text is not a kind of the thing it names. |

### Groupings the question asks for

| Grouping | Where it appears | Expressed as |
| --- | --- | --- |
| Per method: masked or not, and the list apart | Q6 parent | Two node types and separate answer fields; the answer never merges them. |
| Owner and role contacts at one address | Q6.1 | Separate fields (`ownerContacts`, `roleContacts`), as in Q2 and Q4. |

### Disjointness candidates for Stage 5

- `NetworkMaskedAddress` and `MailDropAddress` are different nodes; an address text can appear in both, so their instances are never the same individual but their texts overlap. Candidate: disjoint classes (one node is one classification), not disjoint texts.
- `MailDropAddress` and `Contact`: a listed address is not a contact. Candidate only.

Checked by `make taxonomy` (`scripts/check_taxonomy.py`).


## Q7 (Shared evidence): Stage 3, 2026-11-16

**Result: no hierarchy needed.** The new concepts (`document`, `document-party`, `has-party`, `party-name`, `party-role`, `address-party-count`, `address-document-count`, `process-address-entity-count`, `set-aside`) add no `skos:broader` or `skos:narrower` links.

| Concepts | Reason |
| --- | --- |
| `document`, `deed` | A Deed is a deed-type document, but the two are separate graph nodes that share an id and no answer groups them by kind, so `deed` stays flat and the link is `skos:related` (contrasts-with). |
| `party-name`, `grantee-name` | A grantee name is a party name only on a deed side; the role is recorded code, not a type. Related, not nested. |
| `address-party-count`, `address-document-count`, `process-address-entity-count` | Three hub counts over different sources and units. No answer reports them as one kind. |
| `set-aside` | A derived answer state with three independent reasons (network mask, portfolio mask, mail-drop list). The reasons are existing concepts related to it, not narrower concepts. |

Disjointness candidates for Stage 5: `document` and `deed` are not disjoint (a deed is a document type); `document-party` and `grantee` are not disjoint; none is proposed.

## Q11 (Affiliations): Stage 3, 2026-11-16

**Result: no hierarchy needed.** The new concepts add no `skos:broader` or `skos:narrower` links and no collection.

| Concepts | Reason |
| --- | --- |
| `ownership-affiliation`, `parent-affiliation`, `management-affiliation`, `financing-affiliation`, `other-affiliation` | The five affiliation types of the question's own list, answered side by side. A parent is documented evidence of ownership at a stated level, but no source documents one and the question treats it as its own type ("only a documented parent may be called one"), so it is not nested under ownership. `other-affiliation` is the residual value, not a parent of the rest. |
| `documented`, `hypothesized`, `reported` | Three evidence statuses ordered by how firmly a relationship is supported. Severity order alone never justifies broader/narrower, and none is a kind of another (a reported claim is not a kind of documented fact). |
| `mortgage`, `document` | A mortgage is a document of current type MTGE, but no answer groups documents by kind, and `document`, `deed` stay related, not nested (Q7); the same holds here. Related link, if any, is Stage 4. |
| `borrower`, `lender` | Two roles a party plays on one mortgage, recorded as party types 1 and 2. A role is not a kind of party, and they are opposites, not narrower terms of a party. |
| `affiliation` | The answer item that carries a type and a status. It is not a broader term of the five types (a type is a value of it, not a kind of it). |

Groupings the question asks for: the affiliation type and the evidence status are two value schemes read together by the answer, not a hierarchy; the contact-type to affiliation-type mapping is answer-contract logic (`tests/q11_2/fixtures.yaml` `type_map`), not a broader link.

Disjointness candidates for Stage 5: none proposed (`ownership-affiliation` and `management-affiliation` can both apply to one party in different registrations).

## Q12 (Transfers of a lot): Stage 3, 2026-11-17

**Result: no hierarchy needed.** The new concepts (`grantor`, `has-grantor`, `grantor-name`, `not-a-sale`, `attributable-transfer`) add no `skos:broader` or `skos:narrower` links and no collection.

| Concepts | Reason |
| --- | --- |
| `grantor`, `grantee` | Two roles a party plays on one deed (ACRIS party types 1 and 2). A role is not a kind of party, and they are opposites, not narrower terms of a common concept. Related, not nested (Stage 4). |
| `grantor-name`, `grantee-name`, `party-name` | The same name can sit on both sides of one deed (anchor A, 2025). Each is the name of a role-bound node; none is a kind of another. |
| `not-a-sale` | A derived flag from the recorded amount and document type. It is not a kind of `deed`, and a deed with an amount is not its opposite concept; the answer never calls a deed a sale. |
| `attributable-transfer` | A derived answer state (a name lead against the registered owner), not a kind of `deed` or `owner-contact`. |

Groupings the question asks for: the deed timeline, its counts and the attribution are answer fields read together, not a hierarchy. The portfolio deed set reuses `owner-portfolio` and `deed` without a new grouping.

Disjointness candidates for Stage 5: none proposed (`Grantor` and `Grantee` are different nodes, but one name can appear in both).

## Q13 (Mortgages, assignments, satisfactions): Stage 3, 2026-11-17

**Result: one hierarchy, `financing-document`.** Meaning: **is-a** between a kind of financing document and the general concept. Source: the question's own separation of the documents into mortgages, assignments, satisfactions, terminations and agreements (`specs/questions/q13.md`, answer requirement 2) and the definition of `financing-document`, which is "a mortgage or a document that assigns, satisfies, terminates or supplements one".

| Broader | Narrower | Justification |
| --- | --- | --- |
| `financing-document` | `mortgage` (MTGE) | A mortgage is a financing document. |
| `financing-document` | `assignment` (ASST, AL&R) | A recorded assignment of a mortgage or of leases and rents. |
| `financing-document` | `satisfaction` (SAT) | A recorded satisfaction of a mortgage. |
| `financing-document` | `termination` (TL&R) | A recorded termination of an assignment of leases and rents. |
| `financing-document` | `agreement` (AGMT, SAGE) | A recorded agreement supplementing a loan. |

Each narrower concept has exactly one broader concept; depth is one level; the five stay top concepts of no scheme. The graph stores `docType` only, so the kind is the answer contract's grouping of codes (`tests/q13_support.py` KINDS) and the hierarchy lives only in the vocabulary. `mortgage` was a top concept since Q11; Q11's use (borrower and lender on a mortgage) is unchanged. The `skos:related` links between each kind and `financing-document` were removed because a hierarchical and an associative link between the same pair is not allowed; the sibling links (for example `satisfaction` to `mortgage`) are kept and are Stage 4's to review.

### Concepts left flat, and why

| Concepts | Reason |
| --- | --- |
| `financing-document`, `document` | A financing document is a document of certain types, but the graph keeps one `Document` node and no answer groups documents by kind beyond Q13.3 (same reasoning as `deed`, Q7). Related, not nested. |
| `has-financing-document` | A relationship, not a kind of document. Related to `has-deed`, not nested. |
| `borrower`, `lender` | Roles on a mortgage, not kinds of document or party (Q11). |
| `financing-affiliation` | An affiliation type, not a kind of document. |

### Groupings the question asks for

| Grouping | Where it appears | Expressed as |
| --- | --- | --- |
| Mortgages, assignments, satisfactions, terminations, agreements as separate lists | Q13.3 | The hierarchy above. |
| Document type codes within a kind (ASST and AL&R; AGMT and SAGE) | Q13.3 | Alt labels on the narrower concept; the codes are values of `documentType`, not concepts. |
| Date, recorded date, amount of a document | Q13.1 | No collection; separate fields (as Q3.1). |

### Disjointness candidates for Stage 5

- None proposed. The kinds partition the seven codes today, but a document has one type and the graph stores no class per kind.

## Q14 (Title holder and registered owner on a violation date): Stage 3, 2026-11-17

**Result: no hierarchy needed.** The four new concepts (`supporting-deed`, `date-basis`, `registration-in-force`, `title-registration-relation`) add no `skos:broader` or `skos:narrower` links and no collection. `watchline.ttl` was not changed in this stage.

| Concepts | Reason |
| --- | --- |
| `supporting-deed`, `deed` | A supporting deed is a role a deed plays in one answer (latest on or before a date, under a basis). A role is not a kind of the thing, so it is not narrower than `deed`. Related (Stage 1), not nested. |
| `date-basis` | An input with two values, `document` and `recorded`. The values are plain enums in `profiles/q14.yaml`, not concepts or a scheme; the two dates already exist as `document-date` and `recorded-date`, which stay unnested. |
| `registration-in-force`, `registration` | An answer status of a registration on a date (registered-later, ended, undated, end-unknown, in-force), not a kind of registration. The status values are plain enums, not a scheme: no answer filters by a group of them. A "not in force" group (registered-later, ended, undated, end-unknown) would add a layer no field uses, and "in force" is HPD's period, not responsibility. |
| `title-registration-relation`, `attributable-transfer` | Both are derived answer states that compare a deed party with a registered owner. Neither is a kind of the other. The five relation values (coincide, differ, not-comparable, no-title-record, no-registration-in-force) are plain enums; `differ` and `not-comparable` are not grouped as "no match", which would hide that a difference can be spelling. |

Groupings the question asks for: the three parts of the answer (supporting deeds, registrations with status, relation) are answer fields read together, not a hierarchy.

Disjointness candidates for Stage 5: none proposed (the answer states are computed, not stored).

## Q15 (Open violations of a building): Stage 3, 2026-11-18

**Result: no hierarchy needed.** The six new concepts (`violation`, `has-violation`, `violation-class`, `violation-status`, `inspection-date`, `open-violation-rate`) add no `skos:broader` or `skos:narrower` links and no collection. `watchline.ttl` was not changed in this stage.

| Concepts | Reason |
| --- | --- |
| `violation-class` | Its values A, B, C and I are plain enums in `profiles/q15.yaml`, not concepts or a scheme. The A to C order is severity, and severity order never justifies broader/narrower. No answer filters by a group of classes, and the answer says classes are never added into a severity score. |
| `violation-status` | Open and Close are plain enums. 'Close' covers closed and dismissed, and HPD's finer status is not stored, so there is nothing to nest. |
| `violation`, `building` | A violation is cited against a building but is not a kind of it. Related (Stage 1), not nested. |
| `has-violation` | A relationship, not a kind of violation. Related to `has-building`, not nested. |
| `inspection-date`, `document-date`, `recorded-date` | Dates of different things (an inspector's visit, a document). None is a kind of another. |
| `open-violation-rate` | A computed answer value (open count over PLUTO units), not a kind of `violation` or `residential-units`. |

Groupings the question asks for: counts by class and status, the oldest open inspection date, and the rate are answer fields read together, not a hierarchy. No collection.

Disjointness candidates for Stage 5: none proposed (counts and the rate are computed, not stored).

## Q16 (Reports and filing documents): Stage 3, 2026-11-18

**Result: no hierarchy needed.** The 22 Q16 concepts add no `skos:broader` or `skos:narrower` links and no collection. `watchline.ttl` was not changed in this stage.

| Concepts | Reason |
| --- | --- |
| `source-category` values (`public-record`, `published-reporting`, `web-content`, `project-derived`) | Four flat values of one scheme. No answer filters by a group of them, and `project-derived` is a method's output, not a kind of source. Tracked apart from reliability type (I, II). |
| `review-status` values (`item-unreviewed`, `confirmed`, `refuted`, `inconclusive`, `contested`) | A checking state, not kinds. Order of review and "checked vs not checked" never justify broader/narrower. `confirmed` and `refuted` are reviewer-set; `inconclusive` is not `item-unreviewed`. Not nested under the Q6 `unreviewed`. |
| `fact-relation` values (`agrees`, `adds`, `conflicts`, `unrelated`) | Comparison outcomes computed at answer time. `conflicts` is not grouped with `adds` as "not agreeing"; that would hide that a conflict needs showing beside the recorded value. |
| `match-basis` values (`exact-match`, `lead-only`) | Two flat values. `lead-only` is a caution about a name match, not a narrower kind of match. |
| `retrieved-item`, `reported-claim` | A reported claim is the content of an item (its quoted statement), not a kind of item. Related (Stage 1), not nested. |
| `reported-claim`, `reported` (Q11) | `reported` is an affiliation evidence status; the claim is a statement. Related, not nested. |
| `extraction-method` | Its values (text, character recognition, entered by a person) are plain enums in `profiles/q16.yaml`, not concepts. |
| `retrieved-item`, `affiliation` | An item can contain an affiliation claim; neither is a kind of the other. |

Groupings the question asks for: the five fields of an item (publisher and date, claim, category and status, relation, basis) are answer fields read together, not a hierarchy. No collection.

Validator note: `make vocab` reports one S13 info on a concept with the same literal on `prefLabel` and `hiddenLabel`. It is the Q6 `list-review-status` value `unreviewed` (line 1680 and 1681), not a Q16 concept; left for Q6 review.

Disjointness candidates for Stage 5: none proposed (the items are session evidence and not stored).

## Q17 (Missing, lapsed or stale registration): Stage 3, 2026-11-18

**Result: no hierarchy needed.** The five Q17 concepts (`missing-registration`, `no-usable-registration`, `lapsed-registration`, `registration-older-than-deed`, `unit-threshold`) add no `skos:broader` or `skos:narrower` links and no collection. `watchline.ttl` was not changed in this stage.

| Concepts | Reason |
| --- | --- |
| `missing-registration`, `lapsed-registration`, `registration-older-than-deed` | Three separate conditions, each answered holds, does-not-hold or cannot-tell. None is a kind of another: a lot can be lapsed and older than its deed, or neither. Grouping them as "registration problems" would imply a ruling the answer does not make. |
| `no-usable-registration` | A flag on a registered lot (rows but a placeholder id or BIN), not a kind of `missing-registration`: the lot is not missing, and its other conditions are cannot-tell. Related, not nested. |
| `unit-threshold` | A reporting threshold with plain enum outcomes (`meets-threshold`, `below-threshold`, `units-not-recorded`) in `profiles/q17.yaml`, not concepts. Not a kind of `residential-units`. |
| outcome values (`holds`, `does-not-hold`, `cannot-tell`) | Plain enums shared by three answers. Not a scheme, and no answer filters by a group of them. |

Groupings the question asks for: the four conditions are answer fields read together for one lot, not a hierarchy. No collection.

Disjointness candidates for Stage 5: none proposed (the conditions are computed, not stored).

## Q18 (Restructuring deeds): Stage 3, 2026-11-18

**Result: no hierarchy needed.** The three Q18 concepts (`deed-classification`, `zero-transfer`, `restructuring-signal`) add no `skos:broader` or `skos:narrower` links and no collection. `watchline.ttl` was not changed in this stage.

| Concepts | Reason |
| --- | --- |
| `zero-transfer` and `deed-classification` | A zero-transfer deed is one value of the classification (with correction and priced, plain enums in `profiles/q18.yaml`), not a kind of it. A value of a class code is not narrower than the code. Related, not nested. |
| `zero-transfer` and `not-a-sale` | `not-a-sale` is the Q12 flag (amount 0 or a correction). Zero-transfer is a subset by amount, but the flag is a property of a deed, not a kind of deed, so a broader link would mix meanings. Related, not nested. |
| `restructuring-signal` | One concept for four boolean leads of the same kind; they are fields of the answer, not concepts, and no answer filters by one. Not a kind of `attributable-transfer` (that one is a Q12 match to the registered owner; one of the four signals reads the same match). |
| outcome values (`correction`, `zero-transfer` value, `priced`) | Plain enums, not a scheme: no answer filters by a group of them. |

## Q19 (Membership explanation): Stage 3, 2026-11-19

**Result: no hierarchy needed.** The four Q19 concepts (`pair-layer-state`, `representative-path`, `pre-subdivision-connectivity`, `stage-precision`) add no `skos:broader` or `skos:narrower` links and no collection. `watchline.ttl` was not changed in this stage.

| Concepts | Reason |
| --- | --- |
| `pair-layer-state` | Its values (same, different, ungrouped) are a plain enum in `profiles/q19.yaml`; no answer filters by a group of them. The ungrouped reasons reuse the existing `network-absence-reasons` hierarchy (Q8, Q9), which is not changed. |
| `representative-path` | An answer object (a chain of links), not a kind of link. The link kinds stay flat (`connected-by-identity`, `-deed`, `-name`, `-address`). |
| `pre-subdivision-connectivity` | A condition of a pair, not a kind of `whole-component` or `louvain-community`; those are values of a split, not parents. Related, not nested. |
| `stage-precision` | A property of a linkage stage, not a kind of `ownership-signal`; a stage is not narrower than its precision, nor the reverse. |

Disjointness candidates for Stage 5: none proposed (the four terms are computed at answer time).

## Q20 (The dossier): Stage 3, 2026-11-19

**Result: no hierarchy needed.** The three new concepts (`dossier`, `lead`, `stop-reason`) and the five values of the `stop-reasons` scheme add no `skos:broader` or `skos:narrower` links and no collection. `watchline.ttl` was not changed in this stage.

| Concepts | Reason |
| --- | --- |
| `dossier` | An assembled answer, not a kind of any component. Its sections are answer fields read together, not narrower concepts. Not a kind of `affiliation` or `owner-portfolio`. |
| `lead` | A role a name or address plays under the lead rule, not a kind of name or address, and not a kind of `affiliation`. A hypothesis is a lead, never a finding: related, not nested. Distinct from `lead-only` (a match basis of a retrieved item). |
| `stop-reason` and its five values | A flat value set (all top concepts of `stop-reasons`): a stop reason is chosen once, and the five are alternatives, not kinds of one another. `reached-service-address` is not narrower than `no-further-link`. Reused for an individual lead's unresolved reason without nesting. |
| claim labels, source categories, review statuses | Reused unchanged from Q11 and Q16; the existing schemes stay flat. |

Groupings the question asks for: the seven dossier sections are answer fields read together, not a hierarchy. No collection.

Disjointness candidates for Stage 5: none proposed (the terms are computed at answer time).

## Q21 (Violations across a layer): Stage 3, 2026-11-19

**Result: no hierarchy needed.** The two new concepts (`lot-violation-ranking`, `violation-concentration`) add no `skos:broader` or `skos:narrower` links and no collection. `watchline.ttl` was not changed in this stage.

| Concepts | Reason |
| --- | --- |
| `lot-violation-ranking` | An ordered answer list, not a kind of `violation` or of `open-violation-rate`. Its rows use the rate and the classes, which are fields, not narrower concepts. Related, not nested. |
| `violation-concentration` | A figure computed over that list, not a kind of ranking and not a kind of `violation`. Related, not nested. |
| violation classes A, B, C, I | Reused as the plain enum of `violation-class` (Q15). Severity order never justifies broader/narrower, and "hazardous" is not a class or a concept. |
| layers | `operational-network` and `owner-portfolio` stay flat siblings; neither is a kind of the other (Q8, Q9). |

Groupings the question asks for (per-lot figures, concentration, layer comparison) are answer fields read together, not a hierarchy. No collection.

Disjointness candidates for Stage 5: none proposed (the terms are computed at answer time).

## Q22 (stage 3, 2026-11-19)

**Result: no hierarchy needed.** `abbreviation-match` and `differs-by-numeral-or-word` add no `skos:broader` or `skos:narrower` link and no collection. `watchline.ttl` was not changed in this stage.

| Concepts | Reason |
| --- | --- |
| `abbreviation-match` | A separate outcome, not a kind of `normalization-match`: it needs a named abbreviation table (AB1), which a spelling normalization does not. Siblings in `entity-name-outcomes`. |
| `differs-by-numeral-or-word` | A kind of non-match, but `different` is defined as "not equal after N2", and this one is a reported refinement of it, not a narrower concept. Kept as a sibling so the answer can state it. |
| `exact-normalized`, `normalization-match`, `different`, `not-comparable` | Shared with `name-agreement-outcomes` (Q3); flat top concepts in both schemes. A match strength order never justifies broader/narrower. |

The six outcomes are a flat value set, and the answer reads outcome and rule together as fields. No collection.

Disjointness candidates for Stage 5: none proposed (the outcomes are computed at answer time).

## Q23 (stage 3, 2026-11-19)

**Result: no hierarchy needed.** `watchline.ttl` adds no `skos:broader` or `skos:narrower` link and no collection. The one new concept, `agent-footprint`, is an answer object (counts by spelling, layer states and address masks), not a kind of `agent`, `operational-network` or `owner-portfolio`; it is related to them, not nested. The managing agent is the existing `agent` value of `contact-types` (Q4); a duplicate `managing-agent` concept added in stage 1 was removed.

| Concepts | Reason |
| --- | --- |
| `agent-footprint` | An answer object over the agent, its buildings and the layers. Related, not nested. |
| `agent` | A contact-type value, flat in `contact-types` and `role-contact-types`; a footprint is not a kind of agent. |

Groupings the question asks for (spellings, layer counts, address masks) are answer fields read together, not a hierarchy. No collection.

Disjointness candidates for Stage 5: none proposed (computed at answer time).

## Q24 (stage 3, 2026-11-19)

**Result: no hierarchy needed.** `watchline.ttl` adds no `skos:broader` or `skos:narrower` link and no collection. `name-search` is an answer object (matches, leads, outcome), not a kind of `lead`, `name-agreement` or `dossier`. `legal-suffix-only` is a lead kind reported only in a name search; it is not a narrower concept of `different` (Q3 and Q22 call such names different) or of `normalization-match` (it is not a match).

| Concepts | Reason |
| --- | --- |
| `name-search` | An answer object over existing records. Related, not nested. |
| `legal-suffix-only` | A near-name lead kind. The four near kinds (`normalization-match`, `abbreviation-match`, `differs-by-numeral-or-word`, `legal-suffix-only`) are alternatives, not kinds of each other; the first three stay in `entity-name-outcomes`. |
| basis (exact, normalized), outcome (matches, leads-only, no-match-in-these-sources) | Plain enums of the answer contract; no concept minted. |

Groupings the question asks for (matches, person leads, near names) are answer fields read together, not a hierarchy. No collection.

Disjointness candidates for Stage 5: none proposed (computed at answer time).

## Q25 (Other jurisdictions): Stage 3, 2026-11-19

**Result: no hierarchy needed.** The 7 Q25 concepts (`registry-search`, `registry-outcome` and the four `registry-outcomes` values, plus the scheme) add no `skos:broader` or `skos:narrower` links and no collection. `watchline.ttl` was not changed in this stage.

| Concepts | Reason |
| --- | --- |
| `registry-outcomes` values (`registry-record-found`, `registry-status-only`, `registry-no-record`, `registry-unreachable`) | Four flat outcomes of one search. Amount of information returned never justifies broader/narrower: `registry-status-only` is not a kind of `registry-record-found`, and `registry-unreachable` is not a kind of `registry-no-record` (unreachable says nothing about the entity). |
| `registry-search`, `retrieved-item` | A registry search is how an item is obtained, not a kind of item. Related, not nested. |
| `registry-status-only`, `needs-payment` | An outcome and a stop reason. Related, not nested. |
| `registry-unreachable`, `service-unavailable` | Look-alike outcomes in different schemes (registry versus address service). Related, not nested. |
| `jurisdiction`, `registry-search` | A recorded attribute and the search it prompts. Related, not nested. |

## Q26 (What each absence means): Stage 3, 2026-11-19

**Result: no hierarchy needed.** The one new concept, `source-absence`, adds no `skos:broader` or `skos:narrower` link and no collection. `watchline.ttl` was not changed in this stage.

| Concepts | Reason |
| --- | --- |
| `source-absence`, `network-absence`, `portfolio-absence` | An answer object that summarizes the layer absences beside the other sources' absences. It is not a kind of either. Related, not nested. |
| `source-absence`, the five reasons in `network-absence-reasons` | The reasons are values the answer carries, with their existing hierarchy (Q8); the answer is not a kind of reason. Q26 reuses them unchanged. |
| `source-absence`, `violation` | An absence is the lack of a violation record, not a kind of violation. Related, not nested. |
| `present`, `none-in-snapshot`, `not-loaded` (Q26.4 outcome) | A three-value answer field, not concepts. `not-loaded` is not a sixth reason and no concept is minted for it. |

## Q27 (Complaints): Stage 3, 2026-11-19

**Result: no hierarchy needed.** The 10 Q27 concepts (`complaint-problem`, `problem-id`, `complaint-id`, `has-problem`, `problem-type`, `major-category`, `problem-status`, `received-date`, `duplicate-flag`, `complaint-rate`) add no `skos:broader` or `skos:narrower` link and no collection. `watchline.ttl` was not changed in this stage.

| Concepts | Reason |
| --- | --- |
| `problem-type` values (EMERGENCY, IMMEDIATE EMERGENCY, NON EMERGENCY, HAZARDOUS, REFERRAL) | A plain enum in `profiles/q27.yaml`, no concepts minted. Urgency order never justifies broader/narrower: IMMEDIATE EMERGENCY is not a kind of EMERGENCY for the answer, which counts them apart. |
| `major-category` values | HPD's own list, not declared, not nested. HEAT/HOT WATER and HEATING are separate source values; merging them would be an invented grouping. |
| `problem-status` (OPEN, CLOSE) | A plain enum, as `violation-status`. |
| `complaint-problem`, `violation` | Both are records of a condition at a building: a problem is what was reported, a violation what an inspector cited. Neither is a kind of the other. Related, not nested. |
| `complaint-problem`, `complaint-id` | An identifier of a thing is not a kind of that thing; one complaint has several problems. |
| `complaint-rate`, `open-violation-rate` | Look-alike computed rates with different numerators and periods. Related, not nested. |
| `duplicate-flag`, `received-date`, `problem-id` | Attributes of a problem, not kinds. |

Groupings the question asks for (counts by type, category and status) are answer fields read together, not a hierarchy. No collection.

Disjointness candidates for Stage 5: `Problem` with `Building`, `TaxLot` and `Violation` (a problem is a record, never a building, lot or violation).

## Q28 (Litigation): Stage 3, 2026-11-20

**Result: no hierarchy needed.** The 12 Q28 concepts (`litigation-case`, `litigation-id`, `has-litigation-case`, `case-type`, `case-open-date`, `case-status`, `open-judgement`, `harassment-finding`, `finding-date`, `case-penalty`, `respondent`, `respondent-owner-match`) add no `skos:broader` or `skos:narrower` link and no collection. `watchline.ttl` was not changed in this stage.

| Concepts | Reason |
| --- | --- |
| `case-type` values (Tenant Action, Heat and Hot Water, Comprehensive, Access Warrant, and others) | A plain enum of 14 source values, no concepts minted. 'Tenant Action/Harrassment' is not narrower than 'Tenant Action' for the answer, which keeps them apart and says a harassment finding is a separate field. |
| `harassment-finding` values (After Inquest, After Trial, No Harassment) | A plain enum. 'No Harassment' is an outcome, not a kind of finding; no is-a link. |
| `case-status` | Free text as recorded, not a value set. |
| `litigation-case`, `violation` | Both are records at a building: a case is an action HPD brought, a violation what an inspector cited. Neither is a kind of the other. Related, not nested. |
| `respondent`, `contact`, `corporate-owner` | A respondent is a name HPD recorded in a case, not a kind of owner contact. A role a name plays in one answer is not a kind. Related, not nested. |
| `respondent-owner-match`, `name-agreement` | Answer contracts that compare names under a rule: the match is not a kind of agreement outcome, and its values (matched, not matched, not comparable) are answer fields. Related, not nested. |
| `litigation-id`, `finding-date`, `case-open-date`, `case-penalty`, `open-judgement` | Attributes of a case, not kinds. |

Groupings the question asks for (the fields of a case) are answer fields read together, not a hierarchy. No collection.

Disjointness candidates for Stage 5: `Litigation` with `Building`, `TaxLot`, `Violation` and `Problem` (a case is a record, never a building, lot, violation or problem).

## Q15 pest extension (Q15.3): Stage 3, 2026-11-21

**Result: no hierarchy needed.** The two new concepts (`order-number`, `pest-violation`) add no `skos:broader` or `skos:narrower` link and no collection. `watchline.ttl` was not changed in this stage.

| Concepts | Reason |
| --- | --- |
| `pest-violation`, `violation` | A pest violation is a violation whose order number is on the pest list, so the is-a test would pass. It stays flat because no answer or retrieval step needs the link: `pest-violation` is a computed answer concept, not a node or a class, and the agent reaches both through the related link added in Stage 4. Nesting would also pull it out of the top concepts for no gain. Revisit if a question needs to retrieve all kinds of violation through the hierarchy. |
| the pest kinds (mice, roaches, rodents, vermin-unspecified) | A four-value list kept in `data/hpd_pest_orders.yaml`, not concepts. Mice are rodents in biology, but the `rodents` kind is the rat codes (567, 867); nesting `mice` under `rodents` would make a count of rodent violations include or exclude mice by accident. `vermin-unspecified` (566, 866) is not a parent of the others: its code names no species and covers mice, roaches, rats and other pests, so it is a separate kind, never a roll-up. |
| the eight order codes | Values of one property (`order-number`), recorded in the list file, not concepts. |
| `order-number` | An identifier of a rule HPD cites, not a kind of anything. |

Groupings the question asks for ("pest violations", "mice violations") are one filter over the order number, answered from the code list; they are answer fields, not a hierarchy. No collection.

Disjointness candidates for Stage 5: none new (no class is added; `Violation` already stays disjoint from `Building`, `TaxLot`, `Problem` and `Litigation`).

## Q27 pest extension (Q27.3): Stage 3, 2026-11-21

**Result: no hierarchy needed.** The three new concepts (`minor-category`, `problem-code`, `pest-complaint`) add no `skos:broader` or `skos:narrower` link and no collection. `watchline.ttl` was not changed in this stage.

| Concepts | Reason |
| --- | --- |
| `major-category`, `minor-category`, `problem-code` | HPD's source does nest its values (major category, then minor category, then code), but these three concepts are the attributes, not the values. A minor category is not a kind of major category, and a code is not a kind of minor category: they are levels of one classification, a part-whole or containment relation, not is-a. The nesting is also not a clean tree: a minor category can sit under two major categories (CABINET, RADIATOR) and OTHER appears under many minor categories. The values (PESTS, MICE, OTHER) are strings kept as recorded, not concepts, so there is nothing to nest. The agent reads a value with the property it sits in. |
| `pest-complaint`, `complaint-problem` | A pest complaint is a complaint problem whose minor category is PESTS, so the is-a test would pass. It stays flat for the same reason as `pest-violation` (Q15 extension): it is a computed answer concept, not a node or a class, and no answer or retrieval step needs the link. The Stage 4 related link connects them. |
| the pests (mice, roaches, bed bugs, flies, termites, fleas, other) | Values of `problem-code`, not concepts. `OTHER` is a catch-all, not a parent of the named pests, and is never reported as mice. |
| `pest-complaint`, `pest-violation` | Look-alike answer concepts from different sources: what a tenant reported and what an inspector cited. Neither is a kind of the other. Related, not nested (Stage 4). |

Groupings the question asks for ("pest complaints", "mice complaints") are one filter over the minor category and problem code, answered from the data; they are answer fields, not a hierarchy. No collection.

Disjointness candidates for Stage 5: none new (no class is added; `Problem` already stays disjoint from `Building`, `TaxLot`, `Violation` and `Litigation`).
