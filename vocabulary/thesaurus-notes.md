# Thesaurus notes

Records the cross-branch associations, label review and external mappings. Related links are written in both directions in `watchline.ttl`; each unordered pair appears once below. A related link earns its place only where the schema (`profiles/qNN.yaml`) does not already connect the two concepts. Stage 4 procedure: `specs/stage4-procedure.md`. Checked by `scripts/check_thesaurus.py` (`make thesaurus`).

## Related links

Association kinds:

- `identifier-of`: one concept is the identifier of the other.
- `contrasts-with`: look-alike concepts that must be kept apart in an answer.
- `reported-with`: an answer term that is reported only together with another.
- `output-of`: a result produced by an action on the other concept.
- `found-through`: one concept is located by means of the other.
- `same-subject-different-role`: the same thing, seen in a different role in an answer.
- `summary-of`: a flag or count on one concept that summarizes records held under the other.
- `input-to`: a stored value that is compared at answer time to produce the other concept.

| concept | concept | kind | justification |
| --- | --- | --- | --- |
| `bbl` | `tax-lot` | identifier-of | The BBL identifies the lot. Users ask for "the BBL of" an address, and the schema holds it only as a property name. |
| `bin` | `building` | identifier-of | The BIN identifies the building. Same reason as the BBL. |
| `building` | `pluto-building-count` | contrasts-with | HPD's list of buildings and PLUTO's count disagree on about 27% of lots. The answer reports both, labelled by source. |
| `address` | `address-resolution-outcome` | output-of | The outcome is the result of resolving a typed address. |
| `address-resolution-outcome` | `candidate-street-name` | reported-with | Candidate street names are returned only when the outcome is ambiguous. |
| `related-lot` | `bin` | found-through | Related lots are the other lots that share the resolved BIN. |
| `related-lot` | `tax-lot` | same-subject-different-role | A related lot is another tax lot, reported next to the resolved one. |
| `in-graph` | `tax-lot` | same-subject-different-role | In graph says whether the resolved lot is one the graph holds. |
| `registration-id` | `registration` | identifier-of | The id identifies the registration, not the building it covers. Users quote the id from a notice. |
| `hpd-registered` | `registration` | summary-of | The lot flag says some HPD registration exists on the lot. The registrations themselves are reached from the building, which the schema does not connect to the lot flag. |
| `last-registered-date` | `registration-end-date` | contrasts-with | Users read "registered" as "valid until". One is when HPD last received the filing; the other is when the period ends. The answer gives both and does not call the registration current. |
| `recorded-date` | `document-date` | contrasts-with | Users read "most recent" as the date on the document. The rule is the recorded date; the document date is often absent. The answer gives both. |
| `document-id` | `deed` | identifier-of | The id identifies the document, not a lot or a party. Users quote it from ACRIS. |
| `grantee` | `owner-contact` | contrasts-with | A deed party and an HPD contact are different roles. The comparison between them is made at answer time, so the schema holds no link; a name match is a lead, not a finding. |
| `grantee-name` | `name-agreement` | input-to | The agreement is computed from the names; it is not stored, so the schema cannot lead a reader to it. |
| `owner-name` | `name-agreement` | input-to | The other name compared. Same reason. |
| `mailing-address` | `address-agreement` | input-to | The street line is compared; the result is not stored. |
| `zip-code` | `address-agreement` | input-to | The first five digits are compared. Same reason. |
| `address-line-two` | `address-agreement` | reported-with | Reported next to the address agreement but never compared. |
| `name-agreement` | `comparison-rule` | reported-with | The rule (N1 or N2) is always stated with the result. |
| `address-agreement` | `comparison-rule` | reported-with | The rule (A1) is always stated with the result. |
| `name-agreement` | `address-agreement` | contrasts-with | Two separate fields. A name match does not imply an address match, nor the reverse; neither says the parties are the same. |
| `mailing-address` | `address` | contrasts-with | A party's mailing address is not the address of the property. |
| `role-contact` | `owner-contact` | contrasts-with | Both are HPD contacts on a registration, kept apart by type. Q2 reports owners, Q4 everyone else; the answer never merges them. |
| `agent` | `owner-contact` | contrasts-with | A managing agent is a management relationship, not ownership. Users ask "who is the owner" and get the agent. |
| `head-officer` | `contact-title` | contrasts-with | The role is the HPD type; the title is free text beside it. A title such as PRESIDENT never changes or sets the role. |
| `corporation-name` | `owner-name` | same-subject-different-role | The same entity can be the owner and the agent (anchor C). Reported once per role as recorded; a match is a lead, not a merge. |
| `dos-entity` | `dos-id` | identifier-of | The id identifies the filing, not a person. Users quote it from a DOS lookup. |
| `dos-entity` | `owner-contact` | contrasts-with | A DOS entity and an HPD owner contact are different records. The name match is made at answer time, so the schema holds no link; a match is a lead, not a finding. |
| `dos-entity-name` | `owner-name` | found-through | A DOS record is found by an owner's name. The comparison is computed, so the schema cannot lead a reader from one to the other. |
| `dos-entity-name` | `grantee-name` | found-through | The same, from a deed grantee's name. |
| `dos-entity-name` | `name-agreement` | input-to | The agreement is computed from the two names and not stored. |
| `dos-entity-name` | `comparison-rule` | reported-with | The rule (N1, N2 or N3) is always stated with the match. |
| `dos-process-name` | `dos-process-address` | reported-with | The name and address where the state forwards papers are reported together. |
| `registered-agent-name` | `registered-agent-address` | reported-with | The agent's name and address are reported together, when listed. |
| `dos-process-name` | `registered-agent-name` | contrasts-with | Two different recorded roles on one record. A process name is where service goes; an agent is a listed party. Neither runs the entity. |
| `registered-agent-name` | `agent` | contrasts-with | A DOS registered agent is not an HPD managing agent. Users say "agent" for both. |

