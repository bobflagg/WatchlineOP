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
| `contact` | contact | `Contact` node (all nine HPD types, merged decision 2026-11-15) | Q2.2 | `hpd_contacts` |
| `owner-contact` | registered owner contact | `Contact` nodes with an owner type (answer concept, narrower than `contact`) | Q2.2 | `hpd_contacts` |
| `has-contact` | has contact | `HAS_CONTACT` relationship (Registration to Contact) | Q2.2 | `hpd_contacts` |
| `contact-type` | contact type | `Contact.contactType` (scheme `contact-types`) | Q2.2 | `hpd_contacts` |
| `corporation-name` | corporation name | `Contact.corporationName` | Q2.2 | `hpd_contacts` |
| `person-name` | person name | `Contact.personName` | Q2.2 | `hpd_contacts` |
| `owner-name` | owner name | derived at answer time: `Contact.corporationName` of a corporate owner, else `Contact.personName` (answer concept, not stored) | Q2.2, Q3.4 | `hpd_contacts` |

Contact type values (scheme `contact-types`; the three owner types are also in `owner-contact-types`): `corporate-owner`, `individual-owner`, `joint-owner`. All Q2.2. Reused from Q1: `building`, `bin`.

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
| `mailing-address` | mailing address | `Grantee.mailingAddress`, `Contact.mailingAddress` | Q3.2, Q3.5 | `acris_parties`, `hpd_contacts` |
| `address-line-two` | address line two | `Grantee.addressLine2`, `Contact.addressLine2` | Q3.2, Q3.5 | `acris_parties`, `hpd_contacts` |
| `zip-code` | ZIP code | `Grantee.zip`, `Contact.zip` | Q3.2, Q3.5 | `acris_parties`, `hpd_contacts` |
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

## Q4 trace

| Concept ID | Preferred label | Lives as | Sub-questions | Source |
| --- | --- | --- | --- | --- |
| `role-contact` | role contact | `Contact` nodes with a non-owner type (answer concept, narrower than `contact`) | Q4.1 | `hpd_contacts` |
| `contact-type` | contact type | `Contact.contactType` (scheme `role-contact-types` for the six role types), reused from Q2 | Q4.1 | `hpd_contacts` |
| `contact-title` | contact title | `Contact.title` | Q4.1 | `hpd_contacts` |
| `corporation-name`, `person-name` | (Q2 concepts, reused) | `Contact.corporationName`, `Contact.personName` | Q4.1 | `hpd_contacts` |
| `mailing-address`, `address-line-two`, `zip-code` | (Q3 concepts, reused) | `Contact.mailingAddress`, `.addressLine2`, `.zip` | Q4.2 | `hpd_contacts` |

Role values (scheme `role-contact-types`): `agent` (label managing agent), `head-officer`, `officer`, `shareholder`, `site-manager`, `lessee`. Tagged not in the graph: `contactdescription`, business city and state, `registrationcontactid`.

## Q4 pilot restatement

| Question | Restated with approved terms |
| --- | --- |
| Q4 | For each **registration** of the **building**, list the **role contacts** (**contact type**, **contact title**, **corporation name**, **person name**) and their **mailing address**, **address line two** and **ZIP code**; the **registered owner contacts** come from Q2.2. |
| Q4.1 | Which **role contacts** does each **registration** have, with **contact type** and **contact title**? |
| Q4.2 | What **mailing address** does each **role contact** have? |
| Anchor A | Four role contacts beside the owner; three share one **mailing address**, the **site manager** has none: a record link, not identity. |
| Anchor C | The **managing agent** carries a **corporation name** and a **person name**; the **head officer** title is `PRESIDENT OF CO`. |

No gaps.

# Term trace: Q5

| Concept ID | Preferred label | Lives as | Sub-questions | Source |
| --- | --- | --- | --- | --- |
| `dos-entity` | DOS entity | `DosEntity` node | Q5.1 | `nys_corporations` |
| `dos-id` | DOS id | `DosEntity.dosId` | Q5.1 | `nys_corporations` |
| `dos-entity-name` | DOS entity name | `DosEntity.name` | Q5.1 | `nys_corporations` |
| `entity-type` | entity type | `DosEntity.entityType` | Q5.1 | `nys_corporations` |
| `jurisdiction` | jurisdiction | `DosEntity.jurisdiction` | Q5.1 | `nys_corporations` |
| `initial-filing-date` | initial filing date | `DosEntity.filingDate` | Q5.1 | `nys_corporations` |
| `dos-process-name` | DOS process name | `DosEntity.processName` | Q5.2 | `nys_corporations` |
| `dos-process-address` | DOS process address | `DosEntity.processAddress`, `.processAddressLine2`, `.processCity`, `.processState`, `.processZip` | Q5.2 | `nys_corporations` |
| `registered-agent-name` | registered agent name | `DosEntity.agentName` | Q5.3 | `nys_corporations` |
| `registered-agent-address` | registered agent address | `DosEntity.agentAddress`, `.agentAddressLine2`, `.agentCity`, `.agentState`, `.agentZip` | Q5.3 | `nys_corporations` |
| `comparison-rule` | (Q3 concept, extended) | rule N3 added; computed, not stored | Q5.1 | `src/watchline/compare.py` |

Tagged not in the graph: `ceoname`, `locationname` (empty for LLCs; contract says "not carried"), county, `nameKey` (a loader lookup key, not an answer field), any link from Contact or Grantee to DosEntity (a name match is computed at answer time), officers and managers (not carried; Q5.4 retrieval).

## Q5 pilot restatement

| Question | Restated with approved terms |
| --- | --- |
| Q5 | For an owner name, list each **DOS entity** whose name agrees under a stated **comparison rule**, with **entity type**, **jurisdiction**, **initial filing date**, **DOS process name** and **address**, and **registered agent name** and **address**; otherwise "no record". |
| Anchor A | The **DOS process name** is the entity's own name; no **registered agent**. |
| Anchor G | The **DOS process name** is a person: where service goes, not who runs it. |
| Anchor C | The deed spelling matches the **DOS entity name** under rule N3; the HPD spelling has no record. |
| Anchor D | No record under the HPD spelling; the long form is a Q22 candidate. |

No gaps.

Q5 stage 4 (2026-11-13): related links added or dropped only; no concept, ID or label changed. See `thesaurus-notes.md`.

# Term trace: Q8

