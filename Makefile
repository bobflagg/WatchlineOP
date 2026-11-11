# WatchlineOP pipeline. Run `make help`.
# Steps follow specs/roadmap.md (stages 1-6) and specs/physical-implementation.md.
# Targets marked "not implemented" fail on purpose: an unbuilt step must never look like a pass.
# Credentials stay in .env and are read by the scripts (dotenv). This Makefile never prints them.

.DEFAULT_GOAL := help
SHELL := /bin/bash

# POC graph target. Destructive steps must name it explicitly (physical-implementation.md, section 7).
NEO4J_DB ?= watchline
CONFIRM  ?=
REQUIRED_ENV := JUSTFIX_DATABASE_URL NEO4J_URI NEO4J_USER NEO4J_PASSWORD NEO4J_DATABASE
DIRS := vocabulary profiles ontology shapes mappings queries tests tests/fixtures scripts

define todo
	@echo "not implemented: $(1)" >&2; exit 1
endef

.PHONY: help setup dirs versions check-env \
        vocab profiles taxonomy thesaurus ontology \
        schema load reconcile shapes test graph rebuild clean

help: ## Show this help
	@awk 'BEGIN{FS=":.*## "} /^[a-zA-Z_-]+:.*## /{printf "  %-12s %s\n",$$1,$$2}' $(MAKEFILE_LIST)

## --- Environment ---------------------------------------------------------

setup: ## Install Python dependencies from the lockfile
	uv sync

dirs: ## Create the planned repository layout
	mkdir -p $(DIRS)

versions: ## Print tool versions to record with test results
	@uv --version; uv run python --version

check-env: ## Verify required .env keys are set (values are not printed)
	@test -f .env || { echo ".env not found" >&2; exit 1; }
	@missing=0; for k in $(REQUIRED_ENV); do \
	  grep -Eq "^$$k=.+" .env || { echo "missing in .env: $$k" >&2; missing=1; }; \
	done; exit $$missing

## --- Stages 1-5: semantic artifacts --------------------------------------
# Vocabulary validation runs through the skos MCP server (validate_skos), not from Make.

vocab: ## Stage 1: check the controlled vocabulary file exists
	@test -f vocabulary/watchline.ttl || { echo "vocabulary/watchline.ttl not found" >&2; exit 1; }
	@echo "present. Run validate_skos through the skos MCP server and review its findings."

profiles: ## Stage 2: validate application profiles and column crosswalks
	uv run python scripts/check_profiles.py

taxonomy: ## Stage 3: check broader/narrower links against vocabulary/taxonomy-notes.md
	uv run python scripts/check_taxonomy.py

thesaurus: ## Stage 4: check related links, label notes and external mappings
	uv run python scripts/check_thesaurus.py

ontology: ## Stage 5: ontology, reasoner and OOPS!
	$(call todo,stage 5 ontology checks)

## --- Stage 6: knowledge graph ---------------------------------------------

schema: check-env ## Apply scripts/neo4j-schema.cypher and verify indexes are online
	$(call todo,apply scripts/neo4j-schema.cypher and verify indexes)

load: check-env ## Load the graph from the frozen snapshot using mappings/
	$(call todo,mapping-driven load in bounded batches)

reconcile: check-env ## Source-to-stage-to-graph counts and persisted-value checks
	$(call todo,count and value reconciliation)

shapes: check-env ## Compile shapes (strict) and run shape and supplemental checks
	$(call todo,shacl2cypher strict compile and execution)

test: check-env ## Graph acceptance queries and negative fixtures
	$(call todo,graph acceptance tests against frozen fixtures)

graph: schema load reconcile shapes test ## Full graph build and validation

rebuild: ## Destructive: reset the POC graph (needs CONFIRM=<database name>)
	@test "$(CONFIRM)" = "$(NEO4J_DB)" || { echo "refusing: run 'make rebuild CONFIRM=$(NEO4J_DB)' to reset database '$(NEO4J_DB)'" >&2; exit 1; }
	$(call todo,reset the $(NEO4J_DB) database only; never the source DB or other graphs)

clean: ## Remove Python caches
	find . -name __pycache__ -type d -not -path './.venv/*' -prune -exec rm -rf {} +
