"""Load DosEntity nodes (Q5.1 to Q5.3): NY DOS active-entity records whose name matches a name already in the graph.

Run after scripts/load_registrations.py and scripts/load_deeds.py. Rules (see tests/q5_1/expected.sql):
  - Scope: a DOS record is loaded when its name key (rule N3, src/watchline/compare.py) equals the key of a
    CorporateOwner OwnerContact name or of a Grantee name already in the graph. Nothing else from the 4.2M-row table.
  - nameKey is a lookup key (N3 of the DOS name), not an answer field. No link to OwnerContact or Grantee is stored:
    a name match is a lead and the comparison is computed at answer time.
  - Every record that shares a key is loaded (15+ keys carry two DOS ids); none is chosen.
  - Blank text is absent. Process name 'THE COMPANY' and 'THE LIMITED LIABILITY COMPANY' are kept as recorded.
    CEO and location are not loaded (empty for LLCs; the answer says "not carried").

Safe to rerun (MERGE). Reads the source read-only and writes only to the POC database.
Run: uv run python scripts/load_dos.py
"""

import os
import sys
import time
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from neo4j import GraphDatabase

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from watchline.compare import n3  # noqa: E402

POC_DATABASE = "watchline"
REQUIRED_ENV = ("JUSTFIX_DATABASE_URL", "NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD", "NEO4J_DATABASE")
CHUNK = 5000

NAMES_SQL = "SELECT dosid, currententityname FROM dos_active_corporations"
RECORDS_SQL = """
SELECT dosid, nullif(btrim(currententityname), ''), nullif(btrim(entitytype), ''), nullif(btrim(jurisdiction), ''), initialdosfilingdate::date,
       nullif(btrim(dosprocessname), ''), nullif(btrim(dosprocessaddress1), ''), nullif(btrim(dosprocessaddress2), ''),
       nullif(btrim(dosprocesscity), ''), nullif(btrim(dosprocessstate), ''), nullif(btrim(dosprocesszip), ''),
       nullif(btrim(registeredagentname), ''), nullif(btrim(registeredagentaddress1), ''), nullif(btrim(registeredagentaddress2), ''),
       nullif(btrim(registeredagentcity), ''), nullif(btrim(registeredagentstate), ''), nullif(btrim(registeredagentzip), '')
FROM dos_active_corporations WHERE dosid = ANY(%(ids)s)
"""
CONSTRAINTS = [
    "CREATE CONSTRAINT dos_entity_id_unique IF NOT EXISTS FOR (e:DosEntity) REQUIRE e.dosId IS UNIQUE",
    "CREATE INDEX dos_entity_name_key IF NOT EXISTS FOR (e:DosEntity) ON (e.nameKey)",
]
GRAPH_NAMES = """
CALL () { MATCH (c:OwnerContact {contactType: 'CorporateOwner'}) WHERE c.name IS NOT NULL RETURN collect(DISTINCT c.name) AS a }
CALL () { MATCH (g:Grantee) WHERE g.name IS NOT NULL RETURN collect(DISTINCT g.name) AS b }
RETURN a + b AS names
"""
LOAD = """
UNWIND $rows AS row
MERGE (e:DosEntity {dosId: row.id})
SET e.name = row.name, e.nameKey = row.key, e.entityType = row.type, e.jurisdiction = row.jur, e.filingDate = date(row.filed),
    e.processName = row.pname, e.processAddress = row.paddr, e.processAddressLine2 = row.paddr2, e.processCity = row.pcity,
    e.processState = row.pstate, e.processZip = row.pzip,
    e.agentName = row.aname, e.agentAddress = row.aaddr, e.agentAddressLine2 = row.aaddr2, e.agentCity = row.acity,
    e.agentState = row.astate, e.agentZip = row.azip
RETURN count(*) AS loaded
"""
COUNTS = """
MATCH (e:DosEntity)
RETURN count(e) AS entities, count(e.processName) AS with_process, count(e.agentName) AS with_agent, count(e.jurisdiction) AS with_jur
"""


def main() -> int:
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    missing = [k for k in REQUIRED_ENV if not os.environ.get(k)]
    if missing:
        print(f"missing in .env: {', '.join(missing)}", file=sys.stderr)
        return 1
    if os.environ["NEO4J_DATABASE"] != POC_DATABASE:
        print(f"refusing: NEO4J_DATABASE is not the POC database '{POC_DATABASE}'", file=sys.stderr)
        return 1
    started = time.time()
    driver = GraphDatabase.driver(os.environ["NEO4J_URI"], auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]))
    try:
        driver.verify_connectivity()
    except Exception as exc:
        print(f"cannot reach Neo4j ({type(exc).__name__}). Is the DBMS started in Neo4j Desktop?", file=sys.stderr)
        return 1
    with driver, driver.session(database=POC_DATABASE) as session:
        for c in CONSTRAINTS:
            session.run(c).consume()
        names = session.run(GRAPH_NAMES).single()["names"]
        keys = {k for k in map(n3, names) if k}
        if not keys:
            print("no owner or grantee names in the graph: run the registration and deed loaders first", file=sys.stderr)
            return 1
        print(f"  graph name keys: {len(keys):,} ({time.time() - started:.0f}s)", flush=True)
        staged, loaded = [], 0
        with psycopg.connect(os.environ["JUSTFIX_DATABASE_URL"]) as pg:
            pg.read_only = True
            with pg.cursor(name="dos_names") as scan:
                scan.itersize = 50000
                scan.execute(NAMES_SQL)
                staged = [i for i, nm in scan if n3(nm) in keys]
            print(f"  matching DOS records: {len(staged):,} ({time.time() - started:.0f}s)", flush=True)
            with pg.cursor() as cur:
                for i in range(0, len(staged), CHUNK):
                    cur.execute(RECORDS_SQL, {"ids": staged[i:i + CHUNK]})
                    rows = [{"id": r[0], "name": r[1], "key": n3(r[1]), "type": r[2], "jur": r[3], "filed": r[4].isoformat(),
                             "pname": r[5], "paddr": r[6], "paddr2": r[7], "pcity": r[8], "pstate": r[9], "pzip": r[10],
                             "aname": r[11], "aaddr": r[12], "aaddr2": r[13], "acity": r[14], "astate": r[15], "azip": r[16]}
                            for r in cur.fetchall()]
                    loaded += session.execute_write(lambda tx, b=rows: tx.run(LOAD, rows=b).single()["loaded"])
        g = session.run(COUNTS).single()
    print(f"staged: DOS records {len(staged):,}")
    print(f"graph:  DosEntity {g['entities']:,} (process name {g['with_process']:,}, agent {g['with_agent']:,}, jurisdiction {g['with_jur']:,})")
    ok = loaded == len(staged) == g["entities"]
    print("reconciled" if ok else "MISMATCH between staged and graph counts", file=sys.stdout if ok else sys.stderr)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
