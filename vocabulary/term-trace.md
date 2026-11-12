# Term trace: Q1

Concept IRIs use the base `https://watchline.example/vocab/` followed by the ID below. Graph names are the Neo4j label, relationship type or property. Sources are keys in `data/sources.yaml`.

## Trace

| Concept ID | Preferred label | Lives as | Sub-questions | Source |
| --- | --- | --- | --- | --- |
| `tax-lot` | tax lot | `Lot` node | Q1.1, Q1.2, Q1.4 | `pluto`, `hpd_registrations` |
| `building` | building | `Building` node | Q1.2 | `hpd_registrations` |
| `has-building` | has building | `HAS_BUILDING` relationship | Q1.2 | `hpd_registrations` |
| `bbl` | BBL | `Lot.bbl` | Q1.1, Q1.3 | `pluto`, `hpd_registrations` |
| `bin` | BIN | `Building.bin` | Q1.2, Q1.3 | `hpd_registrations` |
| `address` | address | `Lot.address`, `Building.address` | Q1.1, Q1.2 | `pluto`, `hpd_registrations` |
| `hpd-registered` | HPD registered | `Lot.hpdRegistered` | Q1.1 | `hpd_registrations` |
| `pluto-building-count` | PLUTO building count | `Lot.plutoNumBuildings` | Q1.2 | `pluto` |
| `year-built` | year built | `Lot.yearBuilt` | Q1.4 | `pluto` |
| `building-class` | building class | `Lot.buildingClass` | Q1.4 | `pluto` |
| `residential-units` | residential units | `Lot.unitsRes` | Q1.4 | `pluto` |
| `assessed-total-value` | assessed total value | `Lot.assessedTotal` | Q1.4 | `pluto` |
| `address-resolution-outcome` | address resolution outcome | answer field `outcome` | Q1.3 | `geosupport` |
| `candidate-street-name` | candidate street name | answer field `candidates` | Q1.3 | `geosupport` |
| `related-lot` | related lot | answer field `relatedLots` | Q1.3 | graph (`HAS_BUILDING`) |
| `in-graph` | in graph | answer field `inGraph` | Q1.3 | graph |

Outcome values (scheme `address-resolution-outcomes`): `matched-exactly`, `matched-by-variant`, `ambiguous`, `not-found`, `service-unavailable`. All Q1.3.

## Tagged as not in the graph or vocabulary

| Term | Where it lives |
| --- | --- |
| Geosupport, PLUTO, HPD registrations | Sources, in `data/sources.yaml` |
| Snapshot, release, provenance | Dataset-level records in `data/sources.yaml` and `data/README.md` |
| Condominium billing lot | A documented limit of `related-lot` |

## Pilot restatement

| Question | Restated with approved terms |
| --- | --- |
| Q1 Which tax lot does this address resolve to? | Resolve the typed **address** to a **tax lot** and report its **BBL** with the **address resolution outcome**. |
| Q1.1 | Which **tax lot** (**BBL**, **address**, **HPD registered**) does the resolved **BBL** identify, and is it **in graph**? |
| Q1.2 | Which **buildings** (**BIN**, **address**) does the **tax lot** have, and how does the **PLUTO building count** compare with them? |
| Q1.3 | Was the **address resolution outcome** matched exactly, matched by variant, ambiguous, not found or service unavailable? Which **candidate street names** and **related lots** go with it? |
| Q1.4 | What are the **year built**, **building class**, **residential units** and **assessed total value** of the **tax lot**? |
| Worked example: lot with three buildings | One **tax lot** with three **buildings** (three **BINs**) and one lot-wide **residential units** value. |
| Worked example: PLUTO counts more than HPD lists | **PLUTO building count** 2 against one **building** listed by HPD; both reported, labelled by source. |

No gaps: every domain term in the question, the sub-questions and the worked examples resolves to a concept above.


# Term trace: Q2

Same conventions as Q1. Relationship properties are written `HAS_REGISTRATION.property`.

## Trace

