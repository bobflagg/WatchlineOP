# PESP landlord accountability use case

## Purpose

The first use case for the knowledge graph: an AI agent that helps NYC tenants, tenant organizers, and housing researchers investigate a landlord following the [PESP, *How to Research Your Landlord*, May 2026](dependencies.md#pesp-landlord-research-guide) guide. The agent together with a human-in-the-loop will assemble a reproducible, source-cited dossier explaining the property, the parties named in public records, related properties, conditions and enforcement records, and any supported leads toward a wider ownership or corporate structure.

## Project boundary and acceptance

This document describes the end-to-end use case. WatchlineOP delivers the ontology pipeline, graph, mappings, and acceptance fixtures/contracts that support it. The AI research agent is a downstream consumer, responsible for executing retrieval/extraction and investigation workflows with human review.

Question files declare graph, retrieval/extraction, and/or investigation acceptance as defined in [the roadmap](roadmap.md#acceptance-types-and-responsibility). A graph release can be ready while downstream tests are pending. The full dossier scenario (Q20) is accepted only after its component tests and the downstream investigation test pass.

Graph answers and tests are relative to the frozen JustFix/WoW snapshot, not current live public records. The snapshot's coverage and freshness limits must remain visible. BOR releases and cached web/document/service evidence are separately versioned; see [the expected-answer policy](roadmap.md#expected-answer-policy).

## Users and investigation entry points

The primary user is a tenant or organizer who knows a building's street address and wants to understand whom the records name, what other properties may be connected, and what evidence can inform further research. Researchers and journalists can use the same evidence paths to inspect or challenge an answer.

The principal entry point is an address. Additional entry points include an official property identifier, an organization name, or a person named in a recorded business role. Ambiguous matches must return distinguishable candidates rather than silently select one.

## Research workflow

1. **Identify the property.** Resolve the address to a tax lot and its recorded buildings. Distinguish the addressed building from other buildings associated with the lot. Report match uncertainty and source-reported characteristics.
2. **Identify recorded parties.** Retrieve the registered owner, deed grantee, managing agent, and other disclosed roles. Compare records without collapsing distinct roles into one owner identity.
3. **Investigate the entity.** Inspect business registry records, business addresses, and filing attachments. Follow relevant entities into other jurisdictions when free public records are available.
4. **Explore related properties.** Retrieve separately derived Operational Networks and Owner Portfolios, their memberships, and the evidence and methods behind them. Compare those layers with the disclosed managing agent's footprint.
5. **Examine transactions and conditions.** Review transfers, financing documents, registrations, violations, building-level complaint summaries, and HPD litigation. Preserve the relevant dates and attribution limits.
6. **Follow qualified leads.** Search names and business addresses, retrieve documents, and inspect reported affiliations within an explicit research budget. Log findings, exclusions, conflicts, and dead ends.
7. **Produce a dossier.** Return the findings, evidence paths, unresolved leads, and an explicit reason for stopping. A reader should be able to retrace the investigation.

Web discovery can occur early or recur throughout the process. The workflow is iterative rather than a requirement to finish every database lookup before searching the web.

## Distinctions the model must preserve

| Concept | Meaning in this use case | Interpretation limit |
| --- | --- | --- |
| Tax lot | A jurisdiction's identified land parcel; the NYC preferred term is **Tax lot** | A lot is not necessarily one building |
| Building | A separately identified building associated with a lot | Building counts and parcel counts are different |
| Title / registration facts | Parties and roles stated in deeds, property registrations, or business filings | An HPD registrant, deed grantee, process contact, and managing agent are not interchangeable |
| Management relationship | A disclosed relationship between a building and its managing agent | Shared management does not establish shared ownership |
| Operational Network | A run-specific grouping connected through registration infrastructure and resolved identities, with aggregator-address masking | A derived investigative grouping, not a finding of common ownership |
| Owner Portfolio | A run-specific grouping attributed to one apparent owner using qualifying deed and resolved owner-identity signals | A derived attribution, not a legal determination of beneficial ownership |
| Aggregator / mail-drop address | An address used by many unrelated parties, or identified as a service address | Co-location alone must not support ownership or identity; method-specific masking and curated classifications remain distinct |
| Corporate affiliation | A supported or hypothesized ownership, parent, management, financing, or other relationship | Preserve the specific relationship and its evidentiary basis |

Identifiers: **BBL** is the NYC tax lot identifier and **BIN** is the NYC building identifier. Data sources and ingestion are described in `tech-stack.md`.

[BOR](dependencies.md#bor-beneficial-owner-resolution) supplies the two derived grouping layers. Operational Networks use connected components, with Louvain subdivision for oversized components under the method's recorded policy. Owner Portfolios use ownership signals rather than shared addresses. Eligibility rules, exclusions, component/community distinctions, and method versions belong to the release evidence.

A [BOR](dependencies.md#bor-beneficial-owner-resolution) display name or person anchor is a presentation choice, not an assertion that the named person owns the group. Group identifiers and memberships must be interpreted within their source snapshot and pipeline run.


## Evidence and answer requirements

### Assertion type and source quality

- **Type I — recorded assertion:** a source states the fact, or records join through an official identifier. This describes how the assertion was obtained, not a guarantee that it is correct.
- **Type II — derived conclusion or lead:** a method resolves, groups, classifies, or infers beyond what a source explicitly states.
- **Reported claim:** a publication states something about a subject. Its publication is recorded evidence; the claim's truth and applicability require separate assessment.

Track source category separately: `public_record`, `published_reporting`, `web_content`, or `project_derived`.

## Dossier and research stopping rules

A dossier should contain:

1. Input address or name, resolution outcome, and identified parcels/buildings.
2. Recorded title, registration, management, and business-filing facts.
3. Operational Network and Owner Portfolio results, separately explained.
4. Relevant transaction, financing, violation, complaint, and litigation summaries.
5. Retrieved claims, document extractions, and affiliation leads with their labels.
6. Conflicts, source gaps, excluded evidence, and unresolved leads.
7. Run and snapshot context, citations, retrieval log, and an explicit stop reason.

Follow new entity names and business addresses only when they come from recorded or retrieved evidence, are not masked service-address leads, and fit the stated step/time budget. Log retrieved items even if unused. Stop when the trail reaches a service or masked address, has no further recorded link, requires payment or an inaccessible source, exhausts the budget, or leaves an unresolved conflict. State the applicable stopping reason rather than imply the investigation is complete in an absolute sense.

Web and document findings are session/dossier evidence by default. Promoting them into the knowledge graph requires a separately governed process. Cached retrieval should support replay and evaluation.