| Concept ID | Preferred label | Lives as | Sub-questions | Source |
| --- | --- | --- | --- | --- |
| `operational-network` | operational network | `OperationalNetwork` node | Q8.1, Q8.2 | `bor_layers` |
| `network-group-id` | network id | `OperationalNetwork.groupId` | Q8.1 | `bor_layers` |
| `network-split` | network split | `OperationalNetwork.split` (values `wcc`, `louvain`; scheme `network-splits`) | Q8.1 | `bor_layers` |
| `in-network` | in network | `IN_NETWORK` relationship (Lot to OperationalNetwork) | Q8.1, Q8.2 | `bor_layers` |
| `landlord` | landlord | `Landlord` node, `Landlord.nodeId` | Q8.3 | `bor_layers` |
| `landlord-name` | landlord name | `Landlord.name` | Q8.3, Q8.1, Q9.1 | `bor_layers` |
| `business-address` | business address | `Landlord.businessAddresses` (list of strings) | Q8.3 | `bor_layers` |
| `anchor-landlord` | anchor landlord | `ANCHORED_BY` relationship (OperationalNetwork or OwnerPortfolio to Landlord) | Q8.1, Q9.1 | `bor_layers` |
| `based-on-contact` | based on contact | `BASED_ON_CONTACT` relationship (Landlord to Contact) | Q8.3 | `bor_layers` |
| `covers` | covers | `COVERS` relationship (Landlord to Lot), property `registrationId` (reuses `registration-id`) | Q8.3 | `bor_layers`, `hpd_registrations` |
| `connected-by-name` | connected by name | `CONNECTED_BY_NAME` relationship (Landlord to Landlord), properties `weight`, `networkEdgeId`, `networkGroupId` | Q8.3 | `bor_layers` |
| `connected-by-address` | connected by address | `CONNECTED_BY_ADDRESS` relationship (Landlord to Landlord), properties `weight`, `networkEdgeId`, `networkGroupId` | Q8.3 | `bor_layers` |
| `connected-by-identity` | connected by identity | `CONNECTED_BY_IDENTITY` relationship (Landlord to Landlord), properties `stage`, `evidenceType`, `evidenceId`, `weight`, `portfolioEdgeId`, `portfolioGroupId`, `networkEdgeId`, `networkGroupId` | Q8.3, Q9.3 | `bor_layers` |
| `edge-id` | edge id | `networkEdgeId`, `portfolioEdgeId` on the link relationships | Q8.3, Q9.3 | `bor_layers` |
| `link-weight` | link weight | `CONNECTED_BY_NAME.weight`, `CONNECTED_BY_ADDRESS.weight`, `CONNECTED_BY_IDENTITY.weight` | Q8.3 | `bor_layers` |
| `network-absence` | network absence | `Lot.networkAbsence` (scheme `network-absence-reasons`, top level) | Q8.4 | `bor_layers` |
| `network-absence-detail` | network absence detail | `Lot.networkAbsenceDetail` (the 11 detail values seen in this layer, narrower than the top level) | Q8.4 | `bor_layers` |

Controlled values store the source's own code (hidden label of the concept). Tagged not in the graph: node names and addresses (the landlord's name and address stay in the source; Q3 and Q6 cover them), run, release and snapshot ids (dataset-level, in `data/sources.yaml`), the Owner Portfolio layer (Q9), the 13 absence detail codes that do not occur in this layer, node-observation candidate counts and ambiguity flags, split attempts, and edge component ids. The member counts, building list and residential units of Q8.2 are computed from `IN_NETWORK`, `Lot` and `HAS_BUILDING`, not stored.

## Q8 pilot restatement

| Question | Restated with approved terms |
| --- | --- |
| Q8 | For a building's lot, name the **operational network** it is **in** (its **network id**, with the run named once for the dataset), say whether its **network split** is a **whole component** or a **Louvain community**, list the member lots, buildings and residential units, and list the **network links** between **landlords** with their **link weight** split into **name weight**, **address weight** and **identity weight**; if the lot is in no network, give its **network absence** and **network absence detail**. |
| Anchor C | Network ON-98617: three **landlords**, one covering three lots; two links with identity weight only, one with all three weights. |
| Anchor D | A **whole component** of 35 lots and four landlords. |
| ON-675 | A **Louvain community**: 25 of its links **cross networks**. |
| Anchors A and F | In no network: **no qualifying linkage** (`no_linkage`) and **outside source coverage** (`no_registration`). |

No gaps.

Q8 stage 4 (2026-11-13): related links, hidden labels and notes added only; no concept, ID or preferred label changed. See `thesaurus-notes.md`.

# Term trace: Q9

| Concept ID | Preferred label | Lives as | Sub-questions | Source |
| --- | --- | --- | --- | --- |
| `owner-portfolio` | owner portfolio | `OwnerPortfolio` node | Q9.1, Q9.2, Q9.4 | `bor_layers` |
| `portfolio-group-id` | portfolio id | `OwnerPortfolio.groupId` | Q9.1 | `bor_layers` |
| `portfolio-composition` | portfolio composition | `OwnerPortfolio.composition` (values `identity`, `deed_only`, `deed_bridged`; scheme `portfolio-compositions`) | Q9.1 | `bor_layers` |
| `in-portfolio` | in portfolio | `IN_PORTFOLIO` relationship (Lot to OwnerPortfolio) | Q9.1, Q9.2, Q9.4 | `bor_layers` |
| `connected-by-deed` | connected by deed | `CONNECTED_BY_DEED` relationship (Landlord to Landlord), properties `stage`, `evidenceType`, `evidenceId`, `portfolioEdgeId`, `portfolioGroupId` | Q9.3 | `bor_layers` |
| `evidence-type` | evidence type | `evidenceType` on identity and deed links (scheme `link-evidence-types`) | Q9.3 | `bor_layers` |
| `evidence-id` | evidence id | `evidenceId` on identity and deed links | Q9.3 | `bor_layers` |
| `masked-address-edges` | masked address edges | `NetworkMaskedAddress.maskedEdges` | Q6.2 | `bor_layers` |
| `ownership-signal` | ownership signal | `CONNECTED_BY_IDENTITY.stage`, `CONNECTED_BY_DEED.stage` (the six BOR stage codes; scheme `ownership-signals`) | Q9.3 | `bor_layers` |
| `portfolio-absence` | portfolio absence | `Lot.portfolioAbsence` (top level of `network-absence-reasons`) | Q9.5 | `bor_layers` |
| `portfolio-absence-detail` | portfolio absence detail | `Lot.portfolioAbsenceDetail` (18 detail codes in this layer) | Q9.5 | `bor_layers` |
| `landlord`, `covers`, `registration-id` | (Q8 concepts, reused) | `Landlord`, `COVERS`; the Landlord layer is now the union of both layers' records (31035) | Q9.3 | `bor_layers` |
| `network-absence-reasons` | (scheme, extended) | one scheme for both layers: 8 new detail concepts, all under the five existing top-level reasons; label now "Absence reasons", IRI unchanged | Q9.5 | `bor_layers` |

