# External references and data dependencies

Internal documentation uses repository-relative links. External materials are identified here by public URL and purpose, not by the author's local checkout path. A sibling repository or local PDF is not assumed to exist.

## PESP landlord research guide

- **Reference:** Private Equity Stakeholder Project and Tenant Union Federation, *How to Research Your Landlord*, May 2026 (date on the guide).
- **Publisher page:** [How to research your landlord](https://pestakeholder.org/news/how-to-research-your-landlord/).
- **Document:** [May 2026 guide PDF](https://pestakeholder.org/wp-content/uploads/2026/06/PESP_Landlord_ResearchGuide_2026.pdf).
- **Use:** Methodological background for the use case; not an ingestion source or an expected-answer oracle for NYC records.
- **Access:** Read the publisher-hosted document. If a local copy is retained for reproducible research, record its title/date, source URL, retrieval date, and checksum with the relevant evidence. Do not put a machine-specific path in the shared specification.

## BOR: beneficial owner resolution

- **Repository and overview:** [NYC Beneficial Owner Resolution](https://github.com/bobflagg/nyc-beneficial-owner-resolution).
- **Release interface:** [Release contract](https://github.com/bobflagg/nyc-beneficial-owner-resolution/blob/main/docs/release-contract.md) and [knowledge-graph mapping guidance](https://github.com/bobflagg/nyc-beneficial-owner-resolution/blob/main/docs/kg-mapping.md).
- **Use:** External producer of Operational Networks, Owner Portfolios, and their supporting evidence. WatchlineOP imports the chosen release; no sibling checkout or execution of BOR is implied.
- **Evidence identity:** Record the selected release/run, manifest, checksums, and source context in the fixture notes. Existing question examples name release v0.3.0 and run `2026-05-29-869bd299`; these remain provisional as stated in the question files. Links to `main` explain the current interface, not the frozen evidence used by a test.
- **Availability:** Obtain the selected release from its producer. The repository URL alone does not establish that the required release files are present locally. Missing files leave the affected fixtures pending.

The local JustFix/WoW database is documented in [data/README.md](../data/README.md) and [data/sources.yaml](../data/sources.yaml). Tool choices remain in [tech-stack.md](tech-stack.md). The [expected-answer policy](roadmap.md#expected-answer-policy) governs the evidence used for acceptance.