| Concept ID | Preferred label | Lives as | Sub-questions | Source |
| --- | --- | --- | --- | --- |
| `registration` | HPD registration | `Registration` node | Q2.1, Q2.2 | `hpd_registrations` |
| `has-registration` | has registration | `HAS_REGISTRATION` relationship (Building to Registration) | Q2.1 | `hpd_registrations` |
| `registration-id` | registration id | `Registration.registrationId` | Q2.1 | `hpd_registrations` |
| `last-registered-date` | last registered date | `HAS_REGISTRATION.lastRegistered` | Q2.1 | `hpd_registrations` |
| `registration-end-date` | registration end date | `HAS_REGISTRATION.registrationEnd` | Q2.1 | `hpd_registrations` |
| `owner-contact` | registered owner contact | `OwnerContact` node | Q2.2 | `hpd_contacts` |
| `has-owner-contact` | has owner contact | `HAS_OWNER_CONTACT` relationship (Registration to OwnerContact) | Q2.2 | `hpd_contacts` |
| `contact-type` | contact type | `OwnerContact.contactType` | Q2.2 | `hpd_contacts` |
| `owner-name` | owner name | `OwnerContact.name` | Q2.2 | `hpd_contacts` |

Contact type values (scheme `owner-contact-types`): `corporate-owner`, `individual-owner`, `joint-owner`. All Q2.2. Reused from Q1: `building`, `bin`.

## Tagged as not in the graph or vocabulary

| Term | Where it lives |
| --- | --- |
| Registration period (start) | Not in the source; the answer says so |
| Registration currency ("current", "ended") | Derived by the agent from the end date and a stated date; not stored |
| Other contact types (agent, head officer, officer, shareholder, site manager, lessee) | Not owner contacts; belong to later questions (managing agent, officers) |
| Contact business address, title | Not needed for Q2; later questions (party and address questions) |
| `registrationcontactid` | Not unique; not stored |
| Deed grantee, process contact, managing agent | Distinct roles, caveated in `owner-contact`; other questions |

## Pilot restatement

| Question | Restated with approved terms |
| --- | --- |
| Q2 Who is the HPD-registered owner of this building, and when was the registration last filed? | For the **building** (**BIN**), list its **HPD registrations** (**registration id**), each with its **last registered date** and **registration end date**, and the **registered owner contacts** (**contact type**, **owner name**) on each. |
| Q2.1 | Which **HPD registrations** are on record for the **building**, and for each its **last registered date** and **registration end date**? |
| Q2.2 | For each **HPD registration**, which **registered owner contacts** are recorded, with **contact type** and **owner name**? |
| Worked example: co-op owner | **Owner name** `438 52 ST OWNERS CORP` as HPD spells it, **contact type** corporate owner; the spelling differs from PLUTO's and is reported as recorded. |
| Worked example: multi-building lot | Three **buildings**, three **HPD registrations**, each with one **owner contact**; the **owner name** spellings differ and are reported as recorded. |
| Case: registration ended | **Registration end date** 2021-09-01 is before the snapshot date; reported with the dates, not as current. |
| Case: no registration found | No **building** exists for the lot (no HPD registration), so no **HPD registration** or **owner contact** is returned. |

No gaps: every domain term resolves to a concept above. "Current" is the agent's reading of the end date.

# Term trace: Q3

Same conventions as Q1. Relationship properties and answer fields are named in the Lives as column.

## Trace