Tagged not in the graph: group anchor (a display choice, not an owner), `witness_pieces`, `total_lot_count` (the co-op and condo lots outside the footprint are counted only through their absence reason), node names, decision events and support records behind each signal, evidence items, the five BOR detail codes this layer and the network layer do not use (`not_latest_registration`, `deed_hub_capped`, `curated_exclusion`, `group_below_min_size`, `pair_below_threshold`), and the comparison with the network (computed from `IN_PORTFOLIO` and `IN_NETWORK`, like the member counts of Q9.2).

## Q9 pilot restatement

| Question | Restated with approved terms |
| --- | --- |
| Q9 | For a building's lot, name its **owner portfolio** (**portfolio id**, **portfolio composition**), count its member lots, buildings and units (counting units named, rental lots only), list the **portfolio links** with their **ownership signal**, and compare its footprint with the lot's **operational network** (members in one and not the other); if the lot is in no portfolio, give its **portfolio absence** and **portfolio absence detail**. |
| Anchor D | **Identity-based** portfolio OP-53559: 33 lots, 42 buildings, 454 units, against 35 lots in its network; the two network-only lots are listed. |
| Anchor C | **Identity-based** OP-98617: the same five lots as ON-98617, 116 units; not excluded as a co-op. |
| Deed cases | OP-10201 **deed only**; OP-5346 **deed bridged** (two identity steps joined by a **deed held since** step). |
| Co-op case | 1000317501 is in no portfolio: **co-op or condo excluded**. |

No gaps.

# Term trace: Q6

| Concept ID | Preferred label | Lives as | Sub-questions | Source |
| --- | --- | --- | --- | --- |
| `network-masked-address` | network masked address | `NetworkMaskedAddress` node (73) | Q6.2 | `bor_layers` |
| `masked-address-id` | masked address id | `NetworkMaskedAddress.addressId` | Q6.2 | `bor_layers` |
| `masked-address-text` | masked address text | `NetworkMaskedAddress.address` | Q6.2 | `bor_layers` |
| `masked-address-degree` | masked address degree | `NetworkMaskedAddress.degree` | Q6.2 | `bor_layers` |
| `portfolio-masked-address` | portfolio masked address | `PortfolioMaskedAddress` node (579, derived from 5298 masked identities) | Q6.3 | `bor_layers` |
| `portfolio-masked-address-text` | portfolio masked address text | `PortfolioMaskedAddress.address` | Q6.3 | `bor_layers` |
| `portfolio-masked-address-degree` | portfolio masked address degree | `PortfolioMaskedAddress.degree` | Q6.3 | `bor_layers` |
| `masked-identities` | masked identities | `PortfolioMaskedAddress.maskedIdentities` | Q6.3 | `bor_layers` |
| `mail-drop-address` | mail-drop address | `MailDropAddress` node (122; identity `listKey`) | Q6.4 | `mail_drop_list` |
| `mail-drop-address-key` | mail-drop address key | `MailDropAddress.address` | Q6.4 | `mail_drop_list` |
| `zip-five` | ZIP five | `MailDropAddress.zip5` | Q6.4 | `mail_drop_list` |
| `mail-drop-kind` | mail-drop kind | `MailDropAddress.kind` (scheme `mail-drop-kinds`, 4 values) | Q6.4 | `mail_drop_list` |
| `mail-drop-basis` | mail-drop basis | `MailDropAddress.basis` | Q6.4 | `mail_drop_list` |
| `list-review-status` | list review status | `MailDropAddress.reviewStatus` (scheme `list-review-statuses`, value `unreviewed`) | Q6.4 | `mail_drop_list` |
| `mailing-address`, `address-line-two`, `zip-code`, `contact`, `owner-contact`, `role-contact`, `registration`, `building` | (Q2 to Q4 concepts, reused) | contact addresses on `Contact`; counted at query time | Q6.1 | `hpd_contacts` |

Not in the graph, tagged "answer contract" or "tool output": the address key of Q6.1 (uppercase street line plus first five ZIP characters), the counts (computed at query time), the masking threshold, method and normalizer version (one value each, in `data/sources.yaml`). Q6.3 is in the graph since 2026-11-15 (`PortfolioMaskedAddress`, derived from the identity masks).

Pilot restatement: "Was this address masked by the Operational Network method (a network masked address, with its degree), is it on the mail-drop list (a mail-drop address with a kind), and how many HPD contacts, registrations and buildings carry it?" The Owner Portfolio method records no address.


## Q7 pilot restatement

| Concept | Label | Graph element | Question | Source |
| --- | --- | --- | --- | --- |
| `document` | document | `Document` node (96,901; key `documentId`) | Q7.3 | `acris_master`, `acris_parties` |
| `document-party` | party of a document | `DocumentParty` node (312,981; identity `partyKey`) | Q7.3 | `acris_parties` |
| `has-party` | has party | `HAS_PARTY` relationship (314,366) | Q7.3 | `acris_parties` |
| `party-name` | party name | `DocumentParty.name` (lookup key `nameKey`, rule N3) | Q7.3 | `acris_parties` |
| `party-role` | party role | `HAS_PARTY.partyType` (recorded code 1, 2, 3) | Q7.3 | `acris_parties` |
| `address-party-count` | distinct names at an address | `DocumentParty.addressNames` (over all ACRIS) | Q7.3 | `acris_parties` |
| `address-document-count` | documents at an address | `DocumentParty.addressDocuments` (over all ACRIS) | Q7.3 | `acris_parties` |
| `process-address-entity-count` | process address entity count | `DosEntity.processAddressEntities` (over the whole DOS table) | Q7.2 | `nys_corporations` |
| `set-aside` | set aside | not stored: answer field `setAside` computed from the Q6 masks and the mail-drop list | Q7.4 | `bor_layers`, `mail_drop_list` |
| `corporation-name` | (reused) | `Contact.nameKey` (lookup key, rule N3) | Q7.1 | `hpd_contacts` |

Not in the graph: shared addresses, shared people and links between two given entities (found at answer time by name key, a lead), the group, absence reason and links of Q7.5 (read from existing nodes), and documents outside scope C.

