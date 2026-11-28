"""Print row count and content fingerprint of source tables, with the BOR release's method.

Read-only, against the database in JUSTFIX_DATABASE_URL. Fingerprint = sum of the first 60 bits of md5(row::text) per row, as numeric
(the same method as the BOR manifest's source_tables, so values are comparable with scripts/check_bor_snapshot.py).
Run: uv run python scripts/fingerprint_tables.py [table ...]   (default: the four tables the BOR manifest does not cover)
Prints no credentials.
"""

import os
import sys
from pathlib import Path

import psycopg
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TABLES = ["hpd_violations", "hpd_complaints_and_problems", "hpd_litigations", "dos_active_corporations"]


def main() -> int:
    load_dotenv(ROOT / ".env")
    url = os.environ.get("JUSTFIX_DATABASE_URL")
    if not url:
        print("JUSTFIX_DATABASE_URL is not set", file=sys.stderr)
        return 2
    tables = sys.argv[1:] or DEFAULT_TABLES
    with psycopg.connect(url) as conn:
        conn.read_only = True
        print("database:", conn.execute("SELECT current_database()").fetchone()[0])
        for name in tables:
            found = [r[0] for r in conn.execute(
                "SELECT table_schema FROM information_schema.tables WHERE table_name = %s AND table_schema IN ('public', 'wow')", (name,))]
            if not found:
                print(f"{name}: table not found in schema public or wow")
                continue
            schema = "public" if "public" in found else found[0]
            n, fp = conn.execute(
                f'SELECT count(*), sum((\'x\'||substr(md5(t::text),1,15))::bit(60)::bigint::numeric)::text FROM "{schema}"."{name}" t'
            ).fetchone()
            print(f"{name}: rows {n:,}, fingerprint {fp}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
