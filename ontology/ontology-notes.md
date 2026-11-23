# Ontology notes

Design notes for `watchline-onto.ttl`. Stage 5 procedure: `specs/stage5-procedure.md`. Checked by `scripts/check_ontology.py` (`make ontology`).

## Q1

### Scope

The ontology models what the graph stores: tax lot, building, has building, and ten datatype properties. Elements follow the schema in `profiles/q01.yaml`; the mapping table `concept-mapping.csv` records each element's concepts and graph name. Namespaces are separate: concepts `https://watchline.example/vocab/`, elements `https://watchline.example/onto/`, instances `https://watchline.example/id/`. Ontology IRI `https://watchline.example/onto/watchline`, no version IRI.

### Not modeled

Decided 2026-11-12: graph-stored terms only.

| Term | Reason |
| --- | --- |
| address resolution outcome and its five values | Tool output (Geosupport) reported in the answer; nothing in the graph stores it. Stays a SKOS scheme. |
| related lot, in graph, candidate street name | Computed at answer time from the graph or Geosupport. |
| `grc`, `inferred`, `message`, `tried` | Tool and client diagnostics. |
| `buildingsListed` | Derived at answer time: the count of a lot's `hasBuilding` objects. |

### Axioms

One row per axiom in the ontology. Ranges (`xsd:string`, `xsd:boolean`, `xsd:integer`) are datatype declarations and need no row.

| Axiom | Reason |
| --- | --- |
| `TaxLot` disjointWith `Building` | A lot is not a building (Stage 3 candidate). Lets the reasoner reject a lot-wide value on a building. |
| `hasBuilding`, `bbl`, `hpdRegistered`, `plutoBuildingCount`, `yearBuilt`, `buildingClass`, `residentialUnits`, `assessedTotalValue` domain `TaxLot` | Each appears only on lots in the graph (checked by `make profiles`). The domain makes a lot-wide value on a building inconsistent. |
| `address` domain `TaxLot` or `Building` | Both classes carry an address; the union keeps one property for both. A value on anything else is inconsistent. |
| `bin` domain `Building` | The BIN identifies a building, and appears only on buildings in the graph. |
| `bbl`, `bin`, `address`, `hpdRegistered`, `plutoBuildingCount`, `yearBuilt`, `buildingClass`, `residentialUnits`, `assessedTotalValue` functional | Single-valued in the graph. Uniqueness constraints and loader rules guarantee it. `address` is absent, never multiple, when tied records disagree. |

`address` has a union domain (lot or building) because both use it. `hasBuilding` is not inverse-functional because a BIN can sit on several lots (1003074 on 1002367504 and 1002360018).

### Rules for Stage 6 shapes

OWL cannot express these, and they are not forced into axioms:

- `bbl` is 10 digits, first digit 1 to 5; `bin` is 7 digits, first digit 1 to 5, not ending 000000.
- `bbl` is present on every lot, `bin` on every building, `hpdRegistered` on every lot.
- Every building is linked to at least one lot.
- 0 in `residentialUnits` or `assessedTotalValue` means PLUTO records none; `yearBuilt` is never 0.
- `plutoBuildingCount` and the number of `hasBuilding` objects are different counts and are always reported separately.

### Answer fields

Each field of `profiles/q01.yaml` against the ontology.

| Answer field | Ontology | Note |
| --- | --- | --- |
| `bbl`, `address`, `hpdRegistered` | `bbl`, `address`, `hpdRegistered` | |
| `buildings` | `hasBuilding` with `bin`, `address` | |
| `plutoNumBuildings` | `plutoBuildingCount` | graph name `Lot.plutoNumBuildings` |
| `bin` | `bin` | the addressed building |
| `yearBuilt`, `buildingClass`, `unitsRes`, `assessedTotal` | `yearBuilt`, `buildingClass`, `residentialUnits`, `assessedTotalValue` | |
| `input` | not modeled | user input |
| `inGraph`, `relatedLots`, `buildingsListed` | not modeled | computed at answer time |
| `outcome`, `candidates`, `grc`, `inferred` | not modeled | Geosupport output and client |

### Reasoner and example data

- ROBOT 1.9.11 with HermiT 1.4.5.456, Java 11 (run 2026-11-12). HermiT, not ELK, because ELK does not detect violations of functional data properties.
- `abox/q01.ttl` (values from the verified fixtures): consistent, no unsatisfiable class.
- Negative cases in `abox/negative/`, each flagged inconsistent: `n01` (lot and building at once), `n02` (two BBLs), `n03` (lot-wide units on a building), `n04` (a BIN on a lot).
- ROBOT reads each Turtle file on its own, so an ABox file that does not declare its properties has them read as annotations and the reasoner ignores them. The check therefore merges the TBox and each ABox file into one file before reasoning.

### Pitfall scan

OOPS! (2026-11-12, `make oops`, TBox only; raw report `oops-report.rdf`):

| Pitfall | Level | Finding | Handling |
| --- | --- | --- | --- |
| P11 missing domain or range | Important | `address` had no domain | Fixed: union domain `TaxLot` or `Building`. |
| P13 inverse relationships not declared | Minor | `hasBuilding` has no inverse | Left as is. Q1 stores only `HAS_BUILDING`, and the graph can be traversed in both directions. Add an inverse when a question needs it. |

Rescan after the P11 fix (2026-11-12): only P13 remains, accepted as above.

## Q2

### Scope

Adds two classes (`Registration`, `Contact`), two object properties (`hasRegistration`, `hasContact`) and six datatype properties. `Contact` covers all nine HPD contact types (merged 2026-11-15; Q3 and Q4 reuse it). Elements follow `profiles/q02.yaml`. Same namespaces, one ontology IRI, no version IRI.

### Not modeled

| Term | Reason |
| --- | --- |
| `Contact.contactKey` | A loader key (registration, type, corporation, person and title joined). It carries no meaning, is never an answer field, and is marked `identity_only` in `profiles/q02.yaml`. |
| The nine contact types as classes or individuals | `contactType` is a string as HPD spells it. A subclass per type would add no rule an answer needs, and a title must never change a role; the allowed values are a Stage 6 shape. |
| `ownerName` | The name of an owner contact is the corporation name of a corporate owner or the person name of the others. The graph stores both parts as `corporationName` and `personName`; the owner name is derived at answer time (`profiles/q03.yaml`, Q3.4). |
| Whether a registration is current | The agent's reading of `registrationEnd` against a stated date. |
| Registration period start | Not in the source. |

### Axioms

| Axiom | Reason |
| --- | --- |
| `Registration` disjointWith `Building` | A registration is not a building (Stage 3 candidate). Rejects a registration that carries a BIN. |
| `Registration` disjointWith `Contact` | A registration is not a contact on it. Lets the reasoner reject a contact type on a registration. |
| `hasRegistration` domain `Building` | The graph links only buildings to registrations (checked by `make profiles`). |
| `hasContact`, `registrationId`, `lastRegistered`, `registrationEnd` domain `Registration` | Each appears only on registrations in the graph, except the two dates, which the graph stores on `HAS_REGISTRATION` (see below). |
| `contactType`, `corporationName`, `personName` domain `Contact` | Each appears only on contacts in the graph. Q4 adds `contactTitle` to the same class. |
| `registrationId`, `contactType`, `corporationName`, `personName` functional | Single-valued in the graph: one id per registration, one type per contact, and a name part that is absent, never multiple, when blank. |

`lastRegistered` and `registrationEnd` are deliberately not functional. In the graph they are properties of `HAS_REGISTRATION`, one value per building and registration pair. OWL cannot attach a datatype property to an object property without reifying the pair, so the ontology puts them on the registration. A registration covering several buildings can then carry several values, which functional would wrongly reject.

### Rules for Stage 6 shapes

- `registrationId` is a positive integer and present on every registration; `contactType` is one of the nine HPD types (`CorporateOwner`, `IndividualOwner`, `JointOwner`, `Agent`, `HeadOfficer`, `Officer`, `Shareholder`, `SiteManager`, `Lessee`) and present on every contact.
- Every registration is linked to at least one building; every contact to exactly one registration.
- At most one `lastRegistered` and one `registrationEnd` per building and registration pair (a relationship property).
- `registrationEnd` is never before `lastRegistered`.
- A contact with no corporation name or person name has it absent, never an empty string.
- Names are reported as recorded; no rule merges or compares spellings.

### Answer fields

Each field of `profiles/q02.yaml` against the ontology.

| Answer field | Ontology | Note |
| --- | --- | --- |
| `bin` | `bin` | from Q1 |
| `registrations` | `hasRegistration` | all, none chosen |
| `registrationId` | `registrationId` | |
| `lastRegistered`, `registrationEnd` | `lastRegistered`, `registrationEnd` | relationship properties in the graph |
| `owners` | `hasContact` | all contacts with an owner type, none chosen; empty means none recorded |
| `contactType`, `corporationName`, `personName` | `contactType`, `corporationName`, `personName` | graph names `Contact.contactType`, `Contact.corporationName`, `Contact.personName` |

### Reasoner and example data

- Same tools as Q1: ROBOT 1.9.11 with HermiT, Java 11.
- `abox/q02.ttl` (verified fixtures; person names not repeated): see the run below.
- Negative cases, each meant to be flagged inconsistent: `n05` (registration that is a building), `n06` (two registration ids), `n07` (owner type on a registration).

### Pitfall scan

OOPS! (2026-11-12, `make oops`, run by the user, TBox only; raw report `oops-report.rdf`): one pitfall.

| Pitfall | Level | Finding | Handling |
| --- | --- | --- | --- |
| P13 inverse relationships not declared | Minor | Affects 3 properties: `hasBuilding`, `hasRegistration`, `hasContact` | Left as is, as for Q1. The graph stores one direction and can be traversed both ways. Add an inverse when a question needs it. |

No critical or important pitfall.


## Q3

### Scope

Adds two classes (`Deed`, `Grantee`), two object properties (`hasDeed`, `hasGrantee`) and nine datatype properties, three of them shared by `Grantee` and `Contact`. Elements follow `profiles/q03.yaml`. Same namespaces, one ontology IRI, no version IRI.

### Not modeled

| Term | Reason |
| --- | --- |
| `Grantee.partyKey` | A loader key (document, name, address and ZIP joined). Identity only, never an answer field. |
| name agreement, address agreement, comparison rule | Computed at answer time by `src/watchline/compare.py` over stored values; the outcome schemes stay SKOS. Storing them would assert a finding the rules do not support. |
| The eight deed types as classes | `documentType` is a string as ACRIS spells it. A subclass per type would add no rule an answer needs; the allowed values are a Stage 6 shape. |
| snapshots | Dataset-level provenance in `data/sources.yaml`, no per-record field. |
| grantors, other party and document types, mail-drop flag | Out of scope for Q3 (decision 2026-11-12); no curated mail-drop list exists. |
| `otherLots` | Derived at answer time: the count of other `hasDeed` subjects of the same deed. |

### Axioms

| Axiom | Reason |
| --- | --- |
| `Deed` disjointWith `Registration` | A recorded document is not a registration (Stage 3 candidate). Rejects one node carrying both. |
| `Grantee` disjointWith `Contact` | A deed party is not an HPD contact (Stage 3 candidate). Keeps the two sides of the comparison apart. |
| `hasDeed` domain `TaxLot` | The graph links only lots to deeds (checked by `make profiles`). |
| `hasGrantee` domain `Deed` | Appears only on deeds in the graph. |
| `documentId` domain `Deed` or `Document` | Deeds (Q3) and documents (Q7) both carry the ACRIS id; one property for both, as `mailingAddress`. |
| `documentType` domain `Deed` or `Document` | Same reasoning as `documentId`. |
| `documentDate` domain `Deed` or `Document` | Same reasoning as `documentId`. |
| `recordedDate` domain `Deed` or `Document` | Same reasoning as `documentId`. |
| `documentAmount` domain `Deed` or `Document` | Same reasoning as `documentId`. |
| `granteeName` domain `Grantee` | Appears only on grantees in the graph. |
| `mailingAddress` domain `Grantee` or `Grantor` or `Contact` or `DocumentParty` | Grantees and contacts (Q3, Q4) all carry a mailing address; the union keeps one property for all, as `address` does for lots and buildings. |
| `addressLineTwo` domain `Grantee` or `Grantor` or `Contact` or `DocumentParty` | Same reasoning as `mailingAddress`. |
| `zipCode` domain `Grantee` or `Grantor` or `Contact` or `DocumentParty` | Same reasoning as `mailingAddress`. |
| `documentId`, `documentType`, `documentDate`, `recordedDate`, `documentAmount`, `granteeName`, `mailingAddress`, `addressLineTwo`, `zipCode` functional | Single-valued in the graph: one value per deed or party, absent (never multiple) when blank. For an owner contact, absent when exact duplicate rows disagree. |

`hasDeed` is not inverse-functional (a deed can name many lots) and `hasGrantee` is not functional (a deed can have several grantees or none).

### Rules for Stage 6 shapes

- `documentId` is present on every deed; `documentType` is present and one of `DEED`, `DEED, TS`, `DEED, LE`, `DEED, RC`, `DEEDO`, `DEEDP`, `CORRD`, `CONDEED`; `recordedDate` is present on every deed.
- `documentAmount` is an integer, never negative; 0 is reported as recorded, never read as a free sale.
- Every deed is linked to at least one lot; every grantee to exactly one deed.
- `granteeName` and the address properties are absent when blank, never an empty string.
- Names are stored as recorded (trimmed only); no normalization is applied in the graph.
- "Most recent deed" means the latest `recordedDate`; all deeds tying on it are returned.

### Answer fields

Each field of `profiles/q03.yaml` against the ontology.

| Answer field | Ontology | Note |
| --- | --- | --- |
| `bbl` | `bbl` | from Q1 |
| `deeds` | `hasDeed` | all that tie on the latest recorded date, none chosen |
| `documentId`, `docType`, `docDate`, `recordedDate`, `amount` | `documentId`, `documentType`, `documentDate`, `recordedDate`, `documentAmount` | graph names `Deed.docType`, `Deed.docDate`, `Deed.amount` |
| `otherLots` | not modeled | count of other `hasDeed` subjects, computed at answer time |
| `grantees` | `hasGrantee` | all, none chosen; empty means none recorded |
| `name` | `granteeName` | graph name `Grantee.name` |
| `mailingAddress`, `addressLine2`, `zip` | `mailingAddress`, `addressLineTwo`, `zipCode` | graph names `addressLine2`, `zip`; on grantees and owner contacts |
| `owners` | `hasContact` | all contacts with an owner type, none chosen; empty means none recorded |
| `nameAgreement`, `addressAgreement`, `rule` | not modeled | derived at answer time by `compare.py` (N1, N2, A1) |

### Reasoner and example data