Pilot restatement: "Which people, business addresses, DOS process addresses and ACRIS documents do these two entities share, which of those sit at an address a method masked or the mail-drop list holds, and did either BOR layer group them?"

# Term trace: Q10

Q10 adds no concept, node, relationship or property. Every term is already approved by Q6, Q8 or Q9; the differences between the layers are computed, not stored.

| Term | Where it comes from | Used in | Source |
| --- | --- | --- | --- |
| `operational-network`, `network-group-id`, `network-split`, `in-network` | Q8 | Q10.1, Q10.3 | `bor_layers` |
| `owner-portfolio`, `portfolio-group-id`, `portfolio-composition`, `in-portfolio` | Q9 | Q10.1, Q10.3 | `bor_layers` |
| `connected-by-name`, `connected-by-address`, `connected-by-identity`, `connected-by-deed` | Q8, Q9 | Q10.2, Q10.3 (link kind = relationship type and `stage`) | `bor_layers` |
| `ownership-signal` | Q9 | Q10.2, Q10.3 (`deed.held_since`, `deed.linked_successor`, identity stages) | `bor_layers` |
| `business-address`, `masked-address-edges` | Q8 | Q10.2 (address-only links explain network-only lots) | `bor_layers` |

Tagged not in the graph: the difference lists, the count of networks holding several portfolios (476) and of portfolios spanning several networks (13 in the graph, 14 in the release), and the link kinds that explain a difference (computed from `networkGroupId` and `portfolioGroupId` on the link relationships).

## Q10 pilot restatement

| Question | Restated with approved terms |
| --- | --- |
| Q10 | For a building's lot, name its **operational network** and **owner portfolio** (ids, run, member lots), list the lots in one and not the other, and for each name the link kinds (**connected by address**, **connected by name**, **connected by identity**, **connected by deed**, with **ownership signal**) that carry only one layer's group id. Release-wide: networks holding several portfolios, and portfolios spanning several networks. |
| Anchor D | ON-18742 holds two lots OP-53559 does not; both are joined only by **connected by address** links (3 each). |


# Term trace: Q11

| Concept ID | Preferred label | Lives as | Sub-questions | Source |
| --- | --- | --- | --- | --- |
| `affiliation` | affiliation | answer contract item (computed) | Q11.1 to Q11.4 | derived from the rows below |
| `affiliation-types` scheme: `ownership-affiliation`, `parent-affiliation`, `management-affiliation`, `financing-affiliation`, `other-affiliation` | ownership, parent company, management, financing, other affiliation | answer contract values; the mapping from `Contact.contactType` is in `tests/q11_2/fixtures.yaml` | Q11.1 to Q11.4 | `hpd_contacts`, `acris_parties`, `nys_corporations`, `bor_layers` |
| `evidence-statuses` scheme: `documented`, `hypothesized`, `reported` | documented, hypothesized, reported | answer contract values | Q11.1 to Q11.4 | as above |
| `mortgage` | mortgage | `Document` with `docType` MTGE (scope M) | Q11.1 | `acris_master`, `acris_parties` |
| `borrower`, `lender` | borrower, lender | `HAS_PARTY.partyType` 1 and 2 on a mortgage | Q11.1 | `acris_parties` |

Reused: `document`, `document-party`, `has-party`, `party-name`, `party-role` (Q7.3); `contact`, `contact-type`, the nine contact types, `corporation-name`, `person-name`, `contact-title` (Q2 to Q4); `dos-entity` and the DOS process properties (Q5); `operational-network`, `owner-portfolio`, `in-network`, `in-portfolio`, `network-absence`, `portfolio-absence` (Q8, Q9).

Tagged not in the graph: the affiliation type and evidence status of each item (computed from the role or source), the shared-borrower relationship (computed from co-borrowers on one mortgage), the parent relationship (no source documents one), and reported claims (retrieval, session evidence).

## Q11 pilot restatement

| Question | Restated with approved terms |
| --- | --- |
| Q11 | For an entity name, list each **affiliation** with its **affiliation type** (ownership, parent company, management, financing, other), its **evidence status** (documented, hypothesized, reported) and its source: **mortgages** as **borrower** or **lender** (Q11.1), HPD roles on its registrations (Q11.2), the DOS process contact (Q11.3), and Operational Network and Owner Portfolio membership of its lots (Q11.4, hypothesized). |
| Anchors A and B | A financing affiliation (lender `CONNECTONE BANK`) and a shared-borrower record on one mortgage; management by an agent and site manager and an ownership interest by a shareholder on HPD; a DOS process contact at a five-entity address; no group lead. No parent company is documented. |
| Anchor C | Not found by name: ACRIS and HPD spell the owners corporation differently (a recorded gap). |


# Term trace: Q12

| Concept ID | Preferred label | Lives as | Sub-questions | Source |
| --- | --- | --- | --- | --- |
| `grantor` | grantor | `Grantor` node (partyKey, name, nameKey, mailingAddress, addressLine2, zip) | Q12.1, Q12.3 | `acris_parties` (partytype 1) |
| `has-grantor` | has grantor | `HAS_GRANTOR` relationship | Q12.1, Q12.3 | `acris_parties` |
| `grantor-name` | grantor name | `Grantor.name`; lookup key `Grantor.nameKey` (and `Grantee.nameKey`, rule N3) | Q12.1, Q12.3 | `acris_parties` |
| `not-a-sale` | not a sale | answer contract flag (amount 0, or type CORRD or CONDEED) | Q12.1, Q12.2 | `acris_master` |
| `attributable-transfer` | attributable transfer | answer contract, derived by name key | Q12.3 | `acris_parties`, `hpd_contacts` |

Reused: `deed`, `has-deed`, `grantee`, `has-grantee`, `grantee-name`, `document-type`, `document-date`, `recorded-date`, `document-amount` (Q3); `corporate-owner`, `contact` (Q2); `owner-portfolio`, `in-portfolio`, `portfolio-group-id`, `portfolio-composition` (Q9).

Tagged not in the graph: the period, deed and not-a-sale counts, the other-lot count of a multi-lot deed, portfolio deed lists and the attribution (computed from `HAS_DEED`, `HAS_GRANTOR`, `HAS_GRANTEE`, `IN_PORTFOLIO` and the registered owners); "current owner" as a stored fact; the sale price as intent.

## Q12 pilot restatement