## Labels

Reviewed 2026-11-12 across the whole vocabulary: no label (preferred, alternative or hidden) is shared by two concepts.

- `number of buildings` was removed as an alternative label of `pluto-building-count`. It would send "number of buildings" to PLUTO's count alone, but an answer must give both counts (PLUTO's and HPD's list).
- `assessed value` stays an alternative label of `assessed-total-value` because Q1.4 uses that wording. PLUTO also holds a land-only assessed value. If a question adds it, qualify this label.
- `lot` (of `tax-lot`) can also mean a vacant lot in everyday use. The definition and scope note settle it; kept.
- `parcel`, `structure`, `unit count`, `building class code`, `borough-block-lot` and `building identification number` are plain synonyms; kept.
- Hidden labels hold source column spellings, so a schema or query that says them finds the concept without displaying them: `numbldgs`, `unitsres`, `yearbuilt`, `bldgclass`, `assesstot`.

### Q2 label review (2026-11-12)

No label (preferred, alternative or hidden) is shared by two concepts (`make thesaurus` checks this).

- `registered owner` and `owner of record` are alternative labels of `owner-contact`, the wording the question uses. The definition says it is a contact HPD records, not proof of title.
- Bare `owner` is deliberately not a label of any concept. It would send users to the HPD contact when they may mean the deed grantee or an Owner Portfolio.
- `registration` is an alternative label of `registration` (HPD registration). It can also mean a rent registration or a business registration; the preferred label carries "HPD".
- Hidden labels hold the source spellings: `registrationid`, `lastregistrationdate`, `registrationenddate`, and the stored contact types `CorporateOwner`, `IndividualOwner`, `JointOwner`.

### Q3 label review (2026-11-12)

No label (preferred, alternative or hidden) is shared by two concepts (`make thesaurus` checks this).

- `buyer` moved from alternative to hidden label of `grantee`. Users say it, but a $0 deed is not a sale; it should find the concept without being displayed.
- `price` and `sale price` are deliberately not labels of `document-amount`; the amount is not a price. `deed date` is not a label of `document-date` or `recorded-date`; users may mean either.
- `unit` (of `address-line-two`) is near `unit count` (of `residential-units`). The definitions settle it; kept.
- `name` is a hidden label of `grantee-name` only (the source column). Bare `owner` stays unassigned, as in Q2.
- The definition of `document-type` listed the codes with commas, which read as extra codes ("DEED, TS"). Rewritten with semicolons.
- Hidden labels hold source spellings: `documentid`, `doctype`, `docdate`, `recordedfiled`, `docamount`, `address1`, `address2`, `businessstreetname`, `businessapartment`, `businesszip`.