- ROBOT 1.9.11 with HermiT, as for Q1 and Q2.
- `abox/q03.ttl` (verified fixtures; person names not repeated): consistent, no unsatisfiable class (`make ontology`, 2026-11-12, 58/58).
- Negative cases, each meant to be flagged inconsistent: `n08` (two document ids on one deed), `n09` (a deed that is a registration), `n10` (a grantee that is an owner contact).
- HermiT does not compare `xsd:date` values (not in the OWL 2 datatype map), so the date properties' functional axioms are not tested by a negative case; they are checked by the Stage 6 shapes.

### Pitfall scan

OOPS! (2026-11-12, `make oops`, run by the user, TBox only; raw report `oops-report.rdf`): one pitfall.

| Pitfall | Level | Finding | Handling |
| --- | --- | --- | --- |
| P13 inverse relationships not declared | Minor | Affects 5 properties: `hasBuilding`, `hasRegistration`, `hasContact`, `hasDeed`, `hasGrantee` | Left as is, as for Q1 and Q2. The graph stores one direction and can be traversed both ways. Add an inverse when a question needs it. |

No critical or important pitfall.


## Q4

### Scope

Adds one datatype property (`contactTitle`) to `Contact`. Q4 reuses `contactType`, `corporationName`, `personName` (Q2) and the address properties (Q3), read for the six role types. The Q4 class `RoleContact` and relationship `hasRoleContact` were merged into `Contact` and `hasContact` on 2026-11-15. Elements follow `profiles/q04.yaml`.

### Not modeled

| Term | Reason |
| --- | --- |
| `RoleContact`, `hasRoleContact` | Merged into `Contact` and `hasContact` (decision 2026-11-15). Owner and role contacts are told apart by `contactType`; the vocabulary keeps `owner-contact` and `role-contact` as narrower concepts of `contact`. |
| The six role types (agent, head officer, officer, shareholder, site manager, lessee) as classes | `contactType` is a string as HPD spells it. A subclass per role would add no rule an answer needs, and a title must never change a role. The allowed values are a Stage 6 shape. |
| "Managing agent" as a relationship between parties | HPD lists a contact on a registration; it records no link to an owner. Modeling one would invite reading management as ownership. |
| `contactdescription`, business city and state, `registrationcontactid`, contact currency | Not stored (see `not_stored` in the profile). |

### Axioms

| Axiom | Reason |
| --- | --- |
| `contactTitle` domain `Contact` | Appears only on contacts in the graph. |
| `contactTitle` functional | Single-valued in the graph, absent (never multiple) when blank. |

### Rules for Stage 6 shapes

- `contactTitle` is absent when blank, never an empty string (names: Q2; address properties: Q3).
- `corporationName` appears only on corporate owners, agents and lessees.
- A site manager has no `mailingAddress`, `addressLineTwo` or `zipCode`.
- Titles and names are stored as recorded (trimmed only); a title never changes the type.
- An empty set of role contacts means none is recorded; none is inferred.

### Answer fields

Each field of `profiles/q04.yaml` against the ontology.

| Answer field | Ontology | Note |
| --- | --- | --- |
| `registrationId` | `registrationId` | from Q2 |
| `contacts` | `hasContact` | all contacts with a non-owner type, none chosen; empty means none recorded |
| `contactType` | `contactType` | graph name `Contact.contactType` |
| `title` | `contactTitle` | graph name `Contact.title` |
| `corporationName`, `personName` | `corporationName`, `personName` | |
| `mailingAddress`, `addressLine2`, `zip` | `mailingAddress`, `addressLineTwo`, `zipCode` | graph names `addressLine2`, `zip`; shared with grantees and contacts |
| registration dates, snapshot date | `lastRegistered`, `registrationEnd`; dataset-level | registration dates are Q2.1; snapshot date is dataset provenance in `data/sources.yaml` |

### Reasoner and example data

- ROBOT 1.9.11 with HermiT, as for Q1 to Q3.
- `abox/q04.ttl` (verified fixtures; person names not repeated): see `make ontology` below.
- Negative cases, each meant to be flagged inconsistent: `n11` (two corporation names on one contact), `n12` (two contact types on one contact).

### Pitfall scan

OOPS! (2026-11-12, `make oops`, run by the user, TBox only; raw report `oops-report.rdf`): one pitfall.

| Pitfall | Level | Finding | Handling |
| --- | --- | --- | --- |
| P13 inverse relationships not declared | Minor | Affects 5 properties: `hasBuilding`, `hasRegistration`, `hasContact`, `hasDeed`, `hasGrantee` | Left as is, as for Q1 to Q3. The graph stores one direction and can be traversed both ways. Add an inverse when a question needs it. |

No critical or important pitfall.

## Q5

### Scope

Adds one class (`DosEntity`) and 17 functional datatype properties, all on `DosEntity`. No object property: the graph holds no edge from an owner contact or grantee to a DOS record (decision 2026-11-12). Elements follow `profiles/q05.yaml`. The five process-address parts and five agent-address parts each map to one concept, so their `rdfs:label` repeats the concept's label; the comment says which part.

### Not modeled

| Term | Reason |
| --- | --- |
| `DosEntity.nameKey` | A loader lookup key (rule N3). Identity only, never an answer field. |
| Link from owner contact or grantee to DOS entity | A name match is a lead; the comparison is computed at answer time. An object property would read as identity. |
| Name agreement outcome and comparison rule (N1, N2, N3) | Computed by `compare.py`, not stored. Outcomes stay a SKOS scheme. |
| Entity types as classes | `entityType` is DOS's own wording (54 values). No answer needs a subclass; "single-purpose shell" is not inferred from type. |
| Process name and registered agent as relationships to parties | They are recorded text. A class for them would invite reading a service company or default name as a party or a lead. |
| CEO, location, county, officers, managers, members | Not stored (see `not_stored` in the profile). Q5.4 retrieval reports them as session evidence. |
| Snapshot date | Dataset-level provenance in `data/sources.yaml`. |

### Axioms

| Axiom | Reason |
| --- | --- |
| `DosEntity` disjointWith `Contact` | A state filing record is not an HPD contact (Stage 3 candidate). Rejects merging the two on a name match. |
| `DosEntity` disjointWith `Grantee` | A state filing record is not a deed party (Stage 3 candidate). Same reasoning. |
| `dosId`, `dosEntityName`, `entityType`, `jurisdiction`, `initialFilingDate`, `processName`, `processAddress`, `processAddressLineTwo`, `processCity`, `processState`, `processZip`, `registeredAgentName`, `registeredAgentAddress`, `registeredAgentAddressLineTwo`, `registeredAgentCity`, `registeredAgentState`, `registeredAgentZip` domain `DosEntity` | Each appears only on DOS entities in the graph. |
| `dosId`, `dosEntityName`, `entityType`, `jurisdiction`, `initialFilingDate`, `processName`, `processAddress`, `processAddressLineTwo`, `processCity`, `processState`, `processZip`, `registeredAgentName`, `registeredAgentAddress`, `registeredAgentAddressLineTwo`, `registeredAgentCity`, `registeredAgentState`, `registeredAgentZip` functional | Single-valued in the graph: one per DOS record, absent (never multiple) when blank. A shared name gives two records, not two values. |

### Rules for Stage 6 shapes

- `dosId` is a positive integer, unique and present on every DOS entity; `dosEntityName`, `entityType` and `initialFilingDate` are present on every one.
- `jurisdiction`, the process parts and the agent parts are absent when blank, never an empty string.
- `initialFilingDate` is not in the future relative to the snapshot (2026-07-06).
- A DOS entity has no relationship to an owner contact, grantee or registration.
- The statutory default process names are kept as recorded; none is dropped or replaced.
- Address parts and `registeredAgentState` are stored as recorded; an agent state without an agent name is allowed.
- Every DOS entity's name key equals the N3 key of at least one `CorporateOwner` owner name or grantee name in the graph (scope rule; checked in Cypher, not OWL).

### Answer fields

Each field of `profiles/q05.yaml` against the ontology.

| Answer field | Ontology | Note |
| --- | --- | --- |
| `dosId` | `dosId` | |
| `name` | `dosEntityName` | graph name `DosEntity.name` |
| `entityType`, `jurisdiction` | `entityType`, `jurisdiction` | |
| `filingDate` | `initialFilingDate` | graph name `DosEntity.filingDate` |
| `candidates` | `DosEntity` | all records sharing the key; empty means "no record in the active-entity snapshot"; derived at query time |
| `nameAgreement`, `rule` | not modeled | computed by `compare.py` at answer time |
| `snapshotDate` | dataset-level | provenance in `data/sources.yaml` (2026-07-06) |
| `processName` | `processName` | |
| `processAddress` | `processAddress`, `processAddressLineTwo`, `processCity`, `processState`, `processZip` | graph names `processAddressLine2` etc. |
| `agentName` | `registeredAgentName` | graph name `DosEntity.agentName` |
| `agentAddress` | `registeredAgentAddress`, `registeredAgentAddressLineTwo`, `registeredAgentCity`, `registeredAgentState`, `registeredAgentZip` | graph names `agentAddress` etc. |

### Reasoner and example data

- ROBOT with HermiT, as for Q1 to Q4 (versions recorded by `make versions`).
- `abox/q05.ttl` (verified fixtures; person names not repeated).
- Negative cases, each meant to be flagged inconsistent: `n13` (DOS entity that is a contact), `n14` (that is a grantee), `n15` (two DOS ids on one record).

### Pitfall scan

Pending: `make oops` (TBox only) failed on 2026-11-13 because oops.linkeddata.es was unreachable (timeout from `make oops` and from curl; the site did not load in a browser). Retry later. Expected: P13 (now 6 properties, unchanged, no new object property) and possibly P32 (same label on several properties: the 10 address parts, by design).

## Q8

### Scope

Adds two classes (`OperationalNetwork`, `Landlord`), six object properties (`inNetwork`, `covers`, `basedOnContact`, `connectedByName`, `connectedByAddress`, `connectedByIdentity`) and four datatype properties (`groupId`, `networkSplit`, `networkAbsence`, `networkAbsenceDetail`) plus `linkWeight`. `TaxLot` is reused from Q1 and gains `inNetwork`, `networkAbsence` and `networkAbsenceDetail`. Elements follow `profiles/q08.yaml`. `linkWeight` is a property of a link between two landlord records. OWL cannot attach a datatype property to an object property, so it has no domain (as `lastRegistered` is handled in Q2, but there is no honest single class to put them on). `covers` carries a registration id in the graph; the ontology reuses `registrationId`, the id of the registration BOR used, and does not attach it to the relationship.

### Not modeled

| Term | Reason |
| --- | --- |
| `Landlord.nodeId`, `networkEdgeId`, `portfolioEdgeId`, `evidenceId` | Run-local identity keys only, never answer fields. The release holds the evidence they name. |
| Cleaned or merged names and addresses | Both are kept as the release spells them. Spelling variants of one address (BROOKLYN, BROOKYLN, Brooklyn) are separate values; the ontology does not infer that two spellings are the same address. |
| Which landlord business address is the "main" one | None is preferred; the answer lists them all. |
| Run, release and snapshot | Dataset-level provenance in `data/sources.yaml`. |
| Network split and absence reasons as classes or individuals | Stored as BOR's codes in string properties, like `contactType`. The values stay SKOS schemes (`network-splits`, `network-absence-reasons`); the hierarchy of reasons lives in the vocabulary only. |
| Member lot, building and residential unit counts | Computed at query time from `inNetwork`, `hasBuilding` and `residentialUnits`. |
| A class for the link, and `symmetric` on the four link properties | The link is one stored direction (lower id first) with no meaning in the order. A link class would add elements with no concept; symmetry would infer a second edge the graph does not hold. |
| Network group id on a link, and whether a link crosses a boundary | `networkGroupId` and `portfolioGroupId` on a link say which group both ends sit in. The ontology reaches groups through lots (`covers`, `inNetwork`, `inPortfolio`); a boundary link is a link with no group id, found in the graph, not inferred. |
| Beneficial owner | Idea for later: a shared meaning for `Landlord`. Not modeled now; a landlord record is not proof of ownership. |

### Axioms

| Axiom | Reason |
| --- | --- |
| `OperationalNetwork` disjointWith `TaxLot` | A group is not a parcel. Rejects a lot standing in for its network. |
| `OperationalNetwork` disjointWith `Landlord` | A group is not a record in it. |
| `Landlord` disjointWith `TaxLot` | A landlord record is not a parcel. |
| `Landlord` disjointWith `Contact` | A landlord record is built from HPD contacts but is not one, and is not an owner (Stage 3 candidate). |
| `groupId`, `networkSplit` domain `OperationalNetwork` | Each appears only on networks in the graph. |
| `inNetwork`, `networkAbsence`, `networkAbsenceDetail` domain `TaxLot` | Each appears only on lots in the graph. |
| `covers`, `basedOnContact`, `connectedByName`, `connectedByAddress`, `connectedByIdentity` domain `Landlord` | Each starts only at a landlord record in the graph. |
| `landlordName`, `landlordBusinessAddress` domain `Landlord` | Each appears only on landlord records in the graph. |
| `landlordName`, `anchoredBy` functional | One name per landlord record; one anchor per group. `landlordBusinessAddress` is not functional: a record can have several. |

| `groupId`, `networkSplit`, `networkAbsence`, `networkAbsenceDetail` functional | One value per network or lot in the graph. |

`linkWeight` is not functional: a landlord record has many links, each with its own values.

### Rules for Stage 6 shapes

- `groupId` and `networkSplit` are present on every network; `networkSplit` is `wcc` or `louvain`; `groupId` is `ON-` followed by an integer, unique.
- A lot has at most one `inNetwork`; every network has at least two member lots and no lot is in a network that does not exist.
- `networkAbsence` and `networkAbsenceDetail` are both present or both absent, and absent on every lot in a network; each detail code belongs to its stated top-level reason (the hierarchy in the vocabulary).
- `networkAbsence` is one of the five top-level codes; `networkAbsenceDetail` one of the eleven detail codes.
- A landlord in a network covers one or more lots; each lot in a network is covered by one landlord; each `covers` has an integer `registrationId`. (Q9 relaxes "every landlord covers a lot": 115 portfolio landlords cover only co-op or condo lots outside the graph and appear only as link ends; see `queries/checks/q09-landlords.cypher`.)
- A `connectedByName`, `connectedByAddress` or `connectedByIdentity` link joins two different landlords, lower `nodeId` first, with a positive `linkWeight` (name 1.5 times the match, address 1.0 times, identity 100). A link has a network group id exactly when both ends sit in one network; every network has at least one link inside it.
- No lot in a network is covered by a landlord outside that network.

### Answer fields

Each field of `profiles/q08.yaml` against the ontology.

