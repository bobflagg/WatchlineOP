"""Shared helpers for tests/q5_1 to q5_3. Read-only on both databases. Person names are never printed."""

import os
import sys
from pathlib import Path

import psycopg
import yaml
from dotenv import load_dotenv
from neo4j import GraphDatabase

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from watchline.compare import dos_name_agreement, n3  # noqa: E402,F401

REQUIRED_ENV = ("JUSTFIX_DATABASE_URL", "NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD", "NEO4J_DATABASE")
# Rule N3 in SQL (independent of compare.py): uppercase, remove periods and apostrophes, commas to spaces, collapse spaces.
KEY_SQL = "regexp_replace(upper(replace(replace(replace(btrim({c}),'.',''),',',' '),'''','')),'\\s+',' ','g')"
SOURCE_CANDIDATES = f"SELECT dosid FROM dos_active_corporations WHERE {KEY_SQL.format(c='currententityname')} = {KEY_SQL.format(c='%(name)s')} ORDER BY dosid"
SOURCE_RECORD = """
SELECT nullif(btrim(currententityname),''), nullif(btrim(entitytype),''), nullif(btrim(jurisdiction),''), initialdosfilingdate::date::text,
       nullif(btrim(dosprocessname),''), nullif(btrim(dosprocessaddress1),''), nullif(btrim(dosprocessaddress2),''),
       nullif(btrim(dosprocesscity),''), nullif(btrim(dosprocessstate),''), nullif(btrim(dosprocesszip),''),
       nullif(btrim(registeredagentname),''), nullif(btrim(registeredagentaddress1),''), nullif(btrim(registeredagentaddress2),''),
       nullif(btrim(registeredagentcity),''), nullif(btrim(registeredagentstate),''), nullif(btrim(registeredagentzip),'')
FROM dos_active_corporations WHERE dosid = %(id)s
"""
FIELDS = ["name", "entityType", "jurisdiction", "filingDate", "processName", "processAddress", "processAddressLine2", "processCity",
          "processState", "processZip", "agentName", "agentAddress", "agentAddressLine2", "agentCity", "agentState", "agentZip"]
RETURN_GRAPH = "e {.dosId, .name, .entityType, .jurisdiction, filingDate: toString(e.filingDate), .processName, .processAddress, .processAddressLine2, .processCity, .processState, .processZip, .agentName, .agentAddress, .agentAddressLine2, .agentCity, .agentState, .agentZip}"
results = []


def check(name, ok, detail=""):
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  ({detail})" if detail and not ok else ""))


def connect():
    """Return (neo4j driver, pg connection) or exit 1 when .env is incomplete."""
    load_dotenv(ROOT / ".env")
    missing = [k for k in REQUIRED_ENV if not os.environ.get(k)]
    if missing:
        print(f"missing in .env: {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)
    driver = GraphDatabase.driver(os.environ["NEO4J_URI"], auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]))
    pg = psycopg.connect(os.environ["JUSTFIX_DATABASE_URL"])
    pg.read_only = True
    return driver, pg


def load_fixtures(here: Path):
    return yaml.safe_load((here / "fixtures.yaml").read_text())


def source_record(cur, dosid):
    cur.execute(SOURCE_RECORD, {"id": dosid})
    row = cur.fetchone()
    return dict(zip(FIELDS, row)) if row else None


def finish() -> int:
    failed = results.count(False)
    print(f"{len(results) - failed}/{len(results)} checks passed")
    return 0 if failed == 0 else 1


def run_record_check(here: Path, graph_fields: dict, source_fields: list, total_sql: str, total_cypher: str) -> int:
    """Q5.2 / Q5.3: each fixture record is re-derived from the source, read from the graph, and compared on the given fields.

    graph_fields maps lookup.cypher output names to fixture/source field names. A fixture value "<person>" means a person's name is
    recorded (the name itself is not repeated). Totals: the count of the field in the graph equals the count in the source for the graph's records.
    """
    fx = load_fixtures(here)
    lookup = (here / "lookup.cypher").read_text()
    driver, pg = connect()
    with driver, driver.session(database=os.environ["NEO4J_DATABASE"], default_access_mode="READ") as session, pg, pg.cursor() as cur:
        def same(exp, got):
            return all((g is not None) if e == "<person>" else e == g for e, g in zip(exp, got))

        for f in fx["records"]:
            exp = [f["expect"].get(k) for k in source_fields]
            src = source_record(cur, f["dosId"])
            check(f"{f['dosId']} fixture matches source", src is not None and same(exp, [src[k] for k in source_fields]), f"source gives {src and [src[k] for k in source_fields]}")
            row = session.run(lookup, dosId=f["dosId"]).single()
            got = [row[g] for g in graph_fields] if row else None
            check(f"{f['dosId']} graph matches fixture", got is not None and same(exp, got), f"graph has {got}")
        for dosid in fx.get("absent", []):
            check(f"{dosid} out of scope and absent from the graph", session.run(lookup, dosId=dosid).single() is None)
        ids = [r["id"] for r in session.run("MATCH (e:DosEntity) RETURN e.dosId AS id")]
        cur.execute(total_sql, {"ids": ids})
        src_total = cur.fetchone()[0]
        graph_total = session.run(total_cypher).single()[0]
        check("graph total equals the source total for the loaded records", src_total == graph_total, f"graph {graph_total} vs source {src_total}")
        check("a DosEntity exists for the loaded records", len(ids) > 0 and len(ids) == len(set(ids)))
    return finish()