### Q4 label review (2026-11-12)

No label (preferred, alternative or hidden) is shared by two concepts (`make thesaurus` checks this).

- `managing agent` is the preferred label of `agent`; the bare HPD spelling `Agent` is hidden. Bare `agent` is not a preferred label, since it also means the software agent.
- `title` is a hidden label of `contact-title` only. It is not a label of the role concepts; a title never sets the role.
- `officer` (concept) and `head officer` stay separate. The definitions and scope notes settle it; kept.
- `lessee` is not a tenant of an apartment (scope note); `tenant` is deliberately not a label.
- `manager` and `property manager` are deliberately not labels: they would send users to `agent` or `site-manager` by guess. The two are different HPD roles.
- Hidden labels hold the stored types (`Agent`, `HeadOfficer`, `Officer`, `Shareholder`, `SiteManager`, `Lessee`) and `corporationname`.

### Q5 label review (2026-11-13)

No label (preferred, alternative or hidden) is shared by two concepts (`make thesaurus` checks this).
- `registered agent name` is not given the alternative label `agent`: bare `agent` already means the HPD managing agent. The link to `agent` (contrasts-with) carries the connection.
- `process agent` and `service address` are not labels: the first suggests the registered agent and the second the managing agent's or owner's mailing address. `DOS process name` and `DOS process address` stay distinct.
- No hidden labels added: the DOS source column names are not wording users or other sources use.

## Navigation pilot

Reviewed 2026-11-12 against Q1's worked examples. No gaps.

| Example | Route |
| --- | --- |
| Lot with three buildings (anchor D) | `tax-lot` to `building` through the schema's `has-building`; `building` to `bin` |
| PLUTO counts more buildings than HPD lists | `building` to `pluto-building-count` (contrasts-with) |
| Ambiguous address | `address` to `address-resolution-outcome` to `candidate-street-name` |
| Condominium or shared BIN | `bin` to `related-lot` to `tax-lot` |
| A lot outside the rental scope | `in-graph` to `tax-lot` |
| "What is the year built?" | `tax-lot` property `yearBuilt`, through the schema; no thesaurus link needed |

### Q2 navigation pilot (2026-11-12)

| Example | Route |
| --- | --- |
| Single registration (anchor A) | `building` to `registration` through `has-registration`; `registration` to `owner-contact` through `has-owner-contact` (both schema) |
| Co-op owner (anchor C) | `owner-contact` to `owner-name`, schema; spelling differs from PLUTO's, reported as recorded |
| Multi-building lot (anchor D) | `tax-lot` to `building` (Q1) to `registration`; the lot flag `hpd-registered` to `registration` (summary-of) |
| Registration ended before the snapshot | `last-registered-date` to `registration-end-date` (contrasts-with) |
| Quoted registration number | `registration-id` to `registration` (identifier-of) |
| No registration found | `hpd-registered` false; no route to a registration, by design |

No gaps.

### Q3 navigation pilot (2026-11-12)

| Example | Route |
| --- | --- |
| Exact agreement (anchor A) | `tax-lot` to `deed` through `has-deed` (schema); `deed` to `grantee` through `has-grantee` (schema); `grantee-name` and `owner-name` to `name-agreement` (input-to); `name-agreement` to `comparison-rule` (reported-with) |
| Latest deed is not a sale | `recorded-date` to `document-date` (contrasts-with); `document-amount` and `document-type` are properties of `deed` (schema) |
| Spelling difference (anchor G) | `grantee-name` to `name-agreement` to `different` (scheme); the rule is reached through `comparison-rule` |
| Two deeds the same day (anchor D) | `recorded-date` is a property of `deed` (schema); the tie rule is in its scope note |
| Deed party against HPD owner | `grantee` to `owner-contact` (contrasts-with) |
| Same address on both sides | `mailing-address` and `zip-code` to `address-agreement`; `address-line-two` reported with it |
| Quoted ACRIS document number | `document-id` to `deed` (identifier-of) |
| Property address against party address | `mailing-address` to `address` (contrasts-with) |

No gaps.

### Q4 navigation pilot (2026-11-12)

