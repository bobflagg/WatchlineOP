"""Check Q5.2 process name and address. Read-only on both databases. Run: uv run python tests/q5_2/check_process.py"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from q5_support import run_record_check  # noqa: E402

HERE = Path(__file__).resolve().parent
GRAPH = {"processName": 0, "processAddress": 0, "processCity": 0, "processState": 0, "processZip": 0}
TOTAL_SQL = "SELECT count(nullif(btrim(dosprocessname), '')) FROM dos_active_corporations WHERE dosid = ANY(%(ids)s)"
TOTAL_CYPHER = "MATCH (e:DosEntity) RETURN count(e.processName)"

if __name__ == "__main__":
    sys.exit(run_record_check(HERE, GRAPH, list(GRAPH), TOTAL_SQL, TOTAL_CYPHER))
