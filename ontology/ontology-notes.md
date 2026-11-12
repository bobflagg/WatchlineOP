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
| `contactType`, `ownerName` domain `OwnerContact` | Each appears only on owner contacts in the graph. |
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