| Answer field | Ontology | Note |
| --- | --- | --- |
| `networkId` | `groupId` | graph name `OperationalNetwork.groupId` |
| `anchor` | `anchoredBy`, `landlordName` | graph name `ANCHORED_BY`; the node id is identity only |
| `split` | `networkSplit` | graph name `OperationalNetwork.split` |
| `lots` | `inNetwork`, `TaxLot` | lots with `inNetwork` to the network |
| `buildings` | `hasBuilding` | counting unit BINs |
| `residentialUnits` | `residentialUnits` | derived: sum over member lots |
| `selectedContacts` | `basedOnContact`, `hasContact`, `registrationId`, `contactType` | graph name `BASED_ON_CONTACT`; the contact's registration through `HAS_CONTACT`; distinct contacts |
| `landlords` | `Landlord`, `landlordName`, `landlordBusinessAddress`, `covers`, `registrationId` | graph names `Landlord.name`, `Landlord.businessAddresses` (a list) and `COVERS.registrationId` |
| `links` | `connectedByName`, `connectedByAddress`, `connectedByIdentity`, `linkWeight` | edge ids, `evidenceId` and the node ids are identity only; the graph name of `linkWeight` is `weight` |
| `networkAbsence` | `networkAbsence` | |
| `networkAbsenceDetail` | `networkAbsenceDetail` | |

### Reasoner and example data

- ROBOT with HermiT, as for Q1 to Q5 (versions recorded by `make versions`).
- `abox/q08.ttl` (verified fixtures; weights and names left out).
- Negative cases, each meant to be flagged inconsistent: `n16` (landlord that is a contact), `n17` (network that is a lot), `n18` (two network ids), `n19` (two absence reasons).

### Pitfall scan

Scanned together with Q9 (see Q9 below): no critical pitfall.

## Q9

### Scope

Adds one class (`OwnerPortfolio`), two new object properties (`inPortfolio`, `connectedByDeed`; `connectedByIdentity` is shared with Q8) and six datatype properties (`portfolioId`, `portfolioComposition`, `portfolioAbsence`, `portfolioAbsenceDetail`, `ownershipSignal`, `evidenceType`). `Landlord`, `covers` and `TaxLot` are reused from Q8 and Q1: one shared landlord layer holds the landlord records of both layers. `portfolioId` is a separate property from Q8's `groupId` (its domain is `OperationalNetwork`), because the two ids are different identifiers with different graph names. `ownershipSignal` and `evidenceType` belong to a link between two landlord records; OWL cannot attach a datatype property to an object property, so they have no domain (as the Q8 `linkWeight`). Elements follow `profiles/q09.yaml`.

### Not modeled

| Term | Reason |
| --- | --- |
| Portfolio composition, signal and absence reasons as classes or individuals | Stored as BOR's codes in string properties, like `networkSplit`. The values stay SKOS schemes (`portfolio-compositions`, `ownership-signals`, `network-absence-reasons`); the hierarchy of reasons lives in the vocabulary only. |
| Member lot, building and residential unit counts, and the portfolio-versus-network differences | Computed at query time from `inPortfolio`, `inNetwork`, `hasBuilding` and `residentialUnits`. |
| Co-op and condo lots outside the footprint | Not given an `inPortfolio` link; they carry the absence reason `coop_condo_excluded`. |
| A class for the link | As Q8: one stored direction, no meaning in the order. A link is evidence the method counted, not a statement that the two records are one owner. |
| The evidence a link cites (cluster members, set members, deed parcels, model probabilities) | Not in the loaded graph; `evidenceType` and `evidenceId` name the release record. |
| Run, release and snapshot | Dataset-level provenance in `data/sources.yaml`. |

### Axioms

| Axiom | Reason |
| --- | --- |
| `OwnerPortfolio` disjointWith `TaxLot` | A group is not a parcel. |
| `OwnerPortfolio` disjointWith `Landlord` | A group is not a record in it. |
| `OwnerPortfolio` disjointWith `OperationalNetwork` | The two kinds of group are different entities with different ids, even though a lot can be in both and their members overlap. The Stage 3 candidate was rejected for lots in both groupings; the groups themselves are never the same individual, and the agent must not swap them. |
| `portfolioId`, `portfolioComposition` domain `OwnerPortfolio` | Each appears only on portfolios in the graph. |
| `inPortfolio`, `portfolioAbsence`, `portfolioAbsenceDetail` domain `TaxLot` | Each appears only on lots in the graph. |
| `connectedByDeed` domain `Landlord` | It starts only at a landlord record in the graph. |
| `portfolioId`, `portfolioComposition`, `portfolioAbsence`, `portfolioAbsenceDetail` functional | One value per portfolio or lot in the graph. |

`ownershipSignal` is not functional: a landlord record has many links, each with its own signal.

### Rules for Stage 6 shapes

- `portfolioId` and `portfolioComposition` are present on every portfolio; composition is `identity`, `deed_only` or `deed_bridged`; `portfolioId` is `OP-` followed by an integer, unique.
- A lot has at most one `inPortfolio`; every portfolio has at least one member rental lot (53 have exactly one); no lot is in a portfolio that does not exist.
- `portfolioAbsence` and `portfolioAbsenceDetail` are both present or both absent, and absent on every lot in a portfolio; each detail code belongs to its stated top-level reason (the hierarchy in the vocabulary); the top level is one of five codes and the detail one of the 18 codes used in this layer.
- `coop_condo_excluded` lots have no `inPortfolio`.
- A `connectedByIdentity` or `connectedByDeed` link joins two different landlords and has one `ownershipSignal` among the six codes and one `evidenceType`; every portfolio with more than one landlord record has links that connect its landlord records (15,338 kept portfolio edges in the release, 14,315 identity and 1,023 deed in the graph).
- Each landlord record covers lots only in layers it belongs to: a landlord in a portfolio and in a network may cover lots in either layer. The Q8 rule "no lot in a network is covered by a landlord outside that network" holds only for lots in networks; portfolio-only landlords (111) cover lots in no network.
- A link with a portfolio group id joins landlords of the same portfolio; a link with none is a boundary link or sits in a group the release dropped.

### Answer fields

Each field of `profiles/q09.yaml` against the ontology.

| Answer field | Ontology | Note |
| --- | --- | --- |
| `portfolioId` | `portfolioId` | graph name `OwnerPortfolio.groupId` |
| `anchor` | `anchoredBy`, `landlordName` | graph name `ANCHORED_BY`; shared with Q8; the node id is identity only |
| `composition` | `portfolioComposition` | graph name `OwnerPortfolio.composition` |
| `lots` | `inPortfolio`, `TaxLot` | lots with `inPortfolio` to the portfolio |
| `buildings` | `hasBuilding` | counting unit BINs |
| `residentialUnits` | `residentialUnits` | derived: sum over member lots |
| `links` | `connectedByIdentity`, `connectedByDeed`, `ownershipSignal`, `evidenceType` | graph name of the signal is `stage`; edge ids, `evidenceId` and node ids are identity only |
| `signal` | `ownershipSignal` | |
| `portfolioLots` | `inPortfolio` | derived: count of member lots |
| `networkLots` | `inNetwork` | derived: count of member lots of the network |
| `inBoth` | `inPortfolio`, `inNetwork` | derived: lots with both |
| `portfolioOnlyLots` | `inPortfolio`, `inNetwork` | derived: lots in the portfolio and not in the network |
| `networkOnlyLots` | `inPortfolio`, `inNetwork` | derived: lots in the network and not in the portfolio |
| `portfolioAbsence` | `portfolioAbsence` | |
| `portfolioAbsenceDetail` | `portfolioAbsenceDetail` | |

### Reasoner and example data

- ROBOT with HermiT, as for Q1 to Q8 (versions recorded by `make versions`).
- `abox/q09.ttl` (verified fixtures; names and link evidence left out).
- Negative cases, each meant to be flagged inconsistent: `n20` (portfolio that is a network), `n21` (two portfolio ids), `n22` (two compositions), `n23` (two absence reasons), `n24` (portfolio that is a landlord).

### Pitfall scan

Run 2026-11-13 (`make oops`, TBox only, whole ontology): two pitfalls, none critical.

- P11 (important), kept: `linkWeight` (Q8), `ownershipSignal` and `evidenceType` (Q9). Each is a property of a link between two landlord records. OWL cannot attach a datatype property to an object property, and no class is an honest domain (a domain would infer that every landlord record has the property). The graph stores them on the relationship; the shapes in Stage 6 check them there.
- P13 (minor), kept: no inverse is declared for the 11 object properties. The graph stores one direction, and an inverse would imply edges it does not hold.

## Q6

### Scope

Adds three classes (`NetworkMaskedAddress`, `PortfolioMaskedAddress`, `MailDropAddress`) and the datatype properties of each (the Q6.3 class adds `portfolioMaskedAddressText`, `portfolioMaskedAddressDegree`, `maskedIdentities`), with no object property: the two classifications are matched to HPD contact addresses by text at query time, and the graph holds no relationship to them (user decision 2026-11-13). Q6.1 adds nothing: contacts, registrations and buildings at an address are counted from `mailingAddress`, `addressLine2` and `zipCode` on `Contact`, and `hasContact`, `hasRegistration`. Elements follow `profiles/q06.yaml`. `MailDropAddress.listKey` is identity only.

### Not modeled