| Concept ID | Preferred label | Lives as | Sub-questions | Source |
| --- | --- | --- | --- | --- |
| `deed` | deed | `Deed` node | Q3.1, Q3.2 | `acris_master`, `acris_legals` |
| `has-deed` | has deed | `HAS_DEED` relationship (Lot to Deed) | Q3.1 | `acris_legals` |
| `document-id` | document id | `Deed.documentId` | Q3.1 | `acris_master` |
| `document-type` | document type | `Deed.docType` | Q3.1 | `acris_master` |
| `document-date` | document date | `Deed.docDate` | Q3.1 | `acris_master` |
| `recorded-date` | recorded date | `Deed.recordedDate` | Q3.1 | `acris_master` |
| `document-amount` | document amount | `Deed.amount` | Q3.1 | `acris_master` |
| `grantee` | grantee | `Grantee` node | Q3.2 | `acris_parties` |
| `has-grantee` | has grantee | `HAS_GRANTEE` relationship (Deed to Grantee) | Q3.2 | `acris_parties` |
| `grantee-name` | grantee name | `Grantee.name` | Q3.2 | `acris_parties` |
| `mailing-address` | mailing address | `Grantee.mailingAddress`, `OwnerContact.mailingAddress` | Q3.2, Q3.5 | `acris_parties`, `hpd_contacts` |
| `address-line-two` | address line two | `Grantee.addressLine2`, `OwnerContact.addressLine2` | Q3.2, Q3.5 | `acris_parties`, `hpd_contacts` |
| `zip-code` | ZIP code | `Grantee.zip`, `OwnerContact.zip` | Q3.2, Q3.5 | `acris_parties`, `hpd_contacts` |
| `name-agreement` | name agreement | answer field `nameAgreement` | Q3.4 | `src/watchline/compare.py` |
| `address-agreement` | address agreement | answer field `addressAgreement` | Q3.5 | `src/watchline/compare.py` |
| `comparison-rule` | comparison rule | answer field `rule` | Q3.4, Q3.5 | `src/watchline/compare.py` |

Name agreement values (scheme `name-agreement-outcomes`): `exact-normalized`, `normalization-match`, `different`, `not-comparable`. Address agreement values (scheme `address-agreement-outcomes`): `same`, `differs`, `address-absent`. Reused from Q2 for Q3.3: `registration`, `owner-contact`, `owner-name`, `has-registration`, `has-owner-contact`; from Q1: `tax-lot`, `building`, `has-building`.

## Tagged as not in the graph or vocabulary

| Term | Where it lives |
| --- | --- |
| Grantor / party role of a grantor | Not loaded (decision 2026-11-12); a later transaction question adds it |
| Party type code (1, 2, 3) | Source detail; only grantees (2) are read |
| Mortgage, assignment, transfer-tax and index-correction documents | Not deeds here; document types outside the eight deed codes |
| Mail-drop address | Needs a curated list that does not exist yet (open point); the caveat is carried in `mailing-address` and `address-agreement` |
| "Same party", "owner" as a conclusion | Never asserted; a name match is a lead |
| Comparison outcomes | Computed at answer time by `src/watchline/compare.py`, not stored |
| ACRIS document version rows, `modifieddate`, `goodthroughdate` | Used only to choose the current version of a document |
| `crfn`, reel and page, `pcttransferred` | Not needed for Q3 |

## Pilot restatement

| Question | Restated with approved terms |
| --- | --- |
| Q3 Who is the grantee on the most recent deed for this lot, and does the deed name the same party as the HPD registration, compared by exact normalized name? | For the **tax lot**, list the **deed(s)** with the latest **recorded date**, each with its **document id**, **document type**, **document date** and **document amount**, and its **grantees** (**grantee name**, **mailing address**, **address line two**, **ZIP code**); list the **registered owner contacts** on the lot's buildings' **registrations**; report the **name agreement** and **address agreement** with the **comparison rule**. |
| Q3.1 | Which **deeds** does the **tax lot** have, and which has the latest **recorded date**, with its dates and **document amount**? |
| Q3.2 | Which **grantees** does the **deed** have? |
| Q3.3 | Which **registered owner contacts** are on the **registrations** of the lot's **buildings**? (Q2.2 through `has-building`.) |
| Q3.4 | What is the **name agreement** between each **grantee name** and each **owner name**, under which **comparison rule**? |
| Q3.5 | What is the **address agreement** between each grantee's and each owner contact's **mailing address** and **ZIP code**, with the **address line two** reported apart? |
| Worked example: exact agreement (anchor A) | **Deed** `2025032100031001`, **document amount** 0, **grantee** `5413 PLAZA LLC`, **name agreement** exact normalized (N1). The earlier deed for value is reported too. |
| Worked example: spelling difference (anchor G) | Two **grantees** against `KS Turnpike LLC`: **name agreement** different for both, because `K S` is not `KS`. |
| Case: two deeds the same day (anchor D) | Two **deeds** tie on the **recorded date**; both are returned, none chosen. |

No gaps: every domain term resolves to a concept above.