| Example | Route |
| --- | --- |
| Five contacts (anchor A) | `registration` to `role-contact` through `has-role-contact` (schema); `role-contact` to each type in `role-contact-types` and to `contact-title`, `corporation-name`, `person-name`, `mailing-address` (schema properties) |
| Agent is the owner (anchor C) | `corporation-name` to `owner-name` (same-subject-different-role); `agent` to `owner-contact` (contrasts-with) |
| Title read as role | `head-officer` to `contact-title` (contrasts-with) |
| Owner or agent? | `role-contact` to `owner-contact` (contrasts-with) |
| Shared business address | `mailing-address` to `address-agreement` (Q3); caveat in the scope note of `role-contact` |

No gaps.

### Q5 navigation pilot (2026-11-13)

| Example | Route |
| --- | --- |
| Entity is its own process agent (anchor A) | `dos-entity` to `dos-process-name` and `registered-agent-name` (schema properties); `dos-process-name` to `registered-agent-name` (contrasts-with) |
| Statutory default (`THE COMPANY`) | `dos-process-name` scope note; `dos-process-address` through `dos-process-name` (reported-with) |
| Person as process name (anchor G) | `dos-process-name` scope note: where service goes, not who runs it |
| Spelling (anchor C) | `owner-name` to `dos-entity-name` (found-through); `dos-entity-name` to `comparison-rule` and `name-agreement` |
| Abbreviation (anchor D) | `dos-entity-name` to `comparison-rule`; no match under N3, candidate only |
| Quoted DOS id | `dos-id` to `dos-entity` (identifier-of) |
| "Who is the agent?" | `registered-agent-name` to `agent` (contrasts-with) |

No gaps.

## External mappings

None sought for Q1 (decided 2026-11-12). Nothing in Q1's answers needs an external scheme. Revisit when party, organization or provenance questions arrive (W3C ORG, PROV-O). Q3 (2026-11-12): none sought. A deed, a grantee and an agreement result have no true equivalent the agent needs; a W3C ORG or schema.org party class would blur the grantee with the registered owner, which the project keeps apart. Q2 (2026-11-12): none sought either. HPD registration, owner contact and owner name have no true equivalent in W3C ORG, PROV-O or schema.org that the agent needs; a mapping would be a guess. No SSSOM file exists yet; it is created with the first mapping.

Q4 (2026-11-12): none sought. HPD roles have no true equivalent in W3C ORG or schema.org; a `Role` or `Person` mapping would blur the agent with the owner, which the project keeps apart.

Q5 (2026-11-13): none sought. A DOS entity is a state filing; the W3C ORG `Organization` and schema.org `Organization` are broader than a filed entity and would invite merging it with an HPD owner, which the project keeps apart. A registered agent has no true equivalent that does not blur it with the managing agent.

## Exceptions

Concepts with no related link, left unlinked on purpose:

- `has-building`, `year-built`, `building-class`, `residential-units`, `assessed-total-value`: the schema already declares the node, property or relationship they belong to, and the check enforces it.
- `matched-exactly`, `matched-by-variant`, `ambiguous`, `not-found`, `service-unavailable`: a flat value set in `address-resolution-outcomes`; they relate to the outcome by scheme membership, not by an association.
- Q2: `has-registration`, `has-owner-contact`, `contact-type`: the schema declares the node, property or relationship they belong to. `corporate-owner`, `individual-owner`, `joint-owner`: a flat value set in `owner-contact-types`; they relate to `contact-type` by scheme membership.
- Q3: `has-deed`, `has-grantee`, `document-type`, `document-amount`: the schema declares the node, property or relationship they belong to. `exact-normalized`, `normalization-match`, `different`, `not-comparable`, `same`, `differs`, `address-absent`: flat value sets in `name-agreement-outcomes` and `address-agreement-outcomes`; they relate to their agreement concept by scheme membership.
- Q4: `has-role-contact`, `person-name`: the schema declares the relationship and property. `officer`, `shareholder`, `site-manager`, `lessee`: a flat value set in `role-contact-types`; they relate to `contact-type` by scheme membership.
- Q5: `entity-type`, `jurisdiction`, `initial-filing-date`: properties of the DOS entity node that the schema declares; no cross-branch reader needs a link.
