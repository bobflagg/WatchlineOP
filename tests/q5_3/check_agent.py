"""Check Q5.3 registered agent. Read-only on both databases. Run: uv run python tests/q5_3/check_agent.py"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from q5_support import run_record_check  # noqa: E402

HERE = Path(__file__).resolve().parent
FIELDS = ["agentName", "agentAddress", "agentAddressLine2", "agentCity", "agentState", "agentZip"]
TOTAL_SQL = "SELECT count(nullif(btrim(registeredagentname), '')) FROM dos_active_corporations WHERE dosid = ANY(%(ids)s)"
TOTAL_CYPHER = "MATCH (e:DosEntity) RETURN count(e.agentName)"

if __name__ == "__main__":
    sys.exit(run_record_check(HERE, dict.fromkeys(FIELDS, 0), FIELDS, TOTAL_SQL, TOTAL_CYPHER))
