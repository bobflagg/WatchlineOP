"""Load the three address classifications of Q6: the Operational Network address mask (Q6.2), the Owner Portfolio address mask (Q6.3) and the
curated mail-drop list (Q6.4).

Run after scripts/load_lots.py (no dependency on other nodes: the two node types have no relationships; the agent matches them to
HPD contact addresses by text). Refuses to load unless the BOR zip, manifest and masked_addresses.csv checksums match
data/sources.yaml, the release has exactly one mask method, normalizer, threshold and decision, and the list file's sha256 matches.
  - NetworkMaskedAddress {addressId, address, degree, maskedEdges} per row of masked_addresses.csv (73). The method, normalizer version,
    threshold and unit are one value each for the whole release and are recorded in data/sources.yaml, not on each node.
    The address is the release's own text: uppercase, no city or ZIP, floor and unit text kept.
  - PortfolioMaskedAddress {address, degree, maskedIdentities} per distinct address text of the identities BOR masked as address evidence
    (decision_events rule splink_address_evidence_mask, 5298 identities; 579 texts). The release names no address for these events, so the
    text is derived: identity_names.business_house, business_street and business_apartment, blanks left out, joined by single spaces, exactly as
    filed (uppercase; an internal double space is kept). addr_degree is one value per text; maskedIdentities counts the masked identities at it.
  - MailDropAddress {listKey, address, zip5, kind, basis, reviewStatus} per row of data/mail_drop_addresses.csv (122). listKey is
    address|zip5 and is identity only. zip5 is absent when blank (one row). The list is preliminary: every row is unreviewed.
Safe to rerun (MERGE and SET). Writes only to the POC database. Run: uv run python scripts/load_service_addresses.py
"""

import csv
import json
from collections import Counter
import hashlib
import os
import sys
from pathlib import Path

import yaml
from dotenv import load_dotenv
from neo4j import GraphDatabase

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from watchline.bor_release import BorRelease  # noqa: E402

POC_DATABASE = "watchline"
REQUIRED_ENV = ("NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD", "NEO4J_DATABASE")
KINDS = {"registered_agent", "law_firm", "management_office", "unknown"}
CONSTRAINTS = [
    "CREATE CONSTRAINT network_masked_address_id_unique IF NOT EXISTS FOR (a:NetworkMaskedAddress) REQUIRE a.addressId IS UNIQUE",
    "CREATE CONSTRAINT portfolio_masked_address_unique IF NOT EXISTS FOR (a:PortfolioMaskedAddress) REQUIRE a.address IS UNIQUE",
    "CREATE CONSTRAINT mail_drop_address_key_unique IF NOT EXISTS FOR (a:MailDropAddress) REQUIRE a.listKey IS UNIQUE",
]
LOAD_MASKED = "UNWIND $rows AS row MERGE (a:NetworkMaskedAddress {addressId: row.addressId}) SET a.address = row.address, a.degree = row.degree, a.maskedEdges = row.maskedEdges"
LOAD_PORTFOLIO_MASKED = "UNWIND $rows AS row MERGE (a:PortfolioMaskedAddress {address: row.address}) SET a.degree = row.degree, a.maskedIdentities = row.maskedIdentities"
LOAD_LIST = """
UNWIND $rows AS row
MERGE (a:MailDropAddress {listKey: row.listKey})
SET a.address = row.address, a.kind = row.kind, a.basis = row.basis, a.reviewStatus = row.reviewStatus
FOREACH (_ IN CASE WHEN row.zip5 IS NULL THEN [1] ELSE [] END | REMOVE a.zip5)
FOREACH (_ IN CASE WHEN row.zip5 IS NULL THEN [] ELSE [1] END | SET a.zip5 = row.zip5)
"""


