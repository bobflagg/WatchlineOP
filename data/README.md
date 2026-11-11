# POC source snapshot

The POC uses one fixed JustFix/Who Owns What PostgreSQL snapshot. Database-backed graph tests and expected answers must refer to this same snapshot. The table inventory and known coverage limits are in [sources.yaml](sources.yaml); the evaluation policy is in [the roadmap](../specs/roadmap.md#expected-answer-policy).

## Snapshot identity

Complete this short record from the actual dump and restore procedure before freezing acceptance fixtures. Unknown values are explicitly pending; the database name and table row counts alone do not identify a dump.

| Item | Value |
| --- | --- |
| Target database | `justfixwow` |
| Source dump filename and local/archive location | Pending identification |
| Dump origin / download reference | Pending identification |
| Dump SHA-256 | Pending calculation from the identified dump |
| Dump format | Pending inspection |
| PostgreSQL version used to restore | Pending recording |
| Restoration date | Unknown; record from evidence if available |
| Restore command and prerequisites | Pending recording from the actual procedure; omit credentials |
| Post-restore transformations, if any | Pending verification; record scripts and Git revision, or explicitly state none |

Compute the checksum with `shasum -a 256 /path/to/the-dump` once the file is identified. Record whether it identifies the compressed archive or uncompressed dump. A checksum of an archive should refer to the exact archived file used for restoration.

Do not guess whether restoration uses `pg_restore` or `psql`: record the command appropriate to the actual dump format, database setup, required extensions, and role/ownership options. Keep passwords and connection secrets in ignored environment files.

## POC handling

- Keep the source database fixed and access it read-only during extraction and testing. Rebuild only the POC Neo4j target when its model changes.
- Keep raw dumps/extracts and graph data outside Git. The project reserves `data/raw/`, `data/dumps/`, `data/snapshots/`, and `data/generated/` for ignored local data. Commit this README, the source inventory, and small curated test fixtures.
- Retain one identified baseline. Replacing the source dump is an explicit decision and requires rechecking affected expected answers.
- Record source-table coverage dates separately; they can differ within the database. A local query or restoration date is not a publisher's as-of date.
- Identify BOR releases and retrieval caches separately in the relevant fixture notes; they are not part of the JustFix/WoW dump unless explicitly documented.

This record is intentionally manual. No release service, migration framework, or dependency registry is required for the POC.
