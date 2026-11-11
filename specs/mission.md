# Mission

WatchlineOP implements an ontology pipeline that turns competency questions into a validated Neo4j knowledge graph. The graph gives an AI agent, working with a human in the loop, a source-cited base for answering questions in its domain. The first use case is helping NYC tenants, organizers, and housing researchers investigate a landlord (`use-case.md`).

## What we build

An ontology pipeline in six stages, each producing a reviewed artifact that the next stage builds on:

1. Controlled vocabulary, in SKOS.
2. Metadata schema.
3. Taxonomy.
4. Thesaurus.
5. Ontology, in OWL 2.
6. Knowledge graph, in Neo4j, validated with SHACL shapes.

WatchlineOP delivers the graph, mappings, and acceptance fixtures and contracts. The research agent is a downstream consumer; implementing its browsing, extraction, and investigation orchestration is outside this project's scope. Graph readiness does not establish that the downstream agent passes its acceptance tests.

Stages, acceptance types, and exit criteria are in `roadmap.md`. Tools and sources are in `tech-stack.md`.

## How we work

- **Competency questions drive everything.** The questions in `specs/questions/` are the requirements and the evaluation set. Every term, class, property and shape traces to at least one of them.
- **One question at a time.** Each is reviewed before the next is started.
- **Every answer can be retraced.** Recorded, derived and reported information are kept apart, and each claim carries its source, snapshot and run.