| Question | Restated with approved terms |
| --- | --- |
| Q12 | For a lot and a period, list its **deeds** (document, dates, **document amount**, **grantors**, **grantees**), count the deeds and those that are **not a sale**; repeat for the lots of its **owner portfolio** (run, each deed once); mark each deed an **attributable transfer** or not by comparing the parties' names with the lot's **corporate owner**. |
| Anchor A | 7 deeds, 2 since 2015: a $5,000,000 deed and a $0 deed with the same grantor and grantee; the second is not a sale; both are attributable transfers (the registered owner is a party). |


# Term trace: Q13

| Concept ID | Preferred label | Lives as | Sub-questions | Source |
| --- | --- | --- | --- | --- |
| `financing-document` | financing document | `Document` node whose `docType` is MTGE, ASST, SAT, AGMT, AL&R, TL&R or SAGE and that has a `HAS_FINANCING_DOCUMENT` link | Q13.1, Q13.2, Q13.3 | `acris_master`, `acris_legals` |
| `has-financing-document` | has financing document | `HAS_FINANCING_DOCUMENT` relationship (Lot to Document) | Q13.1 | `acris_legals` |
| `assignment` | assignment | answer contract kind (ASST, AL&R) | Q13.3 | `acris_master` |
| `satisfaction` | satisfaction | answer contract kind (SAT) | Q13.3 | `acris_master` |
| `termination` | termination | answer contract kind (TL&R) | Q13.3 | `acris_master` |
| `agreement` | agreement | answer contract kind (AGMT, SAGE) | Q13.3 | `acris_master` |

Reused: `mortgage`, `borrower`, `lender` (Q11); `document`, `document-party`, `has-party`, `party-name`, `party-role` (Q7); `document-type`, `document-date`, `recorded-date`, `document-amount`, `mailing-address`, `address-line-two`, `zip-code` (Q3); `tax-lot` (Q1).

Thesaurus (Stage 4): related links `mortgage`-`satisfaction`, `mortgage`-`agreement`, `assignment`-`termination`, `satisfaction`-`termination`, `has-deed`-`has-financing-document`; hidden labels added; no concept IDs changed.

Hierarchy (Stage 3): `mortgage`, `assignment`, `satisfaction`, `termination` and `agreement` are narrower than `financing-document`; vocabulary only, not stored.

Tagged not in the graph: the kind and description of a document type, the counts by kind, the other-lot count, "which loan is outstanding" (never answered), a derived conclusion from a termination or a missing satisfaction (Type II), the snapshot date (dataset-level), the borrower and lender roles of non-mortgage party codes.

## Q13 pilot restatement

| Question | Restated with approved terms |
| --- | --- |
| Q13 | For a tax lot, list each **financing document** (**document type** with its description, **document date**, **recorded date**, **document amount**) with its **document parties** as recorded (**borrower** and **lender** on a **mortgage**), separating **mortgages**, **assignments**, **satisfactions**, **terminations** and **agreements**; state that no satisfaction or a termination is not proof of the loan's status. |
| Anchor C | 17 financing documents: six mortgages (one at $0, 1980), two satisfactions (1982, 2001) and none for the 2002, 2005 or 2015 mortgages; three assignments, two assignments of leases and rents, three agreements and a sundry agreement. |
| Anchor A | 11 financing documents: an $8,750,000 mortgage and an assignment of leases and rents recorded 2021-03-22, a termination of assignment of leases and rents 2023-06-15 and a sundry agreement 2023-06-16; no satisfaction follows the 2021 mortgage. |

# Term trace: Q14

| Concept ID | Preferred label | Lives as | Sub-questions | Source |
| --- | --- | --- | --- | --- |
| `supporting-deed` | supporting deed | answer contract (latest deed on or before the date, ties all returned) | Q14.1, Q14.3 | `acris_master` |
| `date-basis` | date basis | answer contract input (`document` or `recorded`) | Q14.1, Q14.3 | `acris_master` |
| `registration-in-force` | registration in force | answer contract status (registered-later, ended, undated, end-unknown, in-force) | Q14.2, Q14.3 | `hpd_registrations` |
| `title-registration-relation` | title and registration relation | answer contract (coincide, differ, not-comparable, no-title-record, no-registration-in-force) | Q14.3 | `acris_parties`, `hpd_contacts` |

Reused: `deed`, `grantee`, `registration`, `contact`, `corporate-owner`, `document-date`, `recorded-date`, `last-registered-date`, `registration-end-date`.

Tagged not in the graph: the violation and its inspection, notice and issue dates (user choice 2026-11-17: 1,970,575 rows; the agent reads them from a tool), the violation status, the supporting-deed flags, the registration status, the relation.

## Q14 pilot restatement

| Question | Restated with approved terms |
| --- | --- |
| Q14 | For a lot and a date taken from a violation, list the **supporting deeds** (**document date**, **recorded date**, **grantee**) under a named **date basis**, the **registrations in force** with their **corporate owner** or individual owner contacts, and their **title and registration relation**; state that a registration filed later is not in force, that the record is today's version of the past, and that a name match is a lead. |
| Anchor A | 2022-10-20: the 2021 deed supports the title holder, no registration in force (filed 2025-09-30). 2026-01-15: the 2025 grantee equals the registered corporate owner. |


## Q15 trace

| Concept ID | Preferred label | Lives as | Sub-questions | Source |
| --- | --- | --- | --- | --- |
| `violation` | violation | `Violation` node | Q15.1, Q15.2 | `hpd_violations` |
| `violation-id` | violation id | `Violation.violationId` | Q15.1 | `hpd_violations` |
| `has-violation` | has violation | `HAS_VIOLATION` relationship | Q15.1 | `hpd_violations` |
| `violation-class` | violation class | `Violation.violationClass` | Q15.1 | `hpd_violations` |
| `violation-status` | violation status | `Violation.status` | Q15.1, Q15.2 | `hpd_violations` |
| `inspection-date` | inspection date | `Violation.inspectionDate` | Q15.1 | `hpd_violations` |
| `open-violation-rate` | open violation rate | answer contract (computed) | Q15.2 | `hpd_violations`, `pluto` |
| `order-number` | order number | `Violation.orderNumber` (extension 2026-11-21) | Q15.3 | `hpd_violations` |
| `pest-violation` | pest violation | answer contract (computed from `orderNumber` and `data/hpd_pest_orders.yaml`) | Q15.3 | `hpd_violations` |

## Q15 pilot restatement

