"""Compare the pinned BOR release's manifest source_tables with the source database named by JUSTFIX_DATABASE_URL.

Read-only. For each table in manifest.source_tables, counts rows and computes the release's fingerprint
(sum of the first 60 bits of md5(row::text), as numeric) and reports match or difference.
Run: uv run python scripts/check_bor_snapshot.py   (large ACRIS tables take several minutes)
Exit 0 only if every table matches. Prints no credentials.
"""

import os
import sys
from pathlib import Path

import psycopg
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from watchline.bor_release import BorRelease  # noqa: E402


def main() -> int:
    load_dotenv(ROOT / ".env")
    url = os.environ.get("JUSTFIX_DATABASE_URL")
    if not url:
        print("JUSTFIX_DATABASE_URL is not set", file=sys.stderr)
        return 2
    release = BorRelease()
    if not release.verify_zip() or release.verify_identity():
        print("refusing: the release is not the pinned one (check data/sources.yaml)", file=sys.stderr)
        return 2
    tables = release.manifest["source_tables"]
    failures = 0
    with psycopg.connect(url) as conn:
        conn.read_only = True
        print("database:", conn.execute("SELECT current_database()").fetchone()[0])
        for name, want in tables.items():
            found = [r[0] for r in conn.execute(
                "SELECT table_schema FROM information_schema.tables WHERE table_name = %s AND table_schema IN ('public', 'wow')", (name,))]
            if not found:
                print(f"DIFF {name}: table not found in schema public or wow")
                failures += 1
                continue
            schema = "public" if "public" in found else found[0]
            sql = (
                f'SELECT count(*), sum((\'x\'||substr(md5(t::text),1,15))::bit(60)::bigint::numeric)::text FROM "{schema}"."{name}" t'
            )
            n, fp = conn.execute(sql).fetchone()
            ok = n == want["row_count"] and fp == want["fingerprint"]
            failures += not ok
            print(f"{'ok  ' if ok else 'DIFF'} {name}: rows {n:,} (release {want['row_count']:,})"
                  f"{'' if fp == want['fingerprint'] else ', fingerprint differs'}")
    print("all tables match" if not failures else f"{failures} table(s) differ")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