| Term | Reason |
| --- | --- |
| `MailDropAddress.listKey` | Identity key only, never an answer field. |
| Mask method, threshold, unit and normalizer version | One value each for the release; recorded once in `data/sources.yaml`, not on each address. |
| The identities behind a portfolio mask | The release records the mask on identities (5298 events). The graph keeps only the derived address text, its degree and the identity count; no identity node or link exists. |
| Mail-drop kind and review status as classes or individuals | Stored as the list's codes in string properties, like `contactType`. The values stay SKOS schemes (`mail-drop-kinds`, `list-review-statuses`). |
| A relationship from a masked or listed address to an HPD contact | Matching is by text (street line plus second line for a mask, the list's key spelling for the list), computed at query time; a stored link would hide that rule. |
| The address key of Q6.1 and the counts | Computed at query time. |

### Axioms

| Axiom | Reason |
| --- | --- |
| `PortfolioMaskedAddress` disjointWith `NetworkMaskedAddress` | Two methods' masks of an address, each its own decision; the nodes are never the same individual even when the texts coincide (30 do). |
| `PortfolioMaskedAddress` disjointWith `MailDropAddress` | Two classifications by different authorities. |
| `PortfolioMaskedAddress` disjointWith `Contact` | A masked address is not an HPD contact. |
| `portfolioMaskedAddressText`, `portfolioMaskedAddressDegree`, `maskedIdentities` domain `PortfolioMaskedAddress` | Each appears only on portfolio masked addresses in the graph. |
| `portfolioMaskedAddressText`, `portfolioMaskedAddressDegree`, `maskedIdentities` functional | One value per node in the graph. |
| `NetworkMaskedAddress` disjointWith `MailDropAddress` | Two classifications by different authorities; one node is one classification. The texts may coincide, but the nodes are never the same individual (Stage 3 candidate). |
| `NetworkMaskedAddress` disjointWith `Contact` | A masked address is not an HPD contact. |
| `MailDropAddress` disjointWith `Contact` | A listed address is not an HPD contact (Stage 3 candidate). |
| `maskedAddressId`, `maskedAddressText`, `maskedAddressDegree`, `maskedEdges` domain `NetworkMaskedAddress` | Each appears only on masked addresses in the graph. |
| `mailDropAddressKey`, `zipFive`, `mailDropKind`, `mailDropBasis`, `listReviewStatus` domain `MailDropAddress` | Each appears only on listed addresses in the graph. |
| `maskedAddressId`, `maskedAddressText`, `maskedAddressDegree`, `maskedEdges`, `mailDropAddressKey`, `zipFive`, `mailDropKind`, `mailDropBasis`, `listReviewStatus` functional | One value per node in the graph. |

### Rules for Stage 6 shapes

- Every masked address has `addressId` (`A` followed by seven digits, unique), a non-blank `address` (unique) and an integer `degree` above 25.
- Every listed address has a non-blank `address`, a `kind` of the four codes and a `basis`; `reviewStatus` is `unreviewed`; `zip5` is five digits or absent; `address` with `zip5` is unique (`listKey`).
- Every portfolio masked address has a non-blank derived `address` (unique), an integer `degree` above 25 and at least one masked identity; the identity counts sum to 5298.
- No node carries two of the three address labels (network masked, portfolio masked, listed).
- None of the three node types has any relationship.

### Answer fields

Each field of `profiles/q06.yaml` against the ontology.

| Answer field | Ontology | Note |
| --- | --- | --- |
| `contacts` | `Contact`, `mailingAddress`, `zipCode` | derived: count of contacts with the street line and first five ZIP characters |
| `ownerContacts` | `Contact`, `contactType` | derived: count of contacts with an owner type |
| `roleContacts` | `Contact`, `contactType` | derived: count of contacts with a non-owner type |
| `registrations` | `hasContact` | derived: distinct registrations of those contacts |
| `buildings` | `hasRegistration` | derived: distinct BINs of those registrations |
| `addressId` | `maskedAddressId` | graph name `NetworkMaskedAddress.addressId` |
| `address` (Q6.2) | `maskedAddressText` | graph name `NetworkMaskedAddress.address` |
| `degree` | `maskedAddressDegree` | |
| `maskedEdges` | `maskedEdges` | address links set aside at the mask, counted from the release; the edges are not stored |
| `maskedIdentities` | `maskedIdentities` | Q6.3: identities masked at the derived text; the graph name is `PortfolioMaskedAddress.maskedIdentities` |
| `hpdContacts` | `mailingAddress`, `addressLine2`, `Contact` | derived: contacts whose street line plus second line equals the text |
| `hpdZips` | `zipCode` | derived: distinct first five characters |
| `address` (Q6.4) | `mailDropAddressKey` | graph name `MailDropAddress.address` |
| `listZip` | `zipFive` | graph name `MailDropAddress.zip5` |
| `kind` | `mailDropKind` | |
| `basis` | `mailDropBasis` | |
| `reviewStatus` | `listReviewStatus` | |

Q6.3 answer fields: `address` (`portfolioMaskedAddressText`), `degree` (`portfolioMaskedAddressDegree`), `maskedIdentities`, `hpdContacts` and `hpdZips` (computed at query time, as Q6.2).

### Reasoner and example data

- ROBOT with HermiT, as for Q1 to Q9 (versions recorded by `make versions`).
- `abox/q06.ttl` (verified fixtures; counts left out because they are derived).
- Negative cases, each meant to be flagged inconsistent: `n25` (masked address that is a mail-drop address), `n26` (two masked ids), `n27` (two kinds), `n28` (listed address that is a contact), `n31` (portfolio mask that is a network mask), `n32` (two portfolio degrees).

### Pitfall scan

Run 2026-11-13 (`make oops`, whole ontology): the same two pitfalls as for Q8 and Q9 and nothing new (P11 on the link properties, kept; P13, kept). No Q6 element is affected.

## Q7

### Scope

Adds two classes (`Document`, `DocumentParty`), one object property (`hasParty`) and six datatype properties (`partyName`, `partyRole`, `addressPartyCount`, `addressDocumentCount`, `processAddressEntities`, plus the reuse below). `documentId`, `documentType`, `documentDate`, `recordedDate` and `documentAmount` are reused from Q3, and `mailingAddress`, `addressLineTwo` and `zipCode` from Q3 and Q4, with their domains widened to a union that includes the new class. `partyRole` belongs to the link between a document and a party; OWL cannot attach a datatype property to an object property, so it has no domain (as `linkWeight`). Elements follow `profiles/q07.yaml`, `profiles/q02.yaml` (`Contact.nameKey`) and `profiles/q05.yaml` (`DosEntity.processAddressEntities`).

### Not modeled

| Term | Reason |
| --- | --- |
| `DocumentParty.partyKey`, `DocumentParty.nameKey`, `Contact.nameKey` | Loader and lookup keys, identity only, never answer fields. |
| shared addresses, shared people, set aside, grouping and links of Q7.1 to Q7.5 | Found or derived at answer time from stored values; the Q7 profile records them as not stored. |
| Document types as classes | `documentType` is a string as ACRIS spells it; no answer needs a subclass per type. |

### Axioms

| Axiom | Reason |
| --- | --- |
| `Document` disjointWith `Registration` | A recorded document is not an HPD registration. Rejects one node carrying both. |
| `Document` disjointWith `DocumentParty` | A document is not a party recorded on it. |
| `DocumentParty` disjointWith `Contact` | A party on an ACRIS document is not an HPD contact; a name match is a lead, never identity. |
| `DocumentParty` disjointWith `Grantee` | A document party is not a deed grantee; the Q3 and Q7 layers stay apart. |
| `hasParty` domain `Document` | Only documents have parties in the graph. |
| `partyName`, `addressPartyCount`, `addressDocumentCount` domain `DocumentParty` | Each appears only on document parties. |
| `processAddressEntities` domain `DosEntity` | Appears only on DOS entities. |
| `partyName`, `addressPartyCount`, `addressDocumentCount`, `processAddressEntities` functional | Single-valued: one value per party or record, absent when blank. |

`partyRole` is not functional: a party can hold more than one role on a document (one link per role). `hasParty` is not functional (a document has many parties).

### Rules for Stage 6 shapes

- Every document has a `documentId` and at least one party (scope C documents have two or more by construction; 19 mortgages in scope M record a single party, kept as recorded); every document party belongs to exactly one document and has at least one `hasParty` link with a `partyRole` of 1, 2 or 3.
- `partyName` and the address properties are absent when blank, never an empty string.
- `addressDocumentCount` is a positive integer and `addressPartyCount` a non-negative integer (names with no letter are not counted; one party is named a backtick); both are present exactly when `mailingAddress` is present.
- `processAddressEntities` is a positive integer present exactly when `processAddress` is present.
- A document party is never an HPD contact, a grantee or a registration.

### Answer fields

Each field of `profiles/q07.yaml` against the ontology.

| Answer field | Ontology | Note |
| --- | --- | --- |
| `registrationsA`, `registrationsB` | `hasContact`, `hasRegistration` | derived: registrations with a contact whose name key equals the given name |
| `sharedAddresses` | `mailingAddress`, `zipCode`, `hasContact` | derived: street line plus first five ZIP characters on contacts of both sides' registrations |
| `sharedPeople` | `personName`, `hasContact` | derived: equal person names on both sides' registrations; never repeated outside the answer |
| `typesA` | `contactType` | the contact types on a side at a shared item |
| `recordsA`, `recordsB` | `DosEntity`, `processAddress` | records found by name key, with the process address parts |
| `entities` | `processAddressEntities` | graph name `DosEntity.processAddressEntities` |
| `sharedPairs` | `processAddress`, `processZip` | derived: equal street line and first five ZIP characters |
| `documents` | `hasParty` | documents with a party of each given name, newest recorded date first |
| `documentId`, `docType`, `recordedDate` | `documentId`, `documentType`, `recordedDate` | graph names `Document.documentId`, `Document.docType`, `Document.recordedDate` |
| `parties` | `hasParty` | all parties of the document, the two given ones marked |
| `name` | `partyName` | graph name `DocumentParty.name` |
| `partyType` | `partyRole` | graph name `HAS_PARTY.partyType`; the recorded code |
| `addressNames`, `addressDocuments` | `addressPartyCount`, `addressDocumentCount` | graph names `DocumentParty.addressNames`, `DocumentParty.addressDocuments` |
| `networkMask`, `portfolioMask`, `mailDrop` | `NetworkMaskedAddress`, `PortfolioMaskedAddress`, `MailDropAddress` | reported apart, each with its own reason |
| `setAside`, `listNotConsulted` | not modeled | derived at answer time from the three classifications |
| `lotsA` | `inNetwork`, `inPortfolio`, `networkAbsence`, `portfolioAbsence` | lots of a side with their groups and BOR reasons |
| `landlordsA` | `covers` | landlord records covering the lots |
| `links` | `connectedByIdentity`, `connectedByDeed`, `connectedByName`, `connectedByAddress`, `linkWeight` | every link between a landlord of each side, with weight and evidence |

### Reasoner and example data

- ROBOT with HermiT, as for Q1 to Q9 (versions recorded by `make versions`).
- `abox/q07.ttl` (verified fixtures; person names not repeated).
- Negative case meant to be flagged inconsistent: `n33` (a document party that is an HPD contact).

### Pitfall scan

Run 2026-11-16 (`make oops`, whole ontology): the same two pitfalls, each one element larger. P11 (5 properties): `partyRole` joins `anchoredBy`, `evidenceType`, `linkWeight` and `ownershipSignal`; like them it is a property of a link, which OWL cannot attach to a relationship, so it has no domain on purpose (accepted). P13 (17 properties): `hasParty` joins the others; the graph stores one direction and can be traversed both ways (accepted). Nothing else.

## Q11

### Scope

Adds no class, property or controlled value. Q11 reads the existing elements: `Document` (with `documentType` MTGE), `DocumentParty`, `hasParty`, `partyName` and `partyRole` (Q7 and Q11.1); `Registration`, `hasContact`, `Contact` and `contactType` (Q2 to Q4); `DosEntity` and the process properties (Q5); `inNetwork`, `inPortfolio`, `networkAbsence` and `portfolioAbsence` (Q8, Q9). No mapping row, axiom or negative case is added, and `profiles/q11.yaml` declares no graph element.

### Not modeled

| Term | Reason |
| --- | --- |
| `affiliation`, the five affiliation types, the three evidence statuses | Answer-contract values computed at answer time from the recorded role or the source (`profiles/q11.yaml` not_stored). Stage 1 decided against storing a third copy of the facts, and no graph element holds them. They stay SKOS concepts in `affiliation-types` and `evidence-statuses`, not ontology controlled values. |
| `mortgage`, `borrower`, `lender` | A mortgage is a `Document` whose `documentType` is MTGE, and a borrower or lender is the recorded `partyRole` code 1 or 2 on it. A class per document type or per role would be a subclass of nothing the graph can state (decision in Q7: `documentType` is a string). |
| shared borrower | Computed from the borrowers on one mortgage. |
| parent company and reported claims | No source documents a parent, and reported claims are session evidence (Q11.5, pending a cache). |

### Axioms

| Axiom | Reason |
| --- | --- |

None added. Disjointness candidates from `taxonomy-notes.md`: none proposed.

### Rules for Stage 6 shapes

- A `Document` whose `documentType` is MTGE has only parties with `partyRole` 1 or 2 (checked on the graph: `tests/q11_1/check_mortgages.py`).
- Every MTGE `Document` names at least one HPD CorporateOwner name by N3 on a party (scope M; `profiles/q07.yaml`).
- The affiliation type and evidence status are never stored on a graph element (the declared properties of `Document`, `Contact`, `DosEntity` and `Lot` carry neither).

### Answer fields

| Answer field | Ontology | Note |
| --- | --- | --- |
| `givenRoles` | `partyRole`, `hasParty` | the party type of the party named by the given name; 1 borrower, 2 lender on a mortgage |
| `docDate`, `recordedDate` | `documentDate`, `recordedDate` | graph names `Document.docDate`, `Document.recordedDate` |
| `amount` | `documentAmount` | graph name `Document.amount`; whole dollars |
| `affiliationType`, `evidenceStatus` | not modeled | computed at answer time from the role or source; SKOS values in `affiliation-types` and `evidence-statuses` |
| `registrationId` | `registrationId` | graph name `Registration.registrationId` |
| `givenTypes`, `others` | `contactType`, `corporationName`, `personName`, `contactTitle`, `mailingAddress`, `zipCode`, `hasContact` | the entity's own roles and every other contact of the registration; a person name is for the answer only |
| `dosId`, `filingDate`, `entityType`, `jurisdiction` | `dosId`, `initialFilingDate`, `entityType`, `jurisdiction` | graph names `DosEntity.*` |
| `processName`, `processAddress`, `processZip`, `entities` | `processName`, `processAddress`, `processZip`, `processAddressEntities` | the process contact and the hub count over the whole active-entity table |
| `bbl`, `networkGroupId`, `networkSplit`, `portfolioGroupId`, `portfolioComposition`, `networkAbsence`, `portfolioAbsence` | `inNetwork`, `inPortfolio`, `networkAbsence`, `portfolioAbsence` | lots of the entity with their groups and BOR reasons, as Q7.5 |
| `networkLots`, `portfolioLots` | not modeled | member counts computed from `inNetwork` and `inPortfolio` (Q10) |

### Reasoner and example data

- ROBOT with HermiT, as for Q1 to Q9 (versions recorded by `make versions`).
- `abox/q11.ttl` (verified fixtures; person names not repeated).
- No negative case: Q11 adds no axiom.

### Pitfall scan

Not run for Q11: the TBox is unchanged since the last scan (2026-11-16), so there is nothing new to submit.


## Q12

### Scope

Adds one class (`Grantor`), one object property (`hasGrantor`) and one functional datatype property (`grantorName`). `mailingAddress`, `addressLineTwo` and `zipCode` gain `Grantor` in their domain union. Elements follow `profiles/q12.yaml`. Everything else Q12 reads is existing: `Deed`, `hasDeed`, `hasGrantee`, the deed properties (Q3), `Contact` and `contactType` (Q2), `inPortfolio`, `portfolioGroupId` and `portfolioComposition` (Q9).

### Not modeled

| Term | Reason |
| --- | --- |
| `Grantor.partyKey` | A loader key. Identity only, never an answer field. |
| `Grantor.nameKey`, `Grantee.nameKey` | Lookup keys (rule N3), identity only (`profiles/q12.yaml`); the comparison is computed at answer time. |
| `not-a-sale`, `notSale`, `notSaleCount` | Derived at answer time from `documentAmount` and `documentType` (decision 2026-11-16). Storing it would assert more than the recorded amount supports. |
| `attributable-transfer`, `attributable`, `ownerNotComparable`, `granteeMatches`, `grantorMatches` | Type II name leads computed at answer time by rule N3. Current registration is not historical ownership. |
| `deedCount`, `otherLots`, the period | Counts and a recorded-date filter, computed from `hasDeed` and `recordedDate`. |
| portfolio deed set | Computed from `inPortfolio` and `hasDeed`. |

### Axioms

| Axiom | Reason |
| --- | --- |
| `Grantor` disjointWith `Contact` | A grantor is not an HPD contact (Stage 3 candidate). Keeps the two sides of the comparison apart. |
| `Grantor` disjointWith `Grantee` | A party row has one role on one deed; the same name on both sides is two nodes. |
| `Grantor` disjointWith `DosEntity` | A deed party is not a DOS record; a name match is a lead. |
| `Grantor` disjointWith `DocumentParty` | A grantor is not a Q7 document party row; the two are separate nodes. |
| `hasGrantor` domain `Deed` | Appears only from deeds in the graph (checked by `make profiles`). |
| `grantorName` domain `Grantor` | Appears only on grantors in the graph. |
| `grantorName` functional | One recorded name per party row; absent when blank. |

The domain unions of `mailingAddress`, `addressLineTwo` and `zipCode` now include `Grantor` (rows under Q3 updated): the same party-address properties, one property for all.

`hasGrantor` is not functional (a deed can have several grantors or none).

### Rules for Stage 6 shapes

- Every `Grantor` has exactly one `Deed` (`hasGrantor`); `grantorName` and the address properties are absent when blank, never an empty string.
- A deed's grantors and grantees are separate nodes, even with the same name.
- `nameKey` on `Grantor` and `Grantee` is rule N3 applied to the name, absent when the name is blank or only periods, commas and apostrophes.
- 1,619,378 grantors on the loaded deeds (profile in `scripts/profile_q12_scope.py`).
- No node or relationship stores a not-a-sale flag, an attribution or a count.

### Answer fields

| Answer field | Ontology | Note |
| --- | --- | --- |
| `documentId`, `docType`, `docDate`, `recordedDate`, `amount` | `documentId`, `documentType`, `documentDate`, `recordedDate`, `documentAmount` | as Q3 |
| `notSale`, `notSaleCount`, `deedCount`, `otherLots` | not modeled | derived at answer time |
| `grantors` | `hasGrantor`, `grantorName`, `mailingAddress`, `addressLineTwo`, `zipCode` | graph names `Grantor.name`, `addressLine2`, `zip`; a person's name is for the answer only |
| `grantees` | `hasGrantee`, `granteeName` and the address properties | as Q3 |
| `portfolioGroupId`, `portfolioComposition`, `portfolioLots` | `portfolioGroupId`, `portfolioComposition`, `inPortfolio` | as Q9; run 2026-05-29-869bd299 |
| `deeds`, `lots` | `hasDeed` | distinct deeds over the member lots |
| `bbl` | `bbl` | from Q1 |
| `corporateOwners` | `hasRegistration`, `hasContact`, `contactType` | CorporateOwner contacts, counted by name key at answer time |
| `ownerNotComparable`, `granteeMatches`, `grantorMatches`, `attributable` | not modeled | Type II, computed at answer time |

### Reasoner and example data

- ROBOT with HermiT, as for Q1 to Q11 (versions recorded by `make versions`).
- `abox/q12.ttl` (verified fixtures; entity names only).
- Negative cases, each meant to be flagged inconsistent: `n34` (a grantor that is a grantee), `n35` (two grantor names).

### Pitfall scan

`make oops` run 2026-11-17 (TBox only): P11 (5 relationship properties without a domain: `linkWeight`, `anchoredBy`, `ownershipSignal`, `evidenceType`, `partyRole`; accepted) and P13 (18 properties without inverses, including `hasGrantor`; minor, accepted). Nothing new for Q12.

## Q13

### Scope

Adds one object property (`hasFinancingDocument`). A financing document is a `Document` (Q7) with a `documentType` of MTGE, ASST, SAT, AGMT, AL&R, TL&R or SAGE; its parties are `DocumentParty` nodes (`hasParty`, `partyRole`). The `Document` comment now names the three load scopes (C, M, F) and traces Q11.1 and Q13.1. Elements follow `profiles/q13.yaml`. Reused: `Document`, `DocumentParty`, `hasParty`, `documentId`, `documentType`, `documentDate`, `recordedDate`, `documentAmount`, `partyName`, `partyRole`, the address properties, `bbl`.

### Not modeled

| Term | Reason |
| --- | --- |
| `financing-document` and the five kinds (`mortgage`, `assignment`, `satisfaction`, `termination`, `agreement`) as classes | Computed at answer time from `documentType` (answer contract `tests/q13_support.py`). No answer needs a subclass; the kind wording is the project's, not ACRIS's. Mapped to `Document` in the table. |
| borrower and lender | `partyRole` 1 and 2 on a document of type MTGE only; named at answer time. |
| `otherLots`, counts by kind, `description`, `kind` | Derived from `hasFinancingDocument` and `documentType`. |
| outstanding loan | Not a recorded fact; the answer lists documents only. |

### Axioms

| Axiom | Reason |
| --- | --- |
| `hasFinancingDocument` domain `TaxLot` | The graph links only lots to financing documents (checked by `make profiles`). |
| `hasFinancingDocument` range `Document` | The target is always a `Document` node. |

`hasFinancingDocument` is not functional or inverse-functional: a lot has many documents and a document can name several lots (252,760 do). No subclass axiom.

### Rules for Stage 6 shapes

- Every `hasFinancingDocument` target has a `documentType` in the seven listed types, a `documentId`, a `recordedDate` where ACRIS has one, and at least one party.
- A document on several lots is one node linked from each lot.
- Absent `documentDate` stays absent (40% of documents); amount 0 is kept as recorded.
- 2,885,412 financing documents, 3,279,564 links, 7,345,721 party links. Scope F parties carry no hub counts.
- No node or relationship stores a kind, description, count or outstanding flag.
- The scope F load must not break the Q7 document shape (relax `queries/checks/q07-documents.cypher` and `tests/q7_3/check_documents.py` for scope F).

### Answer fields

| Answer field | Ontology | Note |
| --- | --- | --- |
| `documentId`, `docType`, `docDate`, `recordedDate`, `amount` | `documentId`, `documentType`, `documentDate`, `recordedDate`, `documentAmount` | as Q3 and Q7 |
| `otherLots` | not modeled | count of other `hasFinancingDocument` subjects of the same document |
| `parties`, `partyType` | `hasParty`, `partyName`, `partyRole`, `mailingAddress`, `addressLineTwo`, `zipCode` | a person's name is for the answer only |
| `role` | not modeled | derived on MTGE only: 1 borrower, 2 lender |
| `kind`, `description`, `documents`, `byKind` | not modeled | answer contract and counts |

### Reasoner and example data

- ROBOT with HermiT, as for Q1 to Q12 (versions recorded by `make versions`).
- `abox/q13.ttl` (verified fixtures; no names).
- Negative case, meant to be flagged inconsistent: `n36` (a building linked to a financing document, against the `TaxLot` domain).

### Pitfall scan

`make oops` run 2026-11-17 (TBox only): user-reported nothing new beyond P11 and P13 (`hasFinancingDocument` has no inverse; minor, accepted). `make profiles` passes (user-reported).

## Q14

### Scope

Adds no class, property or controlled value. Q14 reads existing elements: `TaxLot`, `hasDeed`, `Deed`, `documentId`, `documentType`, `documentDate`, `recordedDate`, `documentAmount`, `hasGrantee`, `Grantee`, `granteeName` (Q3, Q12); `hasBuilding`, `Building`, `bin`, `hasRegistration`, `Registration`, `registrationId`, `lastRegistered`, `registrationEnd`, `hasContact`, `Contact`, `contactType`, `corporationName`, `personName` (Q1, Q2, Q4). No mapping row, axiom or negative case is added, and `profiles/q14.yaml` declares no graph element. Violations are not loaded (decision 2026-11-17).

### Not modeled

| Term | Reason |
| --- | --- |
| `supporting-deed`, `registration-in-force`, `title-registration-relation`, `date-basis` | Roles or answer states computed from a date the caller supplies (`profiles/q14.yaml` not_stored). A deed is supporting only for one date and basis; no graph element holds it. They stay SKOS concepts, not ontology elements, and the status and relation values are plain enums. |
| violation and its dates | Not loaded (1,970,575 rows). The date is an input from a source tool, and the caller says which one counts. |
| `recordedAfterDate`, `confirmatory`, `docDateAbsent`, registration status, relation | Computed at answer time from the deed's dates and type, the registration's dates and name keys (rule N3). A relation is a name lead, never a finding. |
| registration start, earlier filings | The source has neither; the answer states that the records are today's version of the past. |

### Axioms

| Axiom | Reason |
| --- | --- |

None added. Disjointness candidates from `taxonomy-notes.md`: none proposed.

### Rules for Stage 6 shapes

- No Q14 element is stored, so no new shape. The existing deed, grantee and registration shapes cover the inputs.
- Registration status, supporting-deed flags and the title and registration relation are never stored on a graph element (no declared property of `Deed`, `Registration` or `Contact` carries them).
- `tests/q14_1` to `q14_3` re-derive each answer from the frozen baseline and compare it with the graph lookups.

### Answer fields

| Answer field | Ontology | Note |
| --- | --- | --- |
| `documentId`, `docType`, `docDate`, `recordedDate`, `amount` | `documentId`, `documentType`, `documentDate`, `recordedDate`, `documentAmount` | graph names `Deed.documentId`, `Deed.docType`, `Deed.docDate`, `Deed.recordedDate`, `Deed.amount`; whole dollars as recorded |
| `effDate`, `basis`, `docDateAbsent`, `recordedAfterDate`, `confirmatory` | not modeled | computed from `documentDate`, `recordedDate`, `documentType` and the input date and basis |
| `otherLots` | `hasDeed` | count of other lots on the same deed, computed |
| `grantees`, `granteeNames` | `hasGrantee`, `granteeName` | labelled ACRIS; a title holder lead, not proof of title |
| `deeds` | `hasDeed`, `documentId` | the supporting deeds of Q14.1, distinct documents |
| `bin` | `bin` | graph name `Building.bin` |
| `registrationId`, `lastRegistered`, `registrationEnd` | `registrationId`, `lastRegistered`, `registrationEnd` | graph names `Registration.registrationId`, `HAS_REGISTRATION.lastRegistered`, `HAS_REGISTRATION.registrationEnd` |
| `status`, `registrationsInForce`, `relation` | not modeled | computed from the registration dates, the input date and name keys; in force is HPD's period, not responsibility |
| `owners`, `ownerNames` | `hasContact`, `contactType`, `corporationName`, `personName` | owner-type contacts of the registration; labelled HPD; a person name is for the answer only |

### Reasoner and example data

- ROBOT with HermiT, as for Q1 to Q13 (versions recorded by `make versions`).
- `abox/q14.ttl` (verified fixtures; entities only, no person names).
- No negative case: Q14 adds no axiom.

### Pitfall scan

Not run for Q14: the TBox is unchanged since the last scan, so there is nothing new to submit.

## Q15

### Scope

Adds one class (`Violation`), one object property (`hasViolation`) and four functional datatype properties (`violationId`, `violationClass`, `violationStatus`, `inspectionDate`), following `profiles/q15.yaml`. One concept was added to the vocabulary for the key (`violation-id`, `make vocab` to confirm). Reused: `Building`, `bin`, `TaxLot`, `bbl`, `residentialUnits`, `hasBuilding`.

### Not modeled

| Term | Reason |
| --- | --- |
| `open-violation-rate` | A computed answer value (open count over the lot's PLUTO units); never stored. Rate unavailable when units are 0 or absent. |
| counts by class and status, oldest open inspection date | Computed from the `Violation` nodes at answer time. |
| class and status values (A, B, C, I; Open, Close) | Plain enums in the schema, not concepts or classes; no subclass per class or status. |
| apartment, notice and certification dates, finer HPD status | Not loaded. |
| excluded violations (no usable or unregistered BIN) | 10,770 rows, counted by the loader and test, not stored. |

### Axioms

| Axiom | Reason |
| --- | --- |
| `Violation` disjointWith `Building` | A citation is not the structure it is cited against. Rejects one node carrying both. |
| `Violation` disjointWith `TaxLot` | A violation is not a lot, and lot-wide values never attach to it. |
| `hasViolation` domain `Building` | Violations hang on the BIN, never the lot (checked by `make profiles`). With the lot and building disjoint, a lot carrying one is inconsistent. |
| `violationId`, `violationClass`, `violationStatus`, `inspectionDate` domain `Violation` | Each appears only on violations in the graph. |
| `violationId`, `violationClass`, `violationStatus`, `inspectionDate` functional | One value per violation; the loader writes one per row and the id is unique. |

`hasViolation` is not functional (a building has many violations). It is not inverse-functional in the ontology either; the loader links each violation from one building, which Stage 6 checks.

### Rules for Stage 6 shapes

- Every `Violation` has all four properties and exactly one incoming `hasViolation` from a `Building`.
- `violationClass` is one of A, B, C, I; `violationStatus` is Open or Close; `violationId` is unique.
- No lot carries `hasViolation`; the rate and counts are never stored on a node.
- A building with no violation has no edge, and that is an empty answer, not a finding.
- 1,901,592 violations load; 10,770 on registered lots are excluded and counted.

### Answer fields

| Answer field | Ontology | Note |
| --- | --- | --- |
| `violationClass`, `status` | `violationClass`, `violationStatus` | graph names `Violation.violationClass`, `Violation.status` |
| `violations` | `hasViolation` | distinct violations per class and status, computed |
| `oldestInspection` | `inspectionDate` | earliest open date, computed |
| `bbl` | `bbl` | one row per lot the building sits on, never summed |
| `unitsRes` | `residentialUnits` | lot-wide PLUTO value |
| `openViolations` | `hasViolation`, `violationStatus` | count of Open violations, computed |
| `rate` | not modeled | open count over units; absent when units are 0 or absent |

### Reasoner and example data

- ROBOT with HermiT, as for Q1 to Q14 (versions recorded by `make versions`).
- `abox/q15.ttl` (anchor C counts and dates from the fixtures; entities only).
- Negative cases, each meant to be flagged inconsistent: `n37` (a lot with `hasViolation`), `n38` (a violation that is also a building), `n39` (two classes on one violation).

### Pitfall scan

`make oops` run 2026-11-18 (TBox only, user-reported): P11 (5 properties: `linkWeight`, `ownershipSignal`, `evidenceType`, `anchoredBy`, `partyRole`; relationship properties, accepted earlier) and P13 (20 properties lack inverses, now including `hasViolation`; minor, accepted). Nothing new from Q15 beyond P13. `make profiles` passes 883/883 (user-reported).

## Q16

### Scope

Adds no class, property or controlled value. Q16 is retrieval-extraction only: `profiles/q16.yaml` declares no graph element, and web and document findings are session evidence, not graph facts. No mapping row, axiom, example data or negative case is added. The answer reads existing elements only as the recorded facts a retrieved item is compared with (Q2 registrations and contacts, Q3 to Q13 deeds and financing, Q5 DOS entities).

### Not modeled

| Term | Reason |
| --- | --- |
| `retrieved-item`, `reported-claim`, `extraction-method`, `source-category`, `review-status`, `fact-relation`, `match-basis` | Answer-contract terms of session evidence (`profiles/q16.yaml` not_stored). Promoting findings into the graph needs a separately governed process. They stay SKOS concepts. |
| `public-record`, `published-reporting`, `web-content`, `project-derived`, the five review statuses, the four fact relations, `exact-match`, `lead-only` | Plain enums of the answer contract (`allowed_scheme` in the profile), not controlled values of a stored property. No stored property would use them, so no mapping row. |
| PROV-O terms | Used only when a question stores provenance (claims, documents, cached responses). Q16 stores none; the cache belongs to the downstream consumer. |

### Axioms

| Axiom | Reason |
| --- | --- |

None added. Disjointness candidates from `taxonomy-notes.md`: none proposed.

### Rules for Stage 6 shapes

- No Q16 element is stored, so no new shape. Stage 6 declares no shape and tests nothing on the graph; acceptance waits on a retrieval cache.
- A check that no `RetrievedItem`, claim, review status or match basis exists in the graph (computed-not-stored), in the manner of `queries/checks/q14-computed-not-stored.cypher`.
- A review status of `confirmed` or `refuted` is never set by the project; a similar name or low-confidence scan is `lead-only` and never used to join recorded facts. These belong to the cache fixtures and the downstream consumer, not to graph shapes.

### Answer fields

| Answer field | Ontology | Note |
| --- | --- | --- |
| `publisher`, `itemDate`, `locator`, `quotedClaim`, `extractedValue` | not modeled | answer-contract fields of a retrieved item; session evidence |
| `extractionMethod`, `confidence` | not modeled | how a value was read and the low-confidence flag; a low-confidence name is lead only |
| `sourceCategory` | not modeled | enum of four values; tracked apart from reliability type |
| `reviewStatus` | not modeled | starts unreviewed; never set to confirmed or refuted by the project |
| `factRelation`, `matchBasis` | not modeled | computed at answer time against the cited recorded item and rule N3; the recorded item is returned beside it |
| `searchLog`, `asOfDate` | not modeled | inputs and retrieval log kept with the cache |

### Reasoner and example data

- Not run for Q16: the ontology is unchanged, so there is nothing new to reason over (ROBOT 1.9.11 with HermiT stays as recorded for Q1 to Q15).
- No `abox/q16.ttl` and no negative case: Q16 adds no element and no axiom.

### Pitfall scan

Not run for Q16: the TBox is unchanged since the last scan, so there is nothing new to submit.

## Q17

### Scope

Adds no class, property or controlled value. Q17 reads existing elements: `TaxLot`, `bbl`, `hpdRegistered`, `residentialUnits`, `yearBuilt`, `plutoBuildingCount` (Q1); `hasBuilding`, `Building`, `hasRegistration`, `Registration`, `registrationId`, `lastRegistered`, `registrationEnd` (Q1, Q2); `hasDeed`, `Deed`, `documentId`, `documentType`, `recordedDate`, `documentAmount` (Q3, Q12). No mapping row, axiom or negative case is added, and `profiles/q17.yaml` declares no graph element.

### Not modeled

| Term | Reason |
| --- | --- |
| `missing-registration`, `lapsed-registration`, `registration-older-than-deed` | Conditions computed at answer time against the as-of date (2026-05-29) from `hpdRegistered`, `registrationEnd`, `lastRegistered` and `recordedDate`; `holds`, `does-not-hold` and `cannot-tell` are plain enums. They stay SKOS concepts. |
| `no-usable-registration` | A flag computed from `hpdRegistered` and the absence of `hasRegistration` on the lot's buildings. |
| `unit-threshold`, threshold outcome | The threshold (3) is an input; the outcome is computed from `residentialUnits`. No ruling on legal applicability. |
| as-of date, snapshot dates | Input and answer context from `data/sources.yaml`. |

### Axioms

| Axiom | Reason |
| --- | --- |

None added. Disjointness candidates from `taxonomy-notes.md`: none proposed.

### Rules for Stage 6 shapes

- No Q17 element is stored, so no new shape. The lot, registration and deed shapes cover the inputs.
- No condition, flag, outcome, as-of date or threshold is stored on a graph element (a computed-not-stored check, as for Q14 and Q16).
- `tests/q17_1` to `q17_4` re-derive each answer from the frozen baseline and compare it with the graph lookups.

### Answer fields

| Answer field | Ontology | Note |
| --- | --- | --- |
| `hpdRegistered` | `hpdRegistered` | graph name `Lot.hpdRegistered` |
| `missing`, `noUsableRegistration`, `lapsed`, `olderThanDeed`, `thresholdOutcome`, `notASale` | not modeled | computed at answer time from the inputs above and the Q3 deed fields |
| `registrations`, `registeredBuildings` | `hasBuilding`, `hasRegistration`, `registrationId` | counts of distinct (BIN, registration id) pairs and distinct buildings, computed |
| `plutoNumBuildings` | `plutoBuildingCount` | lot-wide, labelled PLUTO |
| `lastRegistered`, `registrationEnd`, `latestRegistered` | `lastRegistered`, `registrationEnd` | graph names `HAS_REGISTRATION.lastRegistered`, `HAS_REGISTRATION.registrationEnd`; the latest is a maximum, computed |
| `latestDeedRecorded`, `latestDeeds` | `recordedDate`, `hasDeed`, `documentId`, `documentType`, `documentAmount` | the deeds recorded on the latest date, all returned |
| `unitsRes`, `yearBuilt`, `threshold` | `residentialUnits`, `yearBuilt`; threshold an input | lot-wide units, never summed across buildings |

### Reasoner and example data

- ROBOT with HermiT, as for Q1 to Q16 (versions recorded by `make versions`).
- `abox/q17.ttl` (verified fixtures: anchors A, E, F and a placeholder-id lot; entities only, no person names).
- No negative case: Q17 adds no axiom.

### Pitfall scan

Not run for Q17: the TBox is unchanged since the last scan, so there is nothing new to submit.

## Q18

### Scope

Adds no class, property or controlled value. Q18 reads existing elements: `TaxLot`, `bbl`, `address` (Q1); `Deed`, `hasDeed`, `documentId`, `documentType`, `documentDate`, `recordedDate`, `documentAmount`, `Grantee`, `hasGrantee`, `granteeName` (Q3); `Grantor`, `hasGrantor`, `grantorName` (Q12); `Contact`, `corporationName` (Q2, for the registered-owner signal); `inPortfolio`, `OwnerPortfolio` (Q9, only to choose the lots). No mapping row, axiom or negative case is added, and `profiles/q18.yaml` declares no graph element.

### Not modeled

| Term | Reason |
| --- | --- |
| `deed-classification`, `zero-transfer` | Computed at answer time from `documentType` and `documentAmount` (correction, zero-transfer, priced are plain enums). They stay SKOS concepts. |
| `restructuring-signal` | Four boolean leads computed at answer time by rule N3 from the deeds, parties, lot address and registered owners. A lead, never a finding of restructuring or common control. They stay a SKOS concept. |
| uncertainty and caveats | Answer contract (`tests/q18_3/contract.yaml`). |

### Axioms

| Axiom | Reason |
| --- | --- |

None added. Disjointness candidates from `taxonomy-notes.md`: none proposed.

### Rules for Stage 6 shapes

- No Q18 element is stored, so no new shape. The deed, party, lot and contact shapes cover the inputs.
- No classification, signal, signal count or uncertainty is stored on a graph element (a computed-not-stored check, as for Q14, Q16 and Q17).
- No Q18 lookup reads group membership (checked by `tests/q18_3`).

### Answer fields

| Answer field | Ontology | Note |
| --- | --- | --- |
| `documentId`, `docType`, `docDate`, `recordedDate`, `amount` | `documentId`, `documentType`, `documentDate`, `recordedDate`, `documentAmount` | graph names `Deed.*` |
| `classification` | not modeled | computed from `documentType` and `documentAmount` |
| `lots` | `hasDeed` | the asked lots on the deed, computed |
| `grantors`, `grantees` | `hasGrantor`, `grantorName`, `hasGrantee`, `granteeName` | all listed; a person never repeated in notes |
| `granteeNamedForLot`, `sameName`, `hasFollowOn`, `followOn`, `granteeRegisteredOwner`, `signals` | not modeled | computed at answer time (nameKey comparisons, rule N3) |
| `caveats`, `uncertain` | not modeled | answer contract |

### Reasoner and example data

- ROBOT with HermiT, as for Q1 to Q17 (versions recorded by `make versions`).
- `abox/q18.ttl` (verified fixtures: anchors A and B; entities only, the person grantor unnamed).
- No negative case: Q18 adds no axiom.

### Pitfall scan

Not run for Q18: the TBox is unchanged since the last scan, so there is nothing new to submit.

## Q19

### Scope

Adds no class, property or controlled value. Q19 reads existing elements: `TaxLot`, `bbl` (Q1); `OperationalNetwork`, `inNetwork`, `groupId`, `networkSplit`, `networkAbsence`, `networkAbsenceDetail`, `Landlord`, `covers`, `connectedByIdentity`, `connectedByName`, `connectedByAddress` (Q8); `OwnerPortfolio`, `inPortfolio`, `portfolioId`, `portfolioComposition`, `portfolioAbsence`, `portfolioAbsenceDetail`, `connectedByDeed` (Q9). No mapping row, axiom or negative case is added, and `profiles/q19.yaml` declares no graph element.

### Not modeled

| Term | Reason |
| --- | --- |
| `pair-layer-state` | Same, different or ungrouped is computed at answer time from group membership and absence properties. It stays a SKOS concept and a plain enum. |
| `representative-path` | A fewest-link chain computed at answer time from `covers` and the `connectedBy*` links; an answer object, not a stored thing. |
| `pre-subdivision-connectivity` | Computed from the links that carry a network edge id, including links across a cut. No component id is stored. |
| `stage-precision` | A method property of the release (`method_metrics`), stated per stage, never stored on a link, landlord or group. |
| uncertainty and caveats | Answer contract; the run, the non-link caveat and the precision caveat are repeated in every answer. |

### Axioms

| Axiom | Reason |
| --- | --- |

None added. Disjointness candidates from `taxonomy-notes.md`: none proposed.

### Rules for Stage 6 shapes

- No Q19 element is stored, so no new shape. The Q8 and Q9 shapes cover every input.
- No pair state, path, connectivity flag, step count or precision is stored on a graph element (a computed-not-stored check, as for Q14, Q16, Q17 and Q18): no link, landlord, lot or group has a property whose name holds precision, probability or confidence; no `componentId` on a network.
- Every `CONNECTED_BY_IDENTITY` and `CONNECTED_BY_DEED` link has a stage and evidence id (Q8, Q9 shapes), so each edge of a path can be explained.

### Answer fields

| Answer field | Ontology | Note |
| --- | --- | --- |
| `bbl` | `bbl` | graph name `Lot.bbl` |
| `networkGroupId`, `networkSplit`, `networkAbsence`, `networkAbsenceDetail` | `groupId`, `networkSplit`, `networkAbsence`, `networkAbsenceDetail` | via `inNetwork` |
| `portfolioGroupId`, `portfolioComposition`, `portfolioAbsence`, `portfolioAbsenceDetail` | `portfolioId`, `portfolioComposition`, `portfolioAbsence`, `portfolioAbsenceDetail` | via `inPortfolio` |
| `state`, `sameNetwork` | not modeled | computed from the group ids |
| `steps`, `nodeIds`, `linkType`, `stage`, `evidenceType`, `evidenceId`, `weight` | `connectedByIdentity`, `connectedByDeed`, `connectedByName`, `connectedByAddress`, `evidenceType`, `covers` | link properties have no domain (OOPS! P11 accepted); the path itself is computed |
| `connected`, `crossesCut` | not modeled | computed from the links; the release's `component_id` is only a check |
| `evaluated`, `precision`, `provisional` | not modeled | method property of the release, not a graph element |

### Reasoner and example data

- ROBOT with HermiT, as for Q1 to Q18 (versions recorded by `make versions`).
- `abox/q19.ttl` (verified fixtures: same group, different groups, no path, a Louvain-split pair; entities only).
- No negative case: Q19 adds no axiom.

### Pitfall scan

Not run for Q19: the TBox is unchanged since the last scan, so there is nothing new to submit.

## Q20

### Scope

Adds no class, property or controlled value. Q20 is an integration scenario: the dossier is assembled at answer time from the elements of Q1 to Q13, Q15 and Q19 (`TaxLot`, `Building`, `Registration`, `Contact`, `Deed`, `Document`, `DocumentParty`, `DosEntity`, `OperationalNetwork`, `OwnerPortfolio` and their properties). No concept of Q20 (`dossier`, `lead`, `stop-reason` and the five `stop-reasons` values) is a class, property or controlled value. The mapping table is unchanged.

### Not modeled

| Term | Reason |
| --- | --- |
| `dossier` | An assembled answer, not a stored thing. Its seven sections are answer fields. No class, so no stored dossier can be asserted about a lot. |
| `lead` | Computed at answer time by the lead rule from recorded and retrieved names and addresses. A lead is a role a name or address plays, not a kind of either, and never a finding. |
| `stop-reason` and its five values | One value chosen per investigation and returned in the answer. They stay SKOS concepts and a plain enum in `profiles/q20.yaml`; `evidence-statuses` and the Q16 schemes are reused the same way. |
| claim label, source category, review status, retrieval log, run | Answer contract (Q16, Q20.4); session evidence is never stored in the graph. PROV-O is not used because nothing is stored. |

### Axioms

| Axiom | Reason |
| --- | --- |

None added. Disjointness candidates from `taxonomy-notes.md`: none proposed.

### Rules for Stage 6 shapes

- No Q20 element is stored, so no new shape. Each section's shapes (Q1 to Q13, Q15, Q19) cover its inputs.
- Computed-not-stored check (as for Q14, Q16 to Q19): no lot, group, contact, deed or document carries a dossier, lead, finding, claim, stop reason or owner conclusion (`tests/q20_2/check_layers.py` already reads this on the loaded graph); add the check as a Cypher check with a few negative cases in stage 6.
- No label of the Q20 vocabulary (`Dossier`, `Lead`, `StopReason`) exists in the graph.

### Answer fields

| Answer field | Ontology | Note |
| --- | --- | --- |
| `section`, `componentAnswer` | not modeled | the dossier is assembled at answer time; each fact keeps its component element |
| `networkId`, `portfolioId` | `groupId`, `portfolioId` | via `inNetwork` and `inPortfolio`; absent when the lot is in no group (anchor A) |
| `leadStatus`, `reason`, `stopReason` | not modeled | computed by the lead rule and chosen once per investigation |
| `label`, `sourceCategory`, `reviewStatus`, `sourceRecordOrUrl`, `retrievedAt`, `run` | not modeled | answer contract; session evidence is not stored (pending a retrieval cache) |

### Reasoner and example data

- ROBOT with HermiT, as for Q1 to Q19 (versions recorded by `make versions`).
- `abox/q20.ttl` (verified fixtures: the anchor A trail: lot, building, registration and owner contact, two deeds, DOS record with its own process name, the joint mortgage, no group); entities only.
- No negative case: Q20 adds no axiom.

### Pitfall scan

Not run for Q20: the TBox is unchanged since the last scan, so there is nothing new to submit.

## Q21

### Scope

Adds no class, property or controlled value. Q21 reads existing elements: `TaxLot` (`residentialUnits`), `Building` (`hasBuilding`), `Violation` (`hasViolation`, `violationClass`, `violationStatus`), `OperationalNetwork` and `OwnerPortfolio` (`inNetwork`, `inPortfolio`). Per-lot open counts, rates, ranks, the concentration share and the layer comparison are computed at answer time.

### Not modeled

| Term | Reason |
| --- | --- |
| `lot-violation-ranking` | An ordered answer list over member lots, not a stored thing. No class, so no rank or count can be asserted on a lot. |
| `violation-concentration` | A figure computed over that list; depends on the number of top lots chosen. |
| `open-violation-rate` | Already declared as derived (Q15); not stored per lot, since a building on several lots counts toward each. |
| "hazardous" | Not a class; classes A, B, C and I are reported apart. |

### Axioms

| Axiom | Reason |
| --- | --- |

None added. Disjointness candidates from `taxonomy-notes.md`: none proposed.

### Rules for Stage 6 shapes

- No Q21 element is stored, so no new shape. Q8, Q9 and Q15 shapes cover the inputs.
- Computed-not-stored check (as for Q14, Q16 to Q20): no lot, building, group or violation carries an open count, rate, rank, share or concentration (`queries/checks/q21-computed-not-stored.cypher`), with a few negative cases.
- No label `Ranking` or `Concentration` exists in the graph.

### Answer fields

| Answer field | Ontology | Note |
| --- | --- | --- |
| `bbl`, `unitsRes` | `bbl`, `residentialUnits` | lot-wide, never summed across buildings; absent or 0 gives rate unavailable |
| `open`, `classA`, `classB`, `classC`, `classI` | `Violation` via `hasBuilding` and `hasViolation`, with `violationStatus` and `violationClass` | counted at answer time as distinct violations |
| `rate`, `topShare`, `sumOpen`, `topOpen`, `distinctOpen`, `memberLots`, `lotsWithOpen` | not modeled | derived at answer time |
| `networkGroupId`, `portfolioGroupId`, absence details | `groupId`, `portfolioId`, `networkAbsenceDetail`, `portfolioAbsenceDetail` | via `inNetwork` and `inPortfolio`; absent when the lot is in no group |
| `netLots`, `portLots`, `onlyNetwork`, `onlyPortfolio`, `both` | not modeled | set differences of two membership lists, computed at answer time |

### Reasoner and example data

- ROBOT with HermiT, as for Q1 to Q20 (versions recorded by `make versions`).
- `abox/q21.ttl` (anchor D lot with three buildings and two illustrative open violations, in network `ON-18742` and portfolio `OP-53559`; a lot with no unit count; anchor A with no portfolio); entities only.
- No negative case: Q21 adds no axiom.

### Pitfall scan

Not run for Q21: the TBox is unchanged since the last scan, so there is nothing new to submit.

## Q22

### Scope

Adds no class, property or controlled value. Q22 reads existing elements: `Contact` (`corporationName`), `Grantee` (`granteeName`), `DosEntity` (`dosId`, `dosEntityName`), and the lot, registration and document elements for joining records. The comparison outcome, rule and joining records are computed at answer time.

### Not modeled

| Term | Reason |
| --- | --- |
| `abbreviation-match`, `differs-by-numeral-or-word` | Outcome values computed at answer time and never stored; like the Q3 outcomes, no controlled value is minted. |
| `name-agreement` outcome and `comparison-rule` S1, L1, AB1 | Computed by `compare.entity_name_comparison`; a stored outcome would read as a link between two parties. |
| joining record, same-entity verdict | Intersections of existing records; a judgment, not a graph fact. |

### Axioms

| Axiom | Reason |
| --- | --- |

None added. Disjointness candidates from `taxonomy-notes.md`: none proposed.

### Rules for Stage 6 shapes

- No Q22 element is stored, so no new shape. Computed-not-stored check (as for Q14, Q16 to Q21): no node or relationship carries an entity name outcome, rule, or same-entity flag (`queries/checks/q22-computed-not-stored.cypher`), with a few negative cases.
- No relationship such as `SAME_AS` or `SAME_ENTITY` exists in the graph: a name match is a lead, not a link.

### Answer fields

| Answer field | Ontology | Note |
| --- | --- | --- |
| `outcome`, `rule` | not modeled | derived at answer time from the two names |
| `nameA`, `nameB` | `corporationName`, `granteeName`, `dosEntityName` | the name as recorded, with its source; a person's name is shown with role and source |
| `kind`, `address` | `hasDeed`, `hasGrantee`, `hasGrantor`, `hasRegistration`, `hasContact`, `hasParty`, `mailingAddress`, `processAddress` | the record kinds the lookup reads |
| `ref` | `bbl`, `documentId`, `dosId` | the lot, document or DOS id that appears in both names' results |

### Reasoner and example data

- ROBOT with HermiT, as for Q1 to Q21 (versions recorded by `make versions`).
- `abox/q22.ttl` (anchor G spellings and anchor B names); entities only.
- No negative case: Q22 adds no axiom.

### Pitfall scan

Not run for Q22: the TBox is unchanged since the last scan, so there is nothing new to submit.

## Q23

### Scope

Adds no class, property or controlled value. Q23 reads existing elements: `Contact` (`contactType`, `corporationName`, `mailingAddress`, `addressLineTwo`), `Registration`, `Building`, `TaxLot`, `hasContact`, `hasRegistration`, `hasBuilding`, `inNetwork`, `inPortfolio`, `NetworkMaskedAddress` (`maskedAddressDegree`) and `PortfolioMaskedAddress` (`portfolioMaskedAddressDegree`). The footprint counts, the same/other/none layer states and the address check are computed at answer time. The name key is a lookup key (Q2) and is not an answer field.

### Not modeled

| Term | Reason |
| --- | --- |
| `agent-footprint` | An answer object over existing records; storing counts would go stale and read as a finding about management or ownership. Stays a SKOS concept. |
| layer state (same, other, none) | A comparison with a chosen reference building, computed at answer time. |
| commercial service or operator verdict | Footprint size suggests, never proves; no element states it. |
| `agent` | A `contactType` value already recorded as the plain string `Agent` (Q4); no controlled-value individual is minted. |

### Axioms

| Axiom | Reason |
| --- | --- |

None added. Disjointness candidates from `taxonomy-notes.md`: none proposed.

### Rules for Stage 6 shapes

- No Q23 element is stored, so no new shape. Computed-not-stored check (as for Q14, Q16 to Q22): no node or relationship carries a footprint count, layer state, commercial-service flag or verdict (`queries/checks/q23-computed-not-stored.cypher`), with a few negative cases.
- No relationship such as `SAME_OWNER` or `MANAGED_BY` joins two lots or contacts: shared management is a record link, not a grouping.

### Answer fields

| Answer field | Ontology | Note |
| --- | --- | --- |
| `contactType` | `contactType` | `Agent` is the managing agent; other types carrying the same name are reported apart |
| `spelling` | `corporationName` | as recorded, case kept; spellings with the same N3 key combine at answer time |
| `registrations`, `buildings`, `lots` | derived | distinct registrations, buildings and lots reached through `hasContact`, `hasRegistration` and `hasBuilding` |
| `referenceLot` | `bbl` | one row per lot of the reference building |
| `network`, `portfolio` | `groupId`, `portfolioId` | run-local group ids of the reference lot, through `inNetwork` and `inPortfolio` |
| `networkSame`, `networkOther`, `networkNone`, `portfolioSame`, `portfolioOther`, `portfolioNone` | derived | counts of footprint lots against the reference lot's groups; none means the release did not group the lot |
| `address` | `mailingAddress`, `addressLineTwo` | street line plus second line, uppercased |
| `contacts` | derived | distinct agent contacts at the address text |
| `networkDegree`, `portfolioDegree` | `maskedAddressDegree`, `portfolioMaskedAddressDegree` | absent when the method did not mask the text; absence is not safety |

### Reasoner and example data

- ROBOT with HermiT, as for Q1 to Q22 (versions recorded by `make versions`).
- `abox/q23.ttl` (an agent with two spellings and a legal-suffix variant; a lot in a network but no portfolio; a masked address); entities only.
- No negative case: Q23 adds no axiom.

### Pitfall scan

Not run for Q23: the TBox is unchanged since the last scan, so there is nothing new to submit.

## Q24

### Scope

Adds no class, property or controlled value. Q24 reads existing elements: `Contact` (`contactType`, `corporationName`, `personName`), `Registration`, `Building`, `TaxLot`, `Deed`, `Grantee` (`granteeName`), `Grantor` (`grantorName`), `DosEntity` (`dosId`, `dosEntityName`), `hasContact`, `hasRegistration`, `hasBuilding`, `hasDeed`, `hasGrantee` and `hasGrantor`. The name key is a lookup key (Q2, Q3, Q5, Q12) and is not an answer field. Matches, leads, bases, counts and the outcome are computed at answer time.

### Not modeled

| Term | Reason |
| --- | --- |
| `name-search` | An answer object over existing records; a stored match would read as a link between records. Stays a SKOS concept. |
| `legal-suffix-only` | A near-name lead kind computed at answer time, like the Q22 outcomes; no controlled value is minted. |
| match basis (exact, normalized) and outcome (matches, leads-only, no-match-in-these-sources) | Plain enums of the answer contract, derived from the recorded name and the name as given. |
| person name key | A person is found by uppercase `personName` at answer time; no new property is needed. |
| filer | Not a role in any loaded source. |

### Axioms

| Axiom | Reason |
| --- | --- |

None added. Disjointness candidates from `taxonomy-notes.md`: none proposed.

### Rules for Stage 6 shapes

- No Q24 element is stored, so no new shape. Computed-not-stored check (as for Q14, Q16 to Q23): no node or relationship carries a match, basis, near-name kind, lead flag or outcome (`queries/checks/q24-computed-not-stored.cypher`), with a few negative cases.
- No relationship such as `SAME_AS`, `SAME_PERSON` or `NAME_MATCH` exists: a name match is a lead, not a link (already guarded by the Q22 check for the first).

### Answer fields

| Answer field | Ontology | Note |
| --- | --- | --- |
| `source`, `basis`, `kind`, `outcome`, `snapshot` | not modeled | derived at answer time; snapshot dates are recorded once in `data/sources.yaml` |
| `role` | `contactType`, `hasGrantee`, `hasGrantor`, `DosEntity` | the recorded contact type, or grantee, grantor or filed entity by the property or class |
| `name` | `corporationName`, `granteeName`, `grantorName`, `dosEntityName` | as recorded; the basis compares it with the name as given |
| `ref` | `registrationId`, `documentId`, `dosId` | the record that carries the name |
| `bin`, `bbl` | `bin`, `bbl` | the building and lot through `hasRegistration`, `hasBuilding` and `hasDeed` |
| `order` | derived | `as given` (HPD order) or `reversed` (last name first); never stored |
| `records`, `buildings`, `lots`, `sample` | derived | distinct registrations or deeds, buildings and lots, and the first ten ids |
| `nameKey` | not modeled | the lookup key (rule N3) of a near-name candidate; not an answer field of any stored element |
| person name | `personName` | held in the graph, shown only with its role and source, never repeated elsewhere |

### Reasoner and example data

- ROBOT with HermiT, as for Q1 to Q23 (versions recorded by `make versions`).
- `abox/q24.ttl` (anchor A entity name in three sources; a person contact and a deed party in reversed order, unnamed); entities only.
- No negative case: Q24 adds no axiom.

### Pitfall scan

Not run for Q24: the TBox is unchanged since the last scan, so there is nothing new to submit.

## Q25

### Scope

Adds no class, property or controlled value. Q25 is retrieval-extraction only: `profiles/q25.yaml` declares no graph element, and registry findings are session evidence. No mapping row, axiom, example data or negative case is added. Q25.1 reads existing elements: `DosEntity` (`dosEntityName`, `jurisdiction`, `dosId`).

### Not modeled

| Term | Reason |
| --- | --- |
| `registry-search`, `registry-outcome` | Answer-contract terms of session evidence (`profiles/q25.yaml` not_stored). Promoting findings into the graph needs a separately governed process. They stay SKOS concepts. |
| `registry-record-found`, `registry-status-only`, `registry-no-record`, `registry-unreachable` | Plain enums of the answer contract (`allowed_scheme` in the profile). No stored property uses them, so no mapping row. |
| Reused `match-basis`, `review-status`, `stop-reason`, `source-category` values | Answer-contract enums (Q16, Q20); not stored. |
| PROV-O terms | Used only when a question stores provenance. Q25 stores none; the cache belongs to the downstream consumer. |

### Axioms

| Axiom | Reason |
| --- | --- |

None added. Disjointness candidates from `taxonomy-notes.md`: none proposed.

### Rules for Stage 6 shapes

- No Q25 element is stored, so no new shape. Computed-not-stored check (as for Q14, Q16 to Q24): no node or relationship carries a registry search, outcome, filing id, registry status or registered agent from another jurisdiction.
- An unreachable registry is never recorded as no record, and a name match in another state is `lead-only`; these belong to the cache fixtures and the downstream consumer, not to graph shapes.

### Answer fields

| Answer field | Ontology | Note |
| --- | --- | --- |
| `entityName`, `jurisdiction`, `recordedBy` | `dosEntityName`, `jurisdiction`, `dosId` | the recorded DOS entity and the place of formation it states |
| `registry`, `query`, `retrievedOn`, `outcome`, `filingId`, `status`, `filingDate`, `registeredAgent`, `sourceCategory` | not modeled | answer-contract fields of a registry search; session evidence |
| `stopReason`, `leadStep` | not modeled | answer-contract fields; a payment-gated step is an unresolved lead |
| `matchBasis`, `reviewStatus` | not modeled | computed at answer time (rule N3 plus any other connecting record); review starts item-unreviewed |

### Reasoner and example data

- Not run for Q25: the ontology is unchanged, so there is nothing new to reason over.
- No `abox/q25.ttl` and no negative case: Q25 adds no element and no axiom.

### Pitfall scan

Not run for Q25: the TBox is unchanged since the last scan, so there is nothing new to submit.

## Q26

### Scope

Adds no class, property or controlled value. Q26 reads existing elements: `TaxLot` (`hpdRegistered`, `residentialUnits`, `yearBuilt`, `networkAbsence`, `portfolioAbsence` and their detail codes, `inNetwork`, `inPortfolio`), `Contact` (`contactType`, `corporationName`, `nameKey`), `DosEntity` (`nameKey`) and `Violation` (`hasViolation`). The absence statement, its reason for the non-layer sources and the violation outcome are computed at answer time.

### Not modeled

| Term | Reason |
| --- | --- |
| `source-absence` | An answer object over five sources, not a stored thing. No class, so no absence or reason can be asserted on a lot beyond BOR's own layer reasons. |
| Reason for registration, DOS and violations | Derived by the rules in `specs/questions/q26.md`; only the two layer reasons are stored (Q8, Q9). |
| `not-loaded`, `none-in-snapshot` | Outcome values of an answer field computed from `hpdRegistered` and the violation count. |
| "exempt", "unregistered", recall | The data does not say which; recall is a fixed statement in the answer. |

### Axioms

| Axiom | Reason |
| --- | --- |

None added. Disjointness candidates from `taxonomy-notes.md`: none proposed.

### Rules for Stage 6 shapes

- No Q26 element is stored, so no new shape. Q1, Q2, Q5, Q8, Q9 and Q15 shapes cover the inputs.
- Computed-not-stored check (as for Q14, Q16 to Q25): no node or relationship carries an absence statement, a derived reason for a non-layer source, or a violation outcome (`queries/checks/q26-computed-not-stored.cypher`), with a few negative cases.

### Answer fields

| Answer field | Ontology | Note |
| --- | --- | --- |
| `bbl`, `unitsRes`, `yearBuilt` | `bbl`, `residentialUnits`, `yearBuilt` | lot-wide; absent when PLUTO has none |
| `hpdRegistered`, `loadedScope` | `hpdRegistered` | false is the registration absence; for violations it means not loaded, never none |
| `reason` (Q26.1, Q26.2, Q26.4), `outcome` | not modeled | derived at answer time |
| `contactType`, `corporationName`, `nameKey` | `contactType`, `corporationName`, `nameKey` | owner contacts reached through `hasContact` |
| `dosRecords` | `DosEntity` with the same `nameKey` | counted at answer time; 0 is no record under this spelling |
| `networkGroupId`, `portfolioGroupId` | `groupId`, `portfolioId` | via `inNetwork` and `inPortfolio`; absent when the lot is in no group |
| `networkAbsence`, `networkAbsenceDetail`, `portfolioAbsence`, `portfolioAbsenceDetail` | same names | BOR's top-level reason and code |
| `violations` | `Violation` via `hasBuilding` and `hasViolation` | distinct violations, counted at answer time |

### Reasoner and example data

- ROBOT with HermiT, as for Q1 to Q25 (versions recorded by `make versions`).
- `abox/q26.ttl` (anchor F unregistered, 20 River Terrace in a network and out of the portfolio by policy, anchor A with no linkage and one violation); entities only.
- No negative case: Q26 adds no axiom.

### Pitfall scan

Not run for Q26: the TBox is unchanged since the last scan, so there is nothing new to submit.

## Q27

### Scope

Adds one class (`Problem`), one object property (`hasProblem`) and seven functional datatype properties (`problemId`, `complaintId`, `problemType`, `majorCategory`, `problemStatus`, `receivedDate`, `duplicateFlag`), following `profiles/q27.yaml`. Reused: `Building`, `bin`, `TaxLot`, `bbl`, `residentialUnits`, `hasBuilding`, `Violation`.

### Not modeled

| Term | Reason |
| --- | --- |
| `complaint-rate` | A computed answer value (the period's problem count over the lot's PLUTO units); never stored. Rate unavailable when units are 0 or absent. |
| counts by type, category and status, open count, distinct complaints, first and last received | Computed from the `Problem` nodes at answer time. |
| type and status values | Plain enums in the schema, not concepts or classes; no subclass per type or status. |
| apartment, unit and space type, anonymity, coordinates, minor category, problem code, complaint status | Not loaded. |
| problems before 2021-01-01; excluded problems (no usable or unregistered BIN) | Outside the loaded window; 27,561 excluded rows counted by the loader and test, not stored. |

### Axioms

| Axiom | Reason |
| --- | --- |
| `Problem` disjointWith `Building` | A report is not the structure it is reported against. |
| `Problem` disjointWith `TaxLot` | A problem is not a lot, and lot-wide values never attach to it. |
| `Problem` disjointWith `Violation` | What a tenant reported is not what an inspector cited; the two are counted apart and never merged. |
| `hasProblem` domain `Building` | Problems hang on the BIN, never the lot (checked by `make profiles`). With the lot and building disjoint, a lot carrying one is inconsistent. |
| `problemId`, `complaintId`, `problemType`, `majorCategory`, `problemStatus`, `receivedDate`, `duplicateFlag` domain `Problem` | Each appears only on problems in the graph. |
| `problemId`, `complaintId`, `problemType`, `majorCategory`, `problemStatus`, `receivedDate`, `duplicateFlag` functional | One value per problem; the loader writes one per row and the id is unique. |

`hasProblem` is not functional (a building has many problems) and not inverse-functional in the ontology; the loader links each problem from one building, which Stage 6 checks. No inverse is declared (OOPS! P13, accepted as for the other relationship properties).

### Rules for Stage 6 shapes

- Every `Problem` has all seven properties and exactly one incoming `hasProblem` from a `Building`.
- `problemStatus` is OPEN or CLOSE; `problemType` is one of the five HPD types; `receivedDate` is on or after 2021-01-01; `problemId` is unique.
- No lot carries `hasProblem`; the rate and counts are never stored on a node.
- A building with no problem has no edge, and that is an empty answer, not a finding.
- 4,033,827 problems load; 27,561 on registered lots since 2021-01-01 are excluded and counted.

### Answer fields

| Answer field | Ontology | Note |
| --- | --- | --- |
| `problemType`, `majorCategory`, `status` | `problemType`, `majorCategory`, `problemStatus` | graph names `Problem.problemType`, `Problem.majorCategory`, `Problem.status` |
| `problems` | `hasProblem` | problem records per type, category and status in the period, computed |
| `duplicates` | `duplicateFlag` | count of flagged problems, computed |
| `complaints` | `complaintId` | distinct ids, computed |
| `firstReceived`, `lastReceived` | `receivedDate` | earliest and latest date, computed |
| `bbl` | `bbl` | one row per lot the building sits on, never summed |
| `unitsRes` | `residentialUnits` | lot-wide PLUTO value |
| `rate` | not modeled | problems over units; absent when units are 0 or absent |

### Reasoner and example data

- ROBOT with HermiT, as for Q1 to Q26 (versions recorded by `make versions`).
- `abox/q27.ttl` (anchor C with two problems, one flagged duplicate, and a building with none; entities only).
- Negative cases, each meant to be flagged inconsistent: `n40` (a lot with `hasProblem`), `n41` (a problem that is also a violation), `n42` (two statuses on one problem).

### Pitfall scan

Pending: the user runs `make oops` (TBox only). Expect only P11 and P13 (`hasProblem` adds one more property without an inverse).

## Q28

### Scope

Adds one class (`Litigation`), one object property (`hasLitigation`) and ten datatype properties (`litigationId`, `caseType`, `caseOpenDate`, `caseStatus`, `openJudgement`, `harassmentFinding`, `findingDate`, `penalty`, `respondent`, `respondentKeys`), following `profiles/q28.yaml`. `respondentKeys` is the only non-functional one (several keys per case). Reused: `Building`, `bin`, `TaxLot`, `bbl`, `hasBuilding`, `Violation`, `Problem`.

### Not modeled

| Term | Reason |
| --- | --- |
| `respondent-owner-match` | A computed answer value (respondent keys against owner names under rule N3); never stored. |
| cases per building, counts by type or status | Computed from the `Litigation` nodes at answer time. |
| case type, harassment finding and open judgement values | Plain enums in the schema, not concepts or classes; no subclass per type or finding. |
| case address, coordinates, districts, judgement amount, respondent role | Not loaded, or not in the source. |
| excluded cases (no usable or unregistered BIN) | 1,483 rows, counted by the loader and test, not stored. |

### Axioms

| Axiom | Reason |
| --- | --- |
| `Litigation` disjointWith `Building` | An action brought is not the structure it is brought against. |
| `Litigation` disjointWith `TaxLot` | A case is not a lot, and lot-wide values never attach to it. |
| `Litigation` disjointWith `Violation` | An action HPD brought is not what an inspector cited; counted apart and never merged. |
| `Litigation` disjointWith `Problem` | An action HPD brought is not what a tenant reported. |
| `hasLitigation` domain `Building` | Cases hang on the BIN, never the lot (checked by `make profiles`). With the lot and building disjoint, a lot carrying one is inconsistent. |
| `litigationId`, `caseType`, `caseOpenDate`, `caseStatus`, `openJudgement`, `harassmentFinding`, `findingDate`, `penalty`, `respondent`, `respondentKeys` domain `Litigation` | Each appears only on cases in the graph. |
| `litigationId`, `caseType`, `caseOpenDate`, `caseStatus`, `openJudgement`, `harassmentFinding`, `findingDate`, `penalty`, `respondent` functional | One value per case; the loader writes one per row and the id is unique. `respondentKeys` is deliberately not functional. |

`hasLitigation` is not functional (a building has many cases) and not inverse-functional in the ontology; the loader links each case from one building, which Stage 6 checks. No inverse is declared (OOPS! P13, accepted). The element `respondentKeys` carries the label "respondent", as its concept does (the mapping check requires it); OOPS! P32 may flag the shared label, accepted because the comment says what differs.

### Rules for Stage 6 shapes

- Every `Litigation` has `litigationId`, `caseType`, `caseStatus` and `openJudgement`, and exactly one incoming `hasLitigation` from a `Building`.
- `openJudgement` is YES or NO; `harassmentFinding` is After Inquest, After Trial or No Harassment when present; `findingDate` appears only with a `harassmentFinding`; `penalty` is a non-negative integer.
- `respondentKeys` appears only with a `respondent`, and is never an empty list.
- No lot carries `hasLitigation`; the owner match and counts are never stored on a node.
- A building with no case has no edge, and that is an empty answer, not a finding.
- 210,169 cases load; 1,483 on registered lots are excluded and counted. Dates before 1990 and after the snapshot are kept and reported.

### Answer fields

| Answer field | Ontology | Note |
| --- | --- | --- |
| `litigationId` | `litigationId` | counting unit: cases |
| `caseType`, `caseOpenDate`, `caseStatus`, `openJudgement` | `caseType`, `caseOpenDate`, `caseStatus`, `openJudgement` | as recorded |
| `harassmentFinding`, `findingDate`, `penalty` | `harassmentFinding`, `findingDate`, `penalty` | absent when none is recorded |
| `respondent`, `respondentKeys` | `respondent`, `respondentKeys` | the recorded string and its N3 keys |
| `cases` | `hasLitigation` | the building's cases with their respondent keys |
| `owners` | `hasRegistration`, `hasContact`, `contactType`, `corporationName`, `personName` | existing Q2 and Q4 elements |
| `respondentOwnerMatch` | not modeled | computed at answer time with rule N3; a lead |

### Reasoner and example data

- ROBOT with HermiT, as for Q1 to Q27 (versions recorded by `make versions`).
- `abox/q28.ttl` (anchor C's closed case, a finding After Trial with a date and penalty, a case with no respondent and no open date, and a building with none; entities only).
- Negative cases, each meant to be flagged inconsistent: `n43` (a lot with `hasLitigation`), `n44` (a case that is also a violation), `n45` (two statuses on one case).

### Pitfall scan

Run 2026-11-20 (TBox only): P11 (5 relationship properties without a domain or range: `anchoredBy`, `evidenceType`, `linkWeight`, `ownershipSignal`, `partyRole`; accepted earlier, none from Q28) and P13 (22 properties without an inverse; `hasLitigation` adds one, accepted). No P32: the shared "respondent" label was not flagged. Nothing new from Q28.

## Q15 pest extension (Q15.3)

### Scope

Adds one functional datatype property, `orderNumber` (label "order number"; domain `Violation`, range string), following `profiles/q15.yaml` (graph name `Violation.orderNumber`). No new class or object property. Reused: `Violation`, `hasViolation`, `violationStatus`, `inspectionDate`. The vocabulary gained `order-number` and `pest-violation` in stage 1 (`make vocab` clean).

### Not modeled

| Term | Reason |
| --- | --- |
| `pest-violation`, `pestKind` | A computed answer value: the violations whose order number is on the list in `data/hpd_pest_orders.yaml`, and the kind of each code. Never stored, so a wrong mapping is fixed in one file. No subclass of `Violation` (stage 3: flat). |
| mice, roaches, rodents, vermin-unspecified | Values of the code list, not classes or concepts. Orders 566 and 866 name no species and are never mice. |
| order descriptions | The text names apartments; not loaded. |
| the eight pest order codes | Values of `orderNumber`, kept in the list file, not individuals or controlled values. |

### Axioms

| Axiom | Reason |
| --- | --- |
| `orderNumber` domain `Violation` | It appears only on violations in the graph. |
| `orderNumber` functional | One order number per violation; the loader writes one per row. |

No new disjointness: `Violation` stays disjoint from `Building`, `TaxLot`, `Problem` and `Litigation`. The range is `xsd:string`: HPD's code is text and is never converted to a number.

### Rules for Stage 6 shapes

- Every `Violation` has exactly one `orderNumber`, numeric text (`[0-9]+`), no leading zero.
- No `pestKind`, description or apartment property is stored.
- The pest counts and the kind are computed at answer time from the order number and `data/hpd_pest_orders.yaml`.

### Answer fields

| Answer field | Ontology | Note |
| --- | --- | --- |
| `orderNumber` | `orderNumber` | graph name `Violation.orderNumber` |
| `pestKind` | not modeled | derived from the order code list; never stored |
| `status` | `violationStatus` | open at the snapshot date |
| `violations` | `hasViolation` | distinct pest violations per order code and status, computed |
| `oldestInspection` | `inspectionDate` | earliest open date per order code, computed |

### Reasoner and example data

- ROBOT with HermiT (1.9.11), as for Q1 to Q28.
- `abox/q15.ttl` gains anchor C's open roach violation (order 568, class C) and the order number of its class B violation (508).
- Negative case `n46`: two order numbers on one violation, flagged inconsistent.
- OOPS! not rerun: the TBox gains one datatype property with a domain and range, so P11 and P13 are unchanged. The user can run `make oops` to confirm.

## Q27 pest extension (Q27.3)

### Scope

Adds two functional datatype properties, `minorCategory` (label "minor category") and `problemCode` (label "problem code"), both domain `Problem`, range string, following `profiles/q27.yaml` (graph names `Problem.minorCategory`, `Problem.problemCode`). No new class or object property. Reused: `Problem`, `hasProblem`, `majorCategory`, `problemStatus`, `receivedDate`, `duplicateFlag`. The vocabulary gained `minor-category`, `problem-code` and `pest-complaint` in stage 1 (`make vocab` clean).

### Not modeled

| Term | Reason |
| --- | --- |
| `pest-complaint`, pest kind | A computed answer value: the Problems whose minor category is PESTS, named by their problem code. Never stored, so the pest is read from the data. No subclass of `Problem` (stage 3: flat). |
| MICE, ROACHES, OTHER, BED BUGS, FLIES, TERMITES, FLEAS, PESTS | Values of the two properties, not classes, individuals or controlled values. `OTHER` is not a pest name and never means mice. |
| HPD's major, minor and code nesting | Containment between attribute values, not is-a (stage 3); no subclass or object property. |

### Axioms

| Axiom | Reason |
| --- | --- |
| `minorCategory`, `problemCode` domain `Problem` | Each appears only on problems in the graph. |
| `minorCategory`, `problemCode` functional | One value per problem; the loader writes one per row. |

No new disjointness: `Problem` stays disjoint from `Building`, `TaxLot`, `Violation` and `Litigation`. The range is `xsd:string`: HPD's values are text kept as recorded.

### Rules for Stage 6 shapes

- Every `Problem` has exactly one `minorCategory` and one `problemCode` (non-empty text).
- A problem whose `minorCategory` is PESTS carries one of the seven pest codes (MICE, ROACHES, OTHER, BED BUGS, FLIES, TERMITES, FLEAS).
- No `pestKind` or derived pest count is stored.
- Counts and the pest are computed at answer time.

### Answer fields

| Answer field | Ontology | Note |
| --- | --- | --- |
| `problemCode` | `problemCode` | graph name `Problem.problemCode`; the pest, with `minorCategory` PESTS |
| `status` | `problemStatus` | open at the snapshot date |
| `problems` | `hasProblem` | distinct pest problems per code and status, computed |
| `duplicates` | `duplicateFlag` | problems flagged duplicate, computed |
| `complaints` | `complaintId` | distinct complaints, computed |
| `firstReceived`, `lastReceived` | `receivedDate` | earliest and latest date per row, computed |

### Reasoner and example data

- ROBOT with HermiT (1.9.11), as for Q1 to Q28.
- `abox/q27.ttl` gains anchor C's mice problem (PESTS, MICE), an OTHER pest problem and a RADIATOR problem coded OTHER (to show OTHER is not a pest name).
- Negative case `n47`: two problem codes on one problem, flagged inconsistent.
- OOPS! not rerun: the TBox gains two datatype properties with a domain and range, so P11 and P13 are unchanged. The user can run `make oops` to confirm.

