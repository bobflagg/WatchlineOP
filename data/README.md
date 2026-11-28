# POC source snapshot

The POC uses one fixed JustFix/Who Owns What PostgreSQL snapshot. Database-backed graph tests and expected answers must refer to this same snapshot. The table inventory and known coverage limits are in [sources.yaml](sources.yaml); the evaluation policy is in [the roadmap](../specs/roadmap.md#expected-answer-policy).

## Snapshot identity

Complete this short record from the actual dump and restore procedure before freezing acceptance fixtures. Unknown values are explicitly pending; the database name and table row counts alone do not identify a dump.

**Current database (recorded 2026-11-28).** The source database is now `watchline`, a new version of the JustFix/WoW database with data through 2026-10-30. It replaces `justfixwow` as the source for loads, tests and expected answers (the baseline below is superseded and kept as history). Every database-backed fixture is re-derived against `watchline`.

| Item | Value |
| --- | --- |
| Database | `watchline` (PostgreSQL; connection in the git-ignored `.env`, `JUSTFIX_DATABASE_URL`). The Neo4j POC database has the same name; they are different systems |
| Data through | 2026-10-30 (the BOR manifest's `snapshot_date`, from the newest `real_property_master.recordedfiled` and `hpd_registrations.lastregistrationdate`) |
| Identified by | Row counts and content fingerprints of 9 tables, matching the pinned BOR release's `manifest.json` `source_tables` exactly (`scripts/check_bor_snapshot.py`, all tables match, user-run 2026-11-28): `hpd_contacts` 744,753; `hpd_registrations` 187,127; `hpd_registrations_grouped_by_bbl_with_contacts` 187,050; `wow_landlords` 172,991; `landlords_with_connections` 119,217; `pluto_latest` 858,312; `real_property_master` 17,143,212; `real_property_legals` 22,833,692; `real_property_parties` 46,772,868. The fingerprint is count plus the sum of the first 60 bits of `md5(row::text)` per row |
| Paired BOR release | `bor-v0.3.0-watchline-2026-10-30.zip`, run `2026-10-30-d416292c`, snapshot `watchline-2026-10-30`, SHA-256 `21677ec3e3020a4dda2f4999b2b45173b99586c456d75db6a6834423aa62b42e` (pinned in `sources.yaml`, `bor_layers`) |
| Dump file and checksum | Pending: no dump of `watchline` has been taken. Until then the fingerprints above identify the database. Tables the loaders read but the BOR manifest does not fingerprint (`hpd_violations`, `hpd_complaints_and_problems`, `hpd_litigations`, `dos_active_corporations`) are not yet identified |
| How it was created | Pending: restore procedure and source dumps not recorded |

**Previous baseline (identified 2026-11-16; superseded 2026-11-28).** The frozen baseline is a plain-SQL dump of the 11 `public` source tables of the live `justfixwow` database, taken by the user on 2026-11-16 and checksummed:

| Item | Value |
| --- | --- |
| Baseline file | `justfixwow-poc-baseline_2026-11-16.sql.gz` (3,529,922,074 bytes), at `~/Learning/Sabbatical/WatchlineNYC/dumps/` on the user's computer, outside Git |
| SHA-256 | `9124f6c0d0f0d2e453f1971247ed29c217d3d4b5f55338d95344e04a617b6278` (user's `shasum -a 256` and the project's `sha256sum` agree; `gzip -t` passes) |
| Contents | `COPY` blocks for `public.acris_document_control_codes`, `dos_active_corporations`, `hpd_complaints_and_problems`, `hpd_contacts`, `hpd_litigations`, `hpd_registrations`, `hpd_violations`, `pluto_latest`, `real_property_legals`, `real_property_master`, `real_property_parties` (checked with `grep '^COPY '`; row counts not recorded) |
| Format and versions | Gzip (`-n`, no stored timestamp) plain SQL; dumped from PostgreSQL 17.10 (Homebrew) by pg_dump 17.10, with `--no-owner --no-privileges` and one `-t` per table above, so the checksum is repeatable |
| Relation to the checks | Every database-backed check was run against the live `justfixwow` on 2026-11-16 (all passing) shortly before this dump; the dump is the fixed record of those tables. A later change to the database is a new baseline and needs the affected fixtures rechecked |

The two upstream JustFix dumps below are provenance, not the baseline. `justfix-db-dump_wow_2026-07-08.sql.gz` holds only the `wow` schema (`wow.wow_bldgs` 181,863 rows, `wow.wow_landlords` 171,347, `wow.wow_portfolios` 97,447); `justfix-db-dump_nycdb_2026-07-08.sql.gz` is the 12.5 GB dump that should hold the `public` tables (its table list is not yet checked). The live `public` tables were not matched to it row by row.

| Item | Value |
| --- | --- |
| Target database | `justfixwow` |
| Source dump filename and local/archive location | `justfix-db-dump_wow_2026-07-08.sql.gz` (37,461,491 bytes), at `~/Learning/Sabbatical/WatchlineNYC/dumps/` on the user's computer, outside Git. It covers the `wow` schema only (see the finding above) |
| Dump origin / download reference | Pending identification (the filename suggests a JustFix Who Owns What dump dated 2026-07-08; no download reference recorded) |
| Dump SHA-256 | `ca3308d012ba64159e123a86535348b9b4c34eeef67c95a7e16a28c82bd27b23`, of the compressed `.sql.gz` exactly as stored (calculated 2026-11-16). Identifies the `wow` schema dump only |
| Dump format | Gzip-compressed plain-text SQL from `pg_dump` (dumped from server 16.11 by pg_dump 16.14, Homebrew). Restored with `psql`, not `pg_restore` |
| PostgreSQL version used to restore | PostgreSQL 17 (`postgresql@17`, Homebrew), from `justfixwow-db-update-notes.md` next to the dump |
| Restoration date | Unknown. The update notes next to the dump are dated 2026-08-12; that shows when the notes were written, not when a restore ran |
| Restore command and prerequisites | Drop and recreate `justfixwow` (owner `wow`), `CREATE EXTENSION postgis;` and `CREATE EXTENSION pg_trgm;`, then `gunzip -c <dump>.sql.gz \| psql -U wow -d justfixwow -h localhost -p 5434` (local cluster on port 5434; one harmless `schema "public" already exists` error is expected). Details in `justfixwow-db-update-notes.md` |
| Post-restore transformations, if any | None recorded in the update notes; not verified. How the `public` source tables were loaded is not recorded |
| Second dump (the `public` source tables, per the user, 2026-11-16) | `justfix-db-dump_nycdb_2026-07-08.sql.gz` (12,547,926,696 bytes), same folder. SHA-256 `76a1644b9232121d0a19b812627d8d67b130c31ba9980ec9b4bfe50eb8eceed7` (calculated 2026-11-16). Gzip plain-text SQL, dumped from server 16.11 by pg_dump 16.14 (Homebrew). Its table list and row counts are not yet checked (a full pass over the 12.5 GB archive). Restore details for it are not recorded (the update notes describe one dump) |

Compute the checksum with `shasum -a 256 /path/to/the-dump` once the file is identified. Record whether it identifies the compressed archive or uncompressed dump. A checksum of an archive should refer to the exact archived file used for restoration.

Do not guess whether restoration uses `pg_restore` or `psql`: record the command appropriate to the actual dump format, database setup, required extensions, and role/ownership options. Keep passwords and connection secrets in ignored environment files.

## POC handling

- Keep the source database fixed and access it read-only during extraction and testing. Rebuild only the POC Neo4j target when its model changes.
- Keep raw dumps/extracts and graph data outside Git. The project reserves `data/raw/`, `data/dumps/`, `data/snapshots/`, and `data/generated/` for ignored local data. Commit this README, the source inventory, and small curated test fixtures.
- Retain one identified baseline. Replacing the source dump is an explicit decision and requires rechecking affected expected answers.
- Record source-table coverage dates separately; they can differ within the database. A local query or restoration date is not a publisher's as-of date.
- Identify BOR releases and retrieval caches separately in the relevant fixture notes; they are not part of the JustFix/WoW dump unless explicitly documented.

This record is intentionally manual. No release service, migration framework, or dependency registry is required for the POC.
