# Term-to-question trace

Each concept in `watchline.ttl` and the questions it serves. Updated per question in Stage 1. Prefix `vocab:` is `https://watchline.example/vocab/`.

| Concept (`vocab:`) | Preferred label | Questions |
| --- | --- | --- |
| `tax-lot` | tax lot | Q1.1, Q1.2, Q1.4 |
| `bbl` | BBL | Q1.1 |
| `building` | building | Q1.2 |
| `bin` | BIN | Q1.2 |
| `addressed-building` | addressed building | Q1.2 |
| `street-address` | street address | Q1.1 |
| `alternate-address` | alternate address | Q1.3 |
| `address-resolution` | address resolution | Q1.1, Q1.3 |
| `address-resolution-outcome` | address resolution outcome | Q1.3 |
| `matched-exactly`, `matched-by-variant`, `ambiguous`, `not-found` | outcome values (scheme `address-resolution-outcomes`) | Q1.3 |
| `address-candidate` | address candidate | Q1.3 |
| `inferred-resolution` | inferred resolution | Q1.3 |
| `street-name-variant` | street-name variant | Q1.3 |
| `geosupport-return-code`, `geosupport-reason-code` | Geosupport return / reason code | Q1.3 |
| `hpd-registration` | HPD registration | Q1.2 (extended by Q2) |
| `source-reported-characteristic` | source-reported characteristic | Q1.4 |
| `year-built`, `building-class`, `residential-units`, `assessed-value` | the four characteristics | Q1.4 |
| `reported-count`, `parcel-count`, `building-count`, `unit-count` | counts, each with its counting unit | Q1.2, Q1.4 |
| `source-snapshot`, `source-record` | provenance | Q1.4 (all) |

## Stage 3 (taxonomy)

Q1: 8 `skos:broader` links, each justified in `taxonomy-notes.md`. `addressed-building` is now a top concept related to `building` (was narrower). No concept IDs changed.