| Question | Restated with approved terms |
| --- | --- |
| Q15 | For a building, give the open **violations** by **violation class** with the snapshot date and the oldest open **inspection date**, and the **open violation rate** with its numerator, the lot's **residential units** and their source; state that a violation is an inspector's citation and that a lot with no unit count gives rate unavailable. |
| Anchor C | 4 open (B 2, C 2), oldest open 2023-03-25, 32 units, 0.125 per unit. |
| Q15.3 | For a building, give its **pest violations** by kind (from the **order number**) and status, with the oldest open **inspection date** and the order codes behind each kind; state that a pest violation is an inspector's citation, that only codes 569 and 869 say mice, and that 566 and 866 are unspecified vermin. |
| Anchor C (Q15.3) | One open roach violation (order 568), oldest open 2023-03-25, no mice. |


# Term trace: Q16

| Concept ID | Preferred label | Lives as | Sub-questions | Source |
| --- | --- | --- | --- | --- |
| `retrieved-item` | retrieved item | answer contract (session evidence) | Q16.1 to Q16.4 | `web_research` |
| `reported-claim` | reported claim | answer contract field | Q16.1 | `web_research` |
| `extraction-method` | extraction method | answer contract field | Q16.2 | `web_research` |
| `source-category` | source category | answer contract field (4 values) | Q16.1, Q16.2 | `web_research` |
| `review-status` | review status | answer contract field (5 values) | Q16.4 | `web_research` |
| `fact-relation` | relation to recorded facts | answer contract field (4 values, computed) | Q16.3 | `web_research`, recorded facts |
| `match-basis` | match basis | answer contract field (2 values) | Q16.3 | `web_research` |

Reused: `affiliation` and `reported` (Q11). New value concepts: `public-record`, `published-reporting`, `web-content`, `project-derived`; `item-unreviewed` (not `unreviewed`, which is the Q6 list-entry status), `confirmed`, `refuted`, `inconclusive`, `contested`; `agrees`, `adds`, `conflicts`, `unrelated`; `exact-match`, `lead-only`.

Stage 4 (2026-11-18): related links and hidden labels only; no concept added or renamed, `item-unreviewed` lost its shared hidden label `unreviewed`.

Tagged not in the graph: every Q16 term (web and document findings are session evidence); publisher, date, URL, page and quoted text (answer fields); the as-of date and budget (inputs); the retrieval log.

## Q16 pilot restatement

| Question | Restated with approved terms |
| --- | --- |
| Q16 | For an entity name or address, list each **retrieved item** with its publisher or filing body, date, locator, **reported claim** or extracted value and **extraction method**, its **source category**, **review status**, **relation to recorded facts** and **match basis**; state that a claim is published, not a fact, and that a name match is a lead. |
| Neutral buildings | May return none: "no reports or documents found in the sources searched", with queries and dates. |

# Term trace: Q17

| Concept ID | Preferred label | Lives as | Sub-questions | Source |
| --- | --- | --- | --- | --- |
| `missing-registration` | missing registration | answer contract (holds, does-not-hold; per lot) | Q17.1 | `hpd_registrations` |
| `no-usable-registration` | no usable registration | answer contract flag (rows but a placeholder id or BIN) | Q17.1 | `hpd_registrations` |
| `lapsed-registration` | lapsed registration | answer contract (holds, does-not-hold, cannot-tell; by end date) | Q17.2 | `hpd_registrations` |
| `registration-older-than-deed` | registration older than the latest deed | answer contract (holds, does-not-hold, cannot-tell) | Q17.3 | `hpd_registrations`, `acris_master` |
| `unit-threshold` | unit threshold | answer contract (meets-threshold, below-threshold, units-not-recorded; threshold 3) | Q17.4 | `pluto` |

Reused: `hpd-registered`, `registration`, `registration-end-date`, `last-registered-date`, `registration-in-force`, `deed`, `recorded-date`, `not-a-sale`, `residential-units`, `year-built`, `pluto-building-count`. Condition results are plain enums (like Q14), not concepts.

Tagged not in the graph: every Q17 condition (computed at answer time from existing nodes), the as-of date and snapshot dates (input and contract, from `data/sources.yaml`), the threshold value 3 (input).

## Q17 pilot restatement

| Question | Restated with approved terms |
| --- | --- |
| Q17 | For a lot, report whether its **registration is missing**, **lapsed** and **older than the latest deed**, each with its dates, and whether PLUTO's **residential units** meet the **unit threshold** of 3; state the snapshot date of each source, that absence from the dataset is not a ruling, and that nothing is decided about legal applicability. |
| Anchor E | Not missing; lapsed (period ended 2021-09-01); older than the deed recorded 2026-04-21; 6 units meet the threshold. |
| Anchor F | Missing; lapsed and older-than-deed cannot-tell; 40 units meet the threshold; built 2025; the data does not say why it is unregistered. |
| Anchor A | Not missing; not lapsed (period ends 2026-09-01 on the 2026-05-29 snapshot); not older than the 2025 deed. |


# Term trace: Q18

| Concept ID | Preferred label | Lives as | Sub-questions | Source |
| --- | --- | --- | --- | --- |
| `deed-classification` | deed classification | answer contract (correction, zero-transfer, priced) | Q18.1 | `acris_master` |
| `zero-transfer` | zero-transfer deed | answer contract (the class that gets signals) | Q18.1, Q18.2 | `acris_master` |
| `restructuring-signal` | restructuring signal | answer contract (four boolean leads and a count) | Q18.2 | `acris_master`, `acris_parties`, `pluto`, `hpd_contacts` |

Reused: `deed`, `grantor`, `grantee`, `recorded-date`, `document-date`, `document-amount`, `not-a-sale`, `attributable-transfer`, `owner-portfolio`, `in-portfolio`, `comparison-rule`.

Tagged not in the graph: classification, the four signals, the signal count and the uncertainty list (computed at answer time from existing `Deed`, `Grantor`, `Grantee`, `Lot` and `Contact` nodes); "restructuring" as a verdict (not needed: only the hint and its support are reported).


# Term trace: Q19

| Concept ID | Preferred label | Lives as | Sub-questions | Source |
| --- | --- | --- | --- | --- |
| `pair-layer-state` | pair state in a layer | answer contract (same, different, ungrouped with reasons) | Q19.1 | `bor_layers` |
| `representative-path` | representative path | answer contract (fewest links, stage and evidence per link) | Q19.2 | `bor_layers` |
| `pre-subdivision-connectivity` | connectivity before subdivision | answer contract (boolean and the cut-crossing links) | Q19.3 | `bor_layers` |
| `stage-precision` | stage precision | answer contract (per stage, or not evaluated) | Q19.4 | `bor_layers` (`method_metrics`) |

