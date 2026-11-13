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

Adds two classes (`Registration`, `OwnerContact`), two object properties (`hasRegistration`, `hasOwnerContact`) and five datatype properties. Elements follow `profiles/q02.yaml`. Same namespaces, one ontology IRI, no version IRI.

### Not modeled

| Term | Reason |
| --- | --- |
| `OwnerContact.contactKey` | A loader key (registration, type and name joined). It carries no meaning, is never an answer field, and is marked `identity_only` in `profiles/q02.yaml`. |
| The three owner contact types as classes or individuals | `contactType` is a string as HPD spells it. A subclass per type would add no rule an answer needs; the allowed values are a Stage 6 shape. |
| Whether a registration is current | The agent's reading of `registrationEnd` against a stated date. |
| Registration period start | Not in the source. |

### Axioms

| Axiom | Reason |
| --- | --- |
| `Registration` disjointWith `Building` | A registration is not a building (Stage 3 candidate). Rejects a registration that carries a BIN. |
| `Registration` disjointWith `OwnerContact` | A registration is not a contact on it. Lets the reasoner reject an owner type on a registration. |
| `hasRegistration` domain `Building` | The graph links only buildings to registrations (checked by `make profiles`). |
| `hasOwnerContact`, `registrationId`, `lastRegistered`, `registrationEnd` domain `Registration` | Each appears only on registrations in the graph, except the two dates, which the graph stores on `HAS_REGISTRATION` (see below). |
| `ownerName` domain `OwnerContact` | Appears only on owner contacts in the graph. (`contactType` was widened in Q4; see below.) |
| `registrationId`, `contactType`, `ownerName` functional | Single-valued in the graph: one id per registration, one type and one name per contact (`name` absent, never multiple). |

`lastRegistered` and `registrationEnd` are deliberately not functional. In the graph they are properties of `HAS_REGISTRATION`, one value per building and registration pair. OWL cannot attach a datatype property to an object property without reifying the pair, so the ontology puts them on the registration. A registration covering several buildings can then carry several values, which functional would wrongly reject.

### Rules for Stage 6 shapes

- `registrationId` is a positive integer and present on every registration; `contactType` is one of `CorporateOwner`, `IndividualOwner`, `JointOwner` and present on every owner contact.
- Every registration is linked to at least one building; every owner contact to exactly one registration.
- At most one `lastRegistered` and one `registrationEnd` per building and registration pair (a relationship property).
- `registrationEnd` is never before `lastRegistered`.
- An owner contact with no name has `ownerName` absent, never an empty string.
- Names are reported as recorded; no rule merges or compares spellings.

### Answer fields

Each field of `profiles/q02.yaml` against the ontology.

| Answer field | Ontology | Note |
| --- | --- | --- |
| `bin` | `bin` | from Q1 |
| `registrations` | `hasRegistration` | all, none chosen |
| `registrationId` | `registrationId` | |
| `lastRegistered`, `registrationEnd` | `lastRegistered`, `registrationEnd` | relationship properties in the graph |
| `owners` | `hasOwnerContact` | all, none chosen; empty means none recorded |
| `contactType`, `name` | `contactType`, `ownerName` | graph name `OwnerContact.name` |

### Reasoner and example data

- Same tools as Q1: ROBOT 1.9.11 with HermiT, Java 11.
- `abox/q02.ttl` (verified fixtures; person names not repeated): see the run below.
- Negative cases, each meant to be flagged inconsistent: `n05` (registration that is a building), `n06` (two registration ids), `n07` (owner type on a registration).

### Pitfall scan

OOPS! (2026-11-12, `make oops`, run by the user, TBox only; raw report `oops-report.rdf`): one pitfall.

| Pitfall | Level | Finding | Handling |
| --- | --- | --- | --- |
| P13 inverse relationships not declared | Minor | Affects 3 properties: `hasBuilding`, `hasRegistration`, `hasOwnerContact` | Left as is, as for Q1. The graph stores one direction and can be traversed both ways. Add an inverse when a question needs it. |

No critical or important pitfall.


## Q3

### Scope

Adds two classes (`Deed`, `Grantee`), two object properties (`hasDeed`, `hasGrantee`) and nine datatype properties, three of them shared by `Grantee` and `OwnerContact`. Elements follow `profiles/q03.yaml`. Same namespaces, one ontology IRI, no version IRI.

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
| `Grantee` disjointWith `OwnerContact` | A deed party is not an HPD contact (Stage 3 candidate). Keeps the two sides of the comparison apart. |
| `hasDeed` domain `TaxLot` | The graph links only lots to deeds (checked by `make profiles`). |
| `hasGrantee`, `documentId`, `documentType`, `documentDate`, `recordedDate`, `documentAmount` domain `Deed` | Each appears only on deeds in the graph. |
| `granteeName` domain `Grantee` | Appears only on grantees in the graph. |
| `mailingAddress` domain `Grantee` or `OwnerContact` or `RoleContact` | Grantees, owner contacts (Q3) and role contacts (Q4) all carry a mailing address; the union keeps one property for all, as `address` does for lots and buildings. |
| `addressLineTwo` domain `Grantee` or `OwnerContact` or `RoleContact` | Same reasoning as `mailingAddress`. |
| `zipCode` domain `Grantee` or `OwnerContact` or `RoleContact` | Same reasoning as `mailingAddress`. |
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
| `owners` | `hasOwnerContact` | Q2 path through the lot's buildings; the owner address is the three properties above |
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
| P13 inverse relationships not declared | Minor | Affects 5 properties: `hasBuilding`, `hasRegistration`, `hasOwnerContact`, `hasDeed`, `hasGrantee` | Left as is, as for Q1 and Q2. The graph stores one direction and can be traversed both ways. Add an inverse when a question needs it. |

