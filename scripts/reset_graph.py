"""Reset the POC graph: delete every node and relationship, and drop every constraint and index of the POC database.

Refuses unless NEO4J_DATABASE is 'watchline'. Never touches the source database or another Neo4j database.
The loaders recreate their own constraints. Run through `make rebuild CONFIRM=watchline`.
"""
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from neo4j import GraphDatabase

POC_DATABASE = "watchline"


def main() -> int:
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    if os.environ.get("NEO4J_DATABASE") != POC_DATABASE:
        print(f"refusing: NEO4J_DATABASE is not the POC database '{POC_DATABASE}'", file=sys.stderr)
        return 1
    driver = GraphDatabase.driver(os.environ["NEO4J_URI"], auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]))
    with driver, driver.session(database=POC_DATABASE) as session:
        before = session.run("MATCH (n) RETURN count(n) AS nodes").single()["nodes"]
        # Batched, in implicit transactions (CALL ... IN TRANSACTIONS cannot run inside an explicit one).
        session.run("MATCH (n) CALL (n) { DETACH DELETE n } IN TRANSACTIONS OF 10000 ROWS").consume()
        for rec in session.run("SHOW CONSTRAINTS YIELD name").data():
            session.run(f"DROP CONSTRAINT `{rec['name']}` IF EXISTS").consume()
        for rec in session.run("SHOW INDEXES YIELD name, type WHERE type <> 'LOOKUP'").data():
            session.run(f"DROP INDEX `{rec['name']}` IF EXISTS").consume()
        after = session.run("MATCH (n) RETURN count(n) AS nodes").single()["nodes"]
    print(f"deleted {before:,} nodes; {after} remain in '{POC_DATABASE}'")
    return 0 if after == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
