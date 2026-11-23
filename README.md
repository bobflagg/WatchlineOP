# WatchlineOP

An ontology pipeline that builds a Neo4j knowledge graph to help NYC tenants,
organizers and housing researchers investigate a landlord from a street
address. It follows the PESP guide *How to Research Your Landlord* (May 2026).
The output is a reproducible, source-cited dossier.

## Approach

- 28 competency questions drive the ontology and become the evaluation set
  (`specs/questions/qNN.md`).
- Each question goes through six stages: data cleanup, vocabulary (SKOS),
  source profiles, taxonomy and thesaurus, ontology (OWL), and SHACL shapes
  with tests.
- Every answer is labeled as a recorded assertion (Type I), a derived lead
  (Type II), or a reported claim. Operational Networks and Owner Portfolios
  are leads to verify, not findings of common ownership.

## Layout

| Path | Contents |
| --- | --- |
| `specs/` | Mission, use case, roadmap, decisions, per-question specs |
| `vocabulary/` | SKOS controlled vocabulary (Turtle) |
| `ontology/` | OWL ontology, example data, negative cases |
| `shapes/`, `queries/checks/` | SHACL shapes and Cypher checks |
| `profiles/` | Source and graph-element profiles |
| `scripts/`, `src/watchline/` | Loaders and checks |
| `tests/` | Per-question tests with expected answers from SQL on a frozen snapshot |
| `data/` | Source inventory and baseline record (raw data is not committed) |

## Running

```
make help
```

Steps are Make targets; unbuilt steps fail on purpose. Loading needs a local
Neo4j and the frozen JustFix/WoW PostgreSQL snapshot (see `data/README.md`),
with credentials in a git-ignored `.env`. Destructive resets need
`CONFIRM=<database name>` and only target the POC graph.

## Status

Work in progress. Acceptance of each question is pending on recording the
frozen dump identity (`data/README.md`).

## License

MIT. See `LICENSE`. Underlying public records keep their own terms.
