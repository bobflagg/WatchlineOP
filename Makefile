# WatchlineOP pipeline. Run `make help`.
# Steps follow specs/roadmap.md (stages 1-6) and specs/physical-implementation.md.
# Targets marked "not implemented" fail on purpose: an unbuilt step must never look like a pass.
# Credentials stay in .env and are read by the scripts (dotenv). This Makefile never prints them.

.DEFAULT_GOAL := help
SHELL := /bin/bash

# POC graph target. Destructive steps must name it explicitly (physical-implementation.md, section 7).
NEO4J_DB ?= watchline
CONFIRM  ?=
SKOS_REPO ?= $(HOME)/git-alt/intentional-arrangement-skos
REQUIRED_ENV := JUSTFIX_DATABASE_URL NEO4J_URI NEO4J_USER NEO4J_PASSWORD NEO4J_DATABASE
DIRS := src scripts tests specs data geosupport

define todo
	@echo "not implemented: $(1)" >&2; exit 1
endef

.PHONY: shapes oops help setup dirs versions check-env \
        vocab profiles taxonomy thesaurus ontology \
        load test graph rebuild rebuild-all clean

help: ## Show this help
	@awk 'BEGIN{FS=":.*## "} /^[a-zA-Z_-]+:.*## /{printf "  %-12s %s\n",$$1,$$2}' $(MAKEFILE_LIST)

## --- Environment ---------------------------------------------------------

setup: ## Install Python dependencies from the lockfile
	uv sync

dirs: ## Create the planned repository layout
	mkdir -p $(DIRS)

versions: ## Print tool versions to record with test results
	@uv --version; uv run python --version; java -version 2>&1 | head -1; tools/robot --version 2>&1 | tail -1

check-env: ## Verify required .env keys are set (values are not printed)
	@test -f .env || { echo ".env not found" >&2; exit 1; }
	@missing=0; for k in $(REQUIRED_ENV); do \
	  grep -Eq "^$$k=.+" .env || { echo "missing in .env: $$k" >&2; missing=1; }; \
	done; exit $$missing

## --- Stages 1-5: semantic artifacts --------------------------------------
# Vocabulary validation runs through the skos MCP server (validate_skos), not from Make.

vocab: ## Stage 1: run validate_skos on the vocabulary (uses a local clone of intentional-arrangement-skos)
	@test -f vocabulary/watchline.ttl || { echo "vocabulary/watchline.ttl not found" >&2; exit 1; }
	@test -x "$(SKOS_REPO)/.venv/bin/python" || { echo "SKOS_REPO not found: set SKOS_REPO=/path/to/intentional-arrangement-skos" >&2; exit 1; }
	SKOS_REPO="$(SKOS_REPO)" "$(SKOS_REPO)/.venv/bin/python" scripts/validate_skos.py vocabulary/watchline.ttl

profiles: check-env ## Stage 2: check profiles/ against the vocabulary, data/sources.yaml and the live graph
	uv run python scripts/check_profiles.py

taxonomy: ## Stage 3 (not yet redone)
	$(call todo,stage 3 taxonomy)

thesaurus: ## Stage 4: check related links, notes, labels and external mappings
	uv run python scripts/check_thesaurus.py

ontology: ## Stage 5: check the ontology, mapping, notes and reasoner (needs Java and tools/robot)
	uv run python scripts/check_ontology.py

oops: ## Stage 5: send the TBox (only) to the OOPS! web service and list its pitfalls
	uv run python scripts/oops_scan.py

## --- Stage 6: knowledge graph (Q1 so far: Lot, Building) -------------------
# Each loader reconciles staged and graph counts and exits non-zero on a mismatch.

load: check-env ## Load Lot, Building and HAS_BUILDING, then Registration, HAS_REGISTRATION and OwnerContact (order matters)
	uv run python scripts/load_lots.py
	uv run python scripts/load_buildings.py
	uv run python scripts/load_registrations.py
	uv run python scripts/load_deeds.py
	uv run python scripts/load_dos.py

test: check-env ## Run every sub-question check (tests/q*_*/check_*.py); all must pass
	@for f in tests/q*_*/check_*.py; do echo "== $$f"; uv run python $$f || exit 1; done

shapes: check-env ## Stage 6: compile the SHACL shapes, run them on the graph, run the seeded bad-data cases
	uv run python scripts/check_shapes.py

graph: load profiles test shapes ## Full graph build and validation

rebuild: ## Destructive: reset the POC graph (needs CONFIRM=<database name>)
	@test "$(CONFIRM)" = "$(NEO4J_DB)" || { echo "refusing: run 'make rebuild CONFIRM=$(NEO4J_DB)' to reset database '$(NEO4J_DB)'" >&2; exit 1; }
	uv run python scripts/reset_graph.py

rebuild-all: ## Destructive: rebuild, then graph, ontology and thesaurus in order (needs CONFIRM=<database name>)
	$(MAKE) rebuild CONFIRM=$(CONFIRM)
	$(MAKE) graph
	$(MAKE) ontology
	$(MAKE) thesaurus

clean: ## Remove Python caches
	find . -name __pycache__ -type d -not -path './.venv/*' -prune -exec rm -rf {} +
