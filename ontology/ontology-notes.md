# Ontology notes

Stage 5 record for `ontology/watchline-onto.ttl`. Prefixes: `vocab:` is `https://watchline.example/vocab/` (concepts), `onto:` is `https://watchline.example/onto/` (ontology elements), `id:` is `https://watchline.example/id/` (instances). Procedure: [stage5-procedure.md](../specs/stage5-procedure.md); policy: [SKOS-to-ontology mapping](../specs/roadmap.md#skos-to-ontology-mapping).

`scripts/check_ontology.py` (`make ontology`) reads the **Axioms** table, the **Answer-shape pilot** table, the tool versions and the **OOPS! result** section below. Keep their formats.

## Setup decisions (first question, 2026-11-11)

- **Layout:** `ontology/watchline-onto.ttl` (TBox and CBox), `ontology/abox/qNN.ttl` (example data), `ontology/abox/negative/` (cases that must be rejected), `ontology/concept-mapping.csv`, this file, `ontology/report-profile.txt` (ROBOT report severities). Turtle is committed.
- **Naming:** classes UpperCamelCase, properties lowerCamelCase, stable once minted. Every element has `rdfs:label` (the approved preferred label), an `rdfs:comment` definition and one or more `onto:traceQuestion` values.
- **External terms:** PROV-O terms (`prov:Entity`, `prov:Activity`) are declared locally, without `owl:imports`. Only the terms used are declared.
- **Versioning:** ontology IRI `https://watchline.example/onto`, no version IRI (POC rules).
- **Instance data:** ROBOT reads each file alone, so assertions in an example file would be read as annotations. The check script merges the TBox and an example file into one graph first. Anyone running ROBOT by hand must do the same.

## Toolchain

| Tool | Version | Note |
| --- | --- | --- |
| Java | OpenJDK 26.0.1 | Homebrew |
| ROBOT | ROBOT version 1.9.11 | `tools/robot.jar` plus the wrapper `tools/robot` (git-ignored; download `robot.jar` from the ontodev/robot v1.9.11 release) |
| reasoner: HermiT 1.4.5.456 | bundled in the ROBOT jar | **Pinned reasoner.** ELK 0.6.0 (also bundled) was tried first and rejected: it silently ignores data-property domains, so negative case n01 (a lot-wide value on a building) passes unflagged. HermiT flags all five negative cases. |
| rdflib | 7.6.0 | check script |
| OOPS! | web service | Run by the user on the TBox only; see below |

## Element kinds

Decisions for each thing the question talks about. The mapping table is `concept-mapping.csv`.

| Thing | Kind | Reason |
| --- | --- | --- |
| tax lot, building, street address, address candidate, HPD registration, source snapshot, source record | class | Independent things the answer lists and counts. |
| address resolution | class (under `prov:Activity`) | One act of mapping an input to a lot, with its own outcome, codes and time. |
| address resolution outcome | class (closed enumeration) with four individuals | Q1.3 needs exactly four values. The values keep their concept IRIs (explicit exception, see mapping). |
| matched exactly, matched by variant, ambiguous, not found | controlled value (concept IRI kept) | Roadmap: a concept may be used directly as a controlled value. |
| BBL, BIN | datatype property (`hasBbl`, `hasBin`) | An identifier is a string attribute of its subject, not a class. Stored as strings, never numbers. |
| addressed building | object property `hasAddressedBuilding` | A role within one resolution; not a subclass of Building (Stage 3 decision). |
| alternate address | object property `usedAlternateAddress` | A street address in a role within one resolution, as for the addressed building. Not a subclass of `StreetAddress`, although the vocabulary lists it under `street-address`: the is-a test holds for the concept but a subclass would give a street address a permanent "alternate" status that it has only relative to one resolution. |
| inferred resolution | defined class | A resolution is inferred exactly when it used an alternate address. |
| four source-reported characteristics | datatype properties of the tax lot | Accepted physical contract: scalar values on the lot (physical-implementation section 3). The concept `source-reported-characteristic` has no class; reifying each value as a statement object is deferred until a question needs independent history of a value. |
| parcel, building and unit counts | classes under `ReportedCount`, pairwise disjoint | Taxonomy candidate confirmed: the counting unit differs and counts are never converted. |
| Geosupport return code, reason code | datatype properties of the resolution | Q1 stores codes as strings; code values are not concepts. |
| source key, record locator, snapshot id, snapshot date | datatype properties | Evidence fields from `profiles/evidence.yaml` that have vocabulary concepts. |
| run id, mapping git revision, source category, assertion type, review status | datatype properties, no concept | Evidence fields from `profiles/evidence.yaml` with no vocabulary concept yet (mapping rows start the note with "no concept:"). Add concepts when a question first needs to discuss them. |
| resolution rule (comparing returned to input address), name normalization | not modeled | Query-time computation; the rules are undefined (open point). |
| presentation of the answer (order, wording) | not modeled | Presentation choice. |
| geosupport message text | not modeled | Specs forbid classification by message text. |
| bbl and bin uniqueness, string patterns | not modeled in OWL | Listed under Rules for Stage 6 shapes. |

## Axioms

Every `rdfs:subClassOf`, `owl:equivalentClass`, disjointness, domain, class-valued range and property chain has a row. A cell may name several elements. Kind is one of `subclass`, `restriction`, `equivalent`, `disjoint`, `domain`, `range`, `chain`. No SKOS link was promoted automatically.

| Element | Kind | Axiom | Reason |
| --- | --- | --- | --- |
| `AddressResolution` | subclass | `prov:Activity` | A resolution is an act performed once, at a time, with inputs and a result. |
| `SourceSnapshot`, `SourceRecord` | subclass | `prov:Entity` | Each is a digital thing used as evidence. The vocabulary mapping is a `skos:broadMatch` to `prov:Entity`; the is-a test holds. |
| `ParcelCount`, `BuildingCount`, `UnitCount` | subclass | `ReportedCount` | Each is a reported count with a fixed counting unit (taxonomy links, is-a test passed in Stage 3). |
| `ParcelCount`, `BuildingCount`, `UnitCount` | restriction | `countingUnit value "tax lot" / "building" / "residential unit"` | The unit is part of the meaning of each kind; the answer must name it. |
| `AddressResolutionOutcome` | equivalent | `{matched exactly, matched by variant, ambiguous, not found}` | Q1.3 allows exactly these four values. A closed enumeration also lets the reasoner reject a fifth. |
| `InferredResolution` | equivalent | `AddressResolution and usedAlternateAddress some StreetAddress` | The vocabulary defines an inferred resolution as one reached through an alternate address; making it a defined class means the label cannot be omitted for such a resolution. |
| `TaxLot`, `Building` | disjoint | `TaxLot` and `Building` are disjoint | A lot is not necessarily one building and the specs never let one stand for the other (taxonomy candidate confirmed). Makes a lot-wide value on a building inconsistent. |
| `ParcelCount`, `BuildingCount`, `UnitCount` | disjoint | pairwise | Counts of different units are never converted into one another (taxonomy candidate confirmed). |
| `hasOutcome` | disjoint | `hasOutcome value ambiguous` and `resolvedToTaxLot some TaxLot` | An ambiguous resolution never silently selects a lot (Q1 answer requirement 5). |
| `resolvedToTaxLot` | disjoint | `hasOutcome value not found` and `resolvedToTaxLot some TaxLot` | A not-found resolution never guesses a nearby lot (Q1 scenario). |
| `hasBbl` | domain | `TaxLot` | Only tax lots have BBLs. |
| `registersBuilding`, `hasRecordedBuilding`, `hasAddressedBuilding` | range | `Building` | The thing on the other side of these is always a building. |
| `hasBin` | domain | `Building` | Only buildings have BINs. |
| `addressText` | domain | `StreetAddress` | Text of an address, never of anything else. |
| `candidateText` | domain | `AddressCandidate` | Text of a candidate only. |
| `hasInputAddress`, `returnedAddress`, `usedAlternateAddress`, `hasOutcome`, `hasAddressCandidate`, `hasAddressedBuilding`, `resolvedToTaxLot`, `geosupportReturnCode`, `geosupportReasonCode` | domain | `AddressResolution` | Each relates something to one resolution; no other class uses it. |
| `hasInputAddress`, `returnedAddress`, `usedAlternateAddress`, `hasRecordedAddress` | range | `StreetAddress` | Each points to an address. |
| `resolvedToTaxLot`, `registeredOnTaxLot`, `countedForTaxLot` | range | `TaxLot` | Each points to a tax lot. |
| `hasOutcome` | range | `AddressResolutionOutcome` | Outcomes are the enumerated values. |
| `hasAddressCandidate` | range | `AddressCandidate` | Candidates are not matches; kept as their own class. |
| `registersBuilding`, `registeredOnTaxLot` | domain | `HpdRegistration` | A registration associates an address, a lot and a building; nothing else here does. |
| `hasRecordedBuilding` | domain | `TaxLot` | A lot has recorded buildings. |
| `hasRecordedBuilding` | chain | `inverse(registeredOnTaxLot) o registersBuilding` | The buildings recorded for a lot are exactly those HPD registrations name for it. The chain gives Q1.2 without a separate assertion; the relation stays open-world (see Rules for Stage 6 shapes). |
| `reportedYearBuilt`, `reportedBuildingClass`, `reportedResidentialUnits`, `reportedAssessedValue` | domain | `TaxLot` | The four values are lot-wide and must not be attached to a building. With the disjointness above, doing so is inconsistent. |
| `countValue`, `countingUnit`, `countedForTaxLot`, `countedFromRecord` | domain | `ReportedCount` | Only tallies have a value, a unit, a described lot and a basis record. |
| `countedFromRecord`, `hasSourceRecord` | range | `SourceRecord` | The basis of a count or value is a source record. |
| `inSnapshot` | domain | `SourceRecord` | A record is a row of a snapshot. |
| `inSnapshot` | range | `SourceSnapshot` | The whole of which a record is a row. |
| `sourceKey`, `sourceRecordLocator` | domain | `SourceRecord` | Properties of a record. |
| `snapshotId`, `snapshotDate` | domain | `SourceSnapshot` | Properties of a snapshot. |

Deliberately absent: domains on `hasRecordedAddress`, `hasSourceRecord`, `runId`, `mappingGitRevision`, `sourceCategory`, `assertionType`, `reviewStatus` (used by several classes, a domain would force inferences); functional-property axioms (HermiT and shapes treat these differently, see Rules for Stage 6 shapes); any subclass between `TaxLot`, `Building`, `HpdRegistration`, `StreetAddress`, `AddressCandidate`.

## Rules for Stage 6 shapes

OWL cannot state these. Do not force them into axioms.

1. **Identifiers.** Exactly one `hasBbl` per `TaxLot`, matching `^[1-5][0-9]{9}$`, unique across lots; at most one `hasBin` per `Building`, matching `^[1-5][0-9]{6}$`, unique across buildings. Placeholder BINs are excluded and reported as registrations with no recorded BIN.
2. **Resolution shape.** Exactly one `hasInputAddress` and exactly one `hasOutcome` per `AddressResolution`. Outcome *matched exactly* or *matched by variant* requires exactly one `resolvedToTaxLot`. *Ambiguous* requires at least two `hasAddressCandidate`. *Not found* requires none and the return code, reason code and variants tried. *Matched by variant* requires `returnedAddress` and the reason code.
3. **Outcome is derived.** *Exact* versus *variant* comes from comparing the returned address to the input after case and whitespace normalization; the GRC alone does not decide it. The rule stays in the classifier, not the ontology. Never classify from message text.
4. **Inferred.** An `InferredResolution` must be labelled inferred in the answer and carry `assertionType` `type_ii`.
5. **Addressed building.** `hasAddressedBuilding` must be a building in the lot's `hasRecordedBuilding` set. The relation is `type_ii` (a derived match after name normalization); a plain object property cannot carry that, so Stage 6 puts the assertion type on the graph edge or a relationship node. Pending until name normalization is defined.
6. **Open world.** `hasRecordedBuilding` is complete only for registered buildings. A lot with no registration is reported as "no building recorded in the HPD registrations", not "no buildings". A building count from HPD registrations equals the number of distinct valid BINs.
7. **Counts.** Each `ReportedCount` has exactly one `countValue`, one `countingUnit` equal to its class's unit, one `countedForTaxLot`, and at least one `countedFromRecord`. A building count from PLUTO and one from HPD are different counts: each names its own records and neither replaces the other. A `UnitCount` equals the lot's `reportedResidentialUnits` and is never multiplied by, divided across, or summed over buildings.
8. **Characteristics.** At most one value of each reported characteristic per lot and source record. Missing or zero year built is absent. A residential unit count of zero is a real value. A blank building class is absent. Assessed value is whole dollars in the ontology; Stage 6 stores cents. Never guess an assessment period.
9. **Evidence.** Each sourced value is tied to a `SourceRecord` that is `inSnapshot` of one `SourceSnapshot`; which properties a record supports is named per field, not implied by the shared link. `snapshotDate` may be absent (PLUTO). `assertionType` is required on derived values; `type_ii` requires a `prov:wasDerivedFrom` link to its inputs; `sourceCategory` and `reviewStatus` follow `profiles/evidence.yaml`.
10. **No cross-snapshot merge.** Records of different snapshots or runs are not merged into one assertion.

## Answer-shape pilot

Each answer field in `profiles/q01-answer.yaml` against the elements that state it. Status values: **expressible**, **pending** (matches the profile), **derived** (computed when the answer is built, then stated with the listed elements), **not modeled**.

| Field | Profile status | Ontology elements | Status | Note |
| --- | --- | --- | --- | --- |
| `input_address` | pending | `hasInputAddress`, `StreetAddress`, `addressText` | expressible, pending | Geosupport input layout not yet recorded. |
| `resolution_outcome` | pending | `hasOutcome`, `AddressResolutionOutcome` | expressible, pending | Derived by the classifier (rule 3), stated as the outcome individual. |
| `geosupport_return_code` | pending | `geosupportReturnCode` | expressible, pending | No cached response. |
| `geosupport_reason_code` | pending | `geosupportReasonCode` | expressible, pending | No cached response. |
| `returned_address` | pending | `returnedAddress`, `addressText` | expressible, pending | Reported when the outcome is matched by variant. |
| `address_candidates` | pending | `hasAddressCandidate`, `candidateText` | expressible, pending | At least two when ambiguous (rule 2). |
| `alternate_address` | pending | `usedAlternateAddress` | expressible, pending | No worked example exists. |
| `inferred_resolution` | pending | `InferredResolution` | expressible, pending | The boolean is class membership, classified by the reasoner. |
| `bbl` | settled | `hasBbl` | expressible | Absent when the outcome gives no lot. |
| `tax_lot_address` | settled | `hasRecordedAddress`, `addressText` | expressible | One address per lot in PLUTO. |
| `buildings` | settled | `hasRecordedBuilding`, `hasBin`, `HpdRegistration` | expressible | Open-world rule 6. |
| `addressed_building` | pending | `hasAddressedBuilding` | expressible, pending | Type II link (rule 5); name normalization undefined. |
| `year_built` | settled | `reportedYearBuilt` | expressible | |
| `building_class` | settled | `reportedBuildingClass` | expressible | |
| `residential_units` | settled | `reportedResidentialUnits` | expressible | Lot-wide; domain is the lot only. |
| `assessed_value` | settled | `reportedAssessedValue` | expressible | Whole dollars here; cents at Stage 6. |
| `parcel_count` | settled | `ParcelCount`, `countValue`, `countingUnit` | derived | Counting unit enforced by class. |
| `building_count` | settled | `BuildingCount`, `countedFromRecord` | derived | HPD basis; counted from the distinct BINs. |
| `unit_count` | settled | `UnitCount`, `reportedResidentialUnits` | derived | Same value as the lot's units, a different kind of thing. |
| `pluto_building_count` | settled | `BuildingCount`, `countedFromRecord` | derived | A second `BuildingCount` whose basis is the PLUTO record; cross-check only. |
| `evidence` | settled | `SourceRecord`, `SourceSnapshot`, `inSnapshot`, `hasSourceRecord`, `sourceKey`, `sourceRecordLocator`, `snapshotId`, `snapshotDate`, `runId`, `mappingGitRevision`, `sourceCategory`, `assertionType`, `reviewStatus` | expressible | Per-field attribution is rule 9. |

## Reasoner and report results

Run 2026-11-11 with ROBOT 1.9.11 and HermiT 1.4.5.456.

- Example data (`abox/q01.ttl` plus TBox): consistent, no unsatisfiable class.
- Expected inferences confirmed: the synthetic alternate-address resolution is classified `InferredResolution`; the synthetic ambiguous one is not; `hasRecordedBuilding` gives 3 buildings for lot 3008210012 and 1 for lot 3008260002.
- Negative cases (all five flagged inconsistent): n01 lot-wide value on a building, n02 lot is a building, n03 ambiguous with a chosen lot, n04 not found with a lot, n05 count of two units.
- `robot report` (profile `report-profile.txt`): 0 errors. Two rules are set to INFO and explained below.

### Kept report findings

| Finding | Reason kept |
| --- | --- |
| `missing_definition` on every element | ROBOT looks for the OBO definition property (IAO:0000115). This ontology holds definitions in `rdfs:comment`, as the procedure requires. |
| `missing_ontology_license` | The license is the project owner's decision. Open point. |
| `missing_superclass` (INFO) | Top-level classes of different kinds on purpose; no is-a was found between them. |

## OOPS! result

Run 2026-11-11 through the OOPS! REST service (https://oops.linkeddata.es/rest) with the user's go-ahead. The TBox only was sent, converted to RDF/XML by ROBOT; no example data. The web form could not be used.

```
tbox-sha256: 55b616a66de2edf4770660a34499b12cf0ad5142de5762c24962cdf153584d9c
unresolved critical pitfalls: 0
```

Three pitfalls were reported (none Critical). All are kept:

| Pitfall | Importance | Affected | Reason kept |
| --- | --- | --- | --- |
| P04 unconnected elements | Minor | `prov:Activity`, `prov:Entity` | Local declarations of PROV-O terms; each is the superclass of an ontology class (`AddressResolution`; `SourceRecord`, `SourceSnapshot`). OOPS! does not see the subclass link because the declarations stand alone. |
| P11 missing domain or range | Important | `hasSourceRecord`, `hasRecordedAddress` (no domain); `runId`, `mappingGitRevision`, `sourceCategory`, `assertionType`, `reviewStatus` (no domain) | Deliberate (see Axioms, "Deliberately absent"): several classes use each, so a domain would infer wrong types. Their ranges are set. |
| P13 inverse relationships not declared | Minor | 14 object properties | Q1 never traverses these backwards, and an inverse per property would add terms no question traces. Add an inverse when a question needs the reverse direction. |
