"""Load Q11.1 financing documents: mortgages (MTGE) naming at least one HPD corporate owner (rule N3), as Document, DocumentParty
and HAS_PARTY (the Q7.3 elements, same rules). Scope M, decision 2026-11-16: 492,092 documents profiled by scripts/profile_q11_scope.py.
Run after scripts/load_registrations.py. Safe to rerun (MERGE). Reads the source read-only; writes only to the POC database.
Allow several minutes. Run: uv run python scripts/load_mortgages.py
"""

import sys

import load_documents

if __name__ == "__main__":
    sys.exit(load_documents.main(load_documents.MORTGAGE_SQL, "scope M (mortgages)"))