No critical or important pitfall.


## Q4

### Scope

Adds one class (`RoleContact`), one object property (`hasRoleContact`) and three datatype properties (`contactTitle`, `corporationName`, `personName`). Q4 also reuses `contactType` (now on owner and role contacts) and widens `mailingAddress`, `addressLineTwo` and `zipCode` to role contacts. Elements follow `profiles/q04.yaml`.

### Not modeled

| Term | Reason |
| --- | --- |
| `RoleContact.contactKey` | A loader key. Identity only, never an answer field (`identity_only` in `profiles/q04.yaml`). |
| The six role types (agent, head officer, officer, shareholder, site manager, lessee) as classes | `contactType` is a string as HPD spells it. A subclass per role would add no rule an answer needs, and a title must never change a role. The allowed values are a Stage 6 shape. |
| "Managing agent" as a relationship between parties | HPD lists a contact on a registration; it records no link to an owner. Modeling one would invite reading management as ownership. |
| `contactdescription`, business city and state, `registrationcontactid`, contact currency | Not stored (see `not_stored` in the profile). |

### Axioms

| Axiom | Reason |
| --- | --- |
| `RoleContact` disjointWith `OwnerContact` | A contact is an owner or a role contact by type; the project keeps them apart (Stage 3 candidate). Rejects one node carrying both. |
| `RoleContact` disjointWith `Grantee` | A deed party is not an HPD contact. Same reasoning as `Grantee` and `OwnerContact` (Q3). |
| `Registration` disjointWith `RoleContact` | A registration is not a contact on it. Same reasoning as `OwnerContact` (Q2). |
| `hasRoleContact` domain `Registration` | The graph links only registrations to role contacts (checked by `make profiles`). |
| `contactTitle`, `corporationName`, `personName` domain `RoleContact` | Each appears only on role contacts in the graph. `ownerName` stays separate on owner contacts. |
| `contactType` domain `OwnerContact` or `RoleContact` | One property for both kinds of contact, as `mailingAddress` is shared; the union is the only domain every use satisfies. |
| `contactTitle`, `corporationName`, `personName` functional | Single-valued in the graph, absent (never multiple) when blank. |

### Rules for Stage 6 shapes

- `contactType` is present on every role contact and one of `Agent`, `HeadOfficer`, `Officer`, `Shareholder`, `SiteManager`, `Lessee`; owner types are rejected here.
- Every role contact is linked to exactly one registration.
- `contactTitle`, `corporationName`, `personName` and the address properties are absent when blank, never an empty string.
- `corporationName` appears only on agents and lessees.
- A site manager has no `mailingAddress`, `addressLineTwo` or `zipCode`.
- Titles and names are stored as recorded (trimmed only); a title never changes the type.
- An empty set of role contacts means none is recorded; none is inferred.

### Answer fields

Each field of `profiles/q04.yaml` against the ontology.

| Answer field | Ontology | Note |
| --- | --- | --- |
| `registrationId` | `registrationId` | from Q2 |
| `contacts` | `hasRoleContact` | all, none chosen; empty means none recorded |
| `contactType` | `contactType` | graph name `RoleContact.contactType` |
| `title` | `contactTitle` | graph name `RoleContact.title` |
| `corporationName`, `personName` | `corporationName`, `personName` | |
| `mailingAddress`, `addressLine2`, `zip` | `mailingAddress`, `addressLineTwo`, `zipCode` | graph names `addressLine2`, `zip`; shared with grantees and owner contacts |
| registration dates, snapshot date | `lastRegistered`, `registrationEnd`; dataset-level | registration dates are Q2.1; snapshot date is dataset provenance in `data/sources.yaml` |

### Reasoner and example data

- ROBOT 1.9.11 with HermiT, as for Q1 to Q3.
- `abox/q04.ttl` (verified fixtures; person names not repeated): see `make ontology` below.
- Negative cases, each meant to be flagged inconsistent: `n11` (a contact that is both role and owner contact), `n12` (two contact types on one contact).

### Pitfall scan

OOPS! (2026-11-12, `make oops`, run by the user, TBox only; raw report `oops-report.rdf`): one pitfall.

| Pitfall | Level | Finding | Handling |
| --- | --- | --- | --- |
| P13 inverse relationships not declared | Minor | Affects 6 properties: `hasBuilding`, `hasRegistration`, `hasOwnerContact`, `hasDeed`, `hasGrantee`, `hasRoleContact` | Left as is, as for Q1 to Q3. The graph stores one direction and can be traversed both ways. Add an inverse when a question needs it. |

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
| `DosEntity` disjointWith `OwnerContact` | A state filing record is not an HPD contact (Stage 3 candidate). Rejects merging the two on a name match. |
| `DosEntity` disjointWith `Grantee` | A state filing record is not a deed party (Stage 3 candidate). Same reasoning. |
| `DosEntity` disjointWith `RoleContact` | Not an HPD contact of any kind; keeps the disjointness uniform across contact classes. |
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
- Negative cases, each meant to be flagged inconsistent: `n13` (DOS entity that is an owner contact), `n14` (that is a grantee), `n15` (two DOS ids on one record).

### Pitfall scan

Pending: `make oops` (TBox only) failed on 2026-11-13 because oops.linkeddata.es was unreachable (timeout from `make oops` and from curl; the site did not load in a browser). Retry later. Expected: P13 (now 6 properties, unchanged, no new object property) and possibly P32 (same label on several properties: the 10 address parts, by design).