Reused: `operational-network`, `owner-portfolio`, `landlord`, `lot`, `whole-component`, `louvain-community`, `network-absence-reasons` (shared absence scheme), `connected-by-identity`, `connected-by-deed`, `connected-by-name`, `connected-by-address`, `network-weight`.

Tagged not in the graph: everything above (computed at answer time from `IN_NETWORK`, `IN_PORTFOLIO`, absence properties, `COVERS` and the `CONNECTED_BY_*` links); evidence behind an edge (the release's evidence items, on request via the evidence id); the supporting registrations, contacts and deeds (Q2 to Q4, Q11, Q12 sources).

## Q19 pilot restatement

| Question | Restated with approved terms |
| --- | --- |
| Q19 | For two lots and each layer in the selected run, report the **pair state** (same, different or ungrouped, with reason codes); for the same group, a **representative path** with stage and evidence per link; for networks, **connectivity before subdivision** apart from membership; and **stage precision** as a method property. State the run, that a non-link is no finding about owners, and that a path is a record link. |
| Anchors A and B | Ungrouped in both layers (no linkage). No path, no finding. |
| 438 52 Street and 1704 East 15 Street | Same portfolio and network, one link (an identity cluster). |

Q19 stage 4 (2026-11-19): 5 related pairs (adds `louvain-community` and `ownership-signal` to the pre-subdivision and precision concepts); no new concept.


# Term trace: Q20

| Concept ID | Preferred label | Lives as | Sub-questions | Source |
| --- | --- | --- | --- | --- |
| `dossier` | dossier | answer contract (assembled at answer time) | Q20.1 to Q20.4 | component answers |
| `lead` | lead | computed at answer time (lead rule) | Q20.3 | recorded and retrieved names and addresses |
| `stop-reason` | stop reason | answer contract field (5 values) | Q20.3 | the trail |

Reused: `network-group-id`, `portfolio-group-id` (Q20.2); `affiliation` evidence statuses `documented`, `hypothesized`, `reported`; `source-category`, `review-status` and their schemes (Q16). New value concepts in the `stop-reasons` scheme: `reached-service-address`, `no-further-link`, `needs-payment`, `budget-reached`, `unresolved-conflict`.

Tagged not in the graph: every Q20 term (the dossier is assembled at answer time); the section list, claim fields, retrieval log and run (answer contract).

## Q20 pilot restatement

| Question | Restated with approved terms |
| --- | --- |
| Q20 | For an address, return the **dossier**: the input and resolution, recorded facts, the **Operational Network** and **Owner Portfolio** apart, transactions and conditions, retrieved items labeled **documented**, **hypothesized** or **reported**, conflicts and gaps, and the run; list each **lead** followed or logged, and give exactly one **stop reason**. |
| Anchor A | Recorded trail ends at the entity's own process address (`reached-service-address`); the shared HPD business address stays a lead for the mail-drop check. |


# Term trace: Q21

| Concept ID | Preferred label | Lives as | Sub-questions | Source |
| --- | --- | --- | --- | --- |
| `lot-violation-ranking` | lot violation ranking | answer contract (per lot: counts by class, units, rate, rank) | Q21.1, Q21.3 | `hpd_violations`, `pluto`, `bor_layers` |
| `violation-concentration` | violation concentration | answer contract (top-3 share, member and affected lot counts) | Q21.2 | `hpd_violations`, `bor_layers` |
| `agent` | managing agent | reused (existing, Q4): contact type Agent on `Contact`, found through `nameKey` | Q23.1 | `hpd_contacts` |
| `agent-footprint` | agent footprint | answer contract (registrations, buildings, lots by spelling; layer counts; address masks) | Q23.1 to Q23.3 | `hpd_contacts`, `hpd_registrations`, `bor_layers` |
| `name-search` | name search | answer contract (matches by source and role, person leads with counts, near names, outcome); reuses `corporation-name`, `person-name`, `contact-type`, `grantee-name`, `grantor-name`, `dos-entity-name` | Q24.1 to Q24.4 | `hpd_contacts`, `hpd_registrations`, `acris_parties`, `nys_corporations` |
| `legal-suffix-only` | legal suffix only | answer contract (near-name lead kind) | Q24.3 | `hpd_contacts`, `acris_parties` |

Reused: `violation`, `violation-class`, `violation-status`, `open-violation-rate`, `residential-units`, `operational-network`, `owner-portfolio`, `in-network`, `in-portfolio`, `has-building`, `has-violation`, `tax-lot`, `building`. Not needed: "hazardous" (classes are reported apart).

| Question | Restated with approved terms |
| --- | --- |
| Q21 | For a chosen layer, give the **lot violation ranking** of its member lots (open violations by class and **open violation rate**, with the unit count), the **violation concentration**, and the same for the other layer with the lots that appear in only one. |

Q22 (stage 1, 2026-11-19). New terms: **abbreviation match**, **differs by numeral or word** (scheme `entity-name-outcomes`, which also reuses exact normalized, normalization match, different, not comparable). Rules S1, L1, AB1 live in `compare.entity_name_comparison` and decision 2026-11-19. Not needed: "joining record" (computed from lot, registration, document, DOS id).

| Question | Restated with approved terms |
| --- | --- |
| Q22 | For two recorded names, give the **entity name outcome** (exact normalized, normalization match with its rule, abbreviation match, differs by numeral or word, different) and the records that join them other than the name; a name match is a lead. |

# Term trace: Q25

| Concept ID | Preferred label | Lives as | Sub-questions | Source |
| --- | --- | --- | --- | --- |
| `registry-search` | registry search | answer contract (session evidence) | Q25.1 to Q25.4 | `web_research` |
| `registry-outcome` | registry outcome | answer contract field (4 values) | Q25.2 | `web_research` |

Reused: `jurisdiction` (Q5), `retrieved-item` and `match-basis` with `exact-match`, `lead-only` (Q16), `needs-payment` (Q20). New value concepts in the `registry-outcomes` scheme: `registry-record-found`, `registry-status-only`, `registry-no-record`, `registry-unreachable`.

Tagged not in the graph: every Q25 term (session evidence); registry name, query, retrieval date, filing id, status, filing date and agent (answer fields).

## Q25 pilot restatement

| Question | Restated with approved terms |
| --- | --- |
| Q25 | For an entity whose **jurisdiction** is recorded outside New York, give each **registry search** with registry, query, date and **registry outcome** (filing id, status, agent where public); report a step that **needs payment** as an unresolved lead; state that a name match is a **lead only** unless another record connects it. |


# Term trace: Q26

| Concept ID | Preferred label | Lives as | Sub-questions | Source |
| --- | --- | --- | --- | --- |
| `source-absence` | source absence | answer contract (per source: snapshot date, reason, outcome `not-loaded`, recall note) | Q26.1 to Q26.4 | `hpd_registrations`, `nys_corporations`, `bor_layers`, `hpd_violations` |

Reused: the five reasons in `network-absence-reasons` (`no-qualifying-linkage`, `excluded-by-policy`, `below-eligibility-rule`, `outside-source-coverage`, `outside-method-input`), `network-absence`, `portfolio-absence`, `hpd-registered`, `dos-entity`, `violation`, `in-network`, `in-portfolio`, `contact`. Not needed: "exempt" and "unregistered" (the data does not say which), "recall" (a fixed statement in the answer).

| Question | Restated with approved terms |
| --- | --- |
| Q26 | For a lot, give each **source absence**: the source and snapshot date, one of the five reasons (or `not-loaded` for violations of an unregistered lot), and the statement that recall is unmeasured for the **Operational Network** and **Owner Portfolio**. |


## Q27 trace

| Concept ID | Preferred label | Lives as | Sub-questions | Source |
| --- | --- | --- | --- | --- |
| `complaint-problem` | complaint problem | `Problem` node | Q27.1, Q27.2 | `hpd_complaints` |
| `problem-id` | problem id | `Problem.problemId` | Q27.1 | `hpd_complaints` |
| `complaint-id` | complaint id | `Problem.complaintId` | Q27.1 | `hpd_complaints` |
| `has-problem` | has problem | `HAS_PROBLEM` relationship | Q27.1 | `hpd_complaints` |
| `problem-type` | problem type | `Problem.problemType` | Q27.1 | `hpd_complaints` |
| `major-category` | major category | `Problem.majorCategory` | Q27.1 | `hpd_complaints` |
| `problem-status` | problem status | `Problem.status` | Q27.1 | `hpd_complaints` |
| `received-date` | received date | `Problem.receivedDate` | Q27.1, Q27.2 | `hpd_complaints` |
| `duplicate-flag` | duplicate flag | `Problem.duplicate` | Q27.1 | `hpd_complaints` |
| `complaint-rate` | complaint rate | answer contract (computed) | Q27.2 | `hpd_complaints`, `pluto` |
| `minor-category` | minor category | `Problem.minorCategory` (extension 2026-11-21) | Q27.3 | `hpd_complaints` |
| `problem-code` | problem code | `Problem.problemCode` (extension 2026-11-21) | Q27.3 | `hpd_complaints` |
| `pest-complaint` | pest complaint | answer contract (computed from `minorCategory` PESTS and `problemCode`) | Q27.3 | `hpd_complaints` |

Reused: `residential-units`, `violation` (related), `open-violation-rate` (related).

Tagged not in the graph: apartment, unit type, space type, anonymity flag, coordinates, the complaint's own status and status date, problems before 2021-01-01. (Minor category and problem code entered the graph in the 2026-11-21 extension, Q27.3.)

## Q27 pilot restatement

| Question | Restated with approved terms |
| --- | --- |
| Q27 | For a building and a period, give the **complaint problems** by **problem type**, **major category** and **problem status** (counting unit: problem records, with **duplicate flag** reported apart and distinct **complaint ids**), the open count at the snapshot date, and the **complaint rate** with its numerator, the lot's **residential units** and their source; state that a problem is what was reported, not what was found, and that a lot with no unit count gives rate unavailable. |
| Anchor C | 2023 to 2025: 27 problems (12 emergency, 2 immediate emergency, 13 non-emergency, 1 flagged duplicate), none open, 32 units, 0.84375 per unit. |
| Q27.3 | For a building and a period, give the **pest complaints** (**minor category** PESTS) by pest (the **problem code**) and **problem status**, with the open count at the snapshot date and the **duplicate flag** reported apart; state that a pest complaint is what a tenant reported, that the count is per building, that OTHER never means mice, and that a pest violation is counted apart. |
| Anchor C (Q27.3) | 2021 onward: 7 closed pest problems (mice 1, roaches 3, other 2, flies 1), none open. |


## Q28 trace

| Concept ID | Preferred label | Lives as | Sub-questions | Source |
| --- | --- | --- | --- | --- |
| `litigation-case` | litigation case | `Litigation` node | Q28.1, Q28.2 | `hpd_litigations` |
| `litigation-id` | litigation id | `Litigation.litigationId` | Q28.1 | `hpd_litigations` |
| `has-litigation-case` | has litigation case | `HAS_LITIGATION` relationship | Q28.1 | `hpd_litigations` |
| `case-type` | case type | `Litigation.caseType` | Q28.1 | `hpd_litigations` |
| `case-open-date` | case open date | `Litigation.caseOpenDate` | Q28.1 | `hpd_litigations` |
| `case-status` | case status | `Litigation.caseStatus` | Q28.1 | `hpd_litigations` |
| `open-judgement` | open judgement | `Litigation.openJudgement` | Q28.1 | `hpd_litigations` |
| `harassment-finding` | harassment finding | `Litigation.harassmentFinding` | Q28.1 | `hpd_litigations` |
| `finding-date` | finding date | `Litigation.findingDate` | Q28.1 | `hpd_litigations` |
| `case-penalty` | case penalty | `Litigation.penalty` | Q28.1 | `hpd_litigations` |
| `respondent` | respondent | `Litigation.respondent` (and derived `respondentKeys`, N3 keys of its parts) | Q28.1, Q28.2 | `hpd_litigations` |
| `respondent-owner-match` | respondent owner match | answer contract (computed) | Q28.2 | `hpd_litigations`, `hpd_contacts` |

Reused: `building`, `registration`, `contact`, `corporate-owner`, `name-agreement`, `comparison-rule`.

Tagged not in the graph: the case address, coordinates and districts (the building carries them), the deed grantee comparison (Q3), the respondent's role, the judgement amount (not in the source).

## Q28 pilot restatement

| Question | Restated with approved terms |
| --- | --- |
| Q28 | For a building, list its **litigation cases** with **case type**, **case open date**, **case status**, **open judgement**, **harassment finding** with its **finding date**, **case penalty** and **respondent**, and for each case the **respondent owner match** against the registered owner contacts; state that a case is an action brought and not a finding of fault, that only After Inquest or After Trial is a harassment finding, and that a name match is a lead. |
| Anchor C | One closed Tenant Action opened 2023-05-15, no finding; the respondent's entity name differs from the HPD owner name under N3 (STREET vs ST): not matched. |