def main() -> int:
    load_dotenv(ROOT / ".env")
    missing = [k for k in REQUIRED_ENV if not os.environ.get(k)]
    if missing:
        print(f"missing in .env: {', '.join(missing)}", file=sys.stderr)
        return 1
    if os.environ["NEO4J_DATABASE"] != POC_DATABASE:
        print(f"refusing: NEO4J_DATABASE is not the POC database '{POC_DATABASE}'", file=sys.stderr)
        return 1

    release = BorRelease()
    problems = release.verify_identity()
    if not release.verify_zip():
        problems.append("zip sha256 differs from data/sources.yaml")
    if not release.verify_member("masked_addresses"):
        problems.append("masked_addresses.csv checksum differs from the manifest")
    if not release.verify_member("graph_edges"):
        problems.append("graph_edges.csv checksum differs from the manifest")
    for t in ("decision_events", "identity_names"):
        if not release.verify_member(t):
            problems.append(f"{t}.csv checksum differs from the manifest")
    masked = list(release.rows("masked_addresses"))
    for col in ("method", "normalizer_version", "threshold", "degree_unit", "decision"):
        if len({r[col] for r in masked}) != 1:
            problems.append(f"masked_addresses.{col} has more than one value")
    list_file = ROOT / "data/mail_drop_addresses.csv"
    expected = yaml.safe_load((ROOT / "data/sources.yaml").read_text())
    expected = expected.get("sources", expected)["mail_drop_list"]["sha256"]
    if hashlib.sha256(list_file.read_bytes()).hexdigest() != expected:
        problems.append("data/mail_drop_addresses.csv sha256 differs from data/sources.yaml")
    listed = list(csv.DictReader(list_file.open(newline="", encoding="utf-8")))
    if any(r["kind"] not in KINDS for r in listed):
        problems.append("a list row has a kind outside the four known kinds")
    # Edges BOR set aside at a masked address (graph_edges: kept False, drop_reason address_mask). An edge that touches two masked
    # addresses is cited to the one with the lower id, so the counts add up to the 230,305 rows, one address each.
    edges_set_aside = Counter(r["evidence_id"] for r in release.rows("graph_edges", drop_reason="address_mask"))
    masked_rows = [{"addressId": r["address_id"], "address": r["address"], "degree": int(r["degree"]),
                    "maskedEdges": edges_set_aside.get(r["address_id"], 0)} for r in masked]
    if sum(edges_set_aside.values()) != sum(r["maskedEdges"] for r in masked_rows):
        problems.append("graph_edges cites a masked address that masked_addresses.csv does not list")
    if problems:
        print("refusing to load:\n  " + "\n  ".join(problems), file=sys.stderr)
        return 1

    # The Owner Portfolio mask is recorded on identities (rule splink_address_evidence_mask, detail addr_degree), not on addresses. The text is the
    # identity's own business address as filed: house, street and apartment, blanks left out, joined by single spaces. One degree per text.
    identity_text = {}
    for r in release.rows("identity_names"):
        identity_text[r["identity_id"]] = " ".join(p.strip() for p in (r["business_house"], r["business_street"], r["business_apartment"]) if p and p.strip())
    degrees: dict[str, set] = {}
    counts = Counter()
    for e in release.rows("decision_events", rule="splink_address_evidence_mask"):
        text = identity_text.get(e["subject_id"])
        if not text:
            problems.append(f"masked identity {e['subject_id']} has no business address in identity_names")
            continue
        degrees.setdefault(text, set()).add(int(json.loads(e["detail"])["addr_degree"]))
        counts[text] += 1
    if any(len(v) != 1 for v in degrees.values()):
        problems.append("an address text has more than one addr_degree")
    if problems:
        print("refusing to load:\n  " + "\n  ".join(problems), file=sys.stderr)
        return 1
    portfolio_rows = [{"address": t, "degree": next(iter(v)), "maskedIdentities": counts[t]} for t, v in sorted(degrees.items())]

    list_rows = [{"listKey": f"{r['address_key']}|{r['zip5']}", "address": r["address_key"], "zip5": r["zip5"] or None, "kind": r["kind"],
                  "basis": r["basis"], "reviewStatus": r["review_status"]} for r in listed]
    driver = GraphDatabase.driver(os.environ["NEO4J_URI"], auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]))
    with driver, driver.session(database=POC_DATABASE) as session:
        for c in CONSTRAINTS:
            session.run(c).consume()
        session.run(LOAD_MASKED, rows=masked_rows).consume()
        session.run(LOAD_PORTFOLIO_MASKED, rows=portfolio_rows).consume()
        session.run(LOAD_LIST, rows=list_rows).consume()
        n = session.run("MATCH (a:NetworkMaskedAddress) RETURN count(a) AS n").single()["n"]
        m = session.run("MATCH (a:MailDropAddress) RETURN count(a) AS n").single()["n"]
        p = session.run("MATCH (a:PortfolioMaskedAddress) RETURN count(a) AS n, sum(a.maskedIdentities) AS ids").single()
    print(f"NetworkMaskedAddress {n} (release {len(masked_rows)}), PortfolioMaskedAddress {p['n']} (release {len(portfolio_rows)}, "
          f"identities {p['ids']} of {sum(counts.values())}), MailDropAddress {m} (file {len(list_rows)})")
    return 0 if (n, m, p["n"], p["ids"]) == (len(masked_rows), len(list_rows), len(portfolio_rows), sum(counts.values())) else 1


if __name__ == "__main__":
    sys.exit(main())
