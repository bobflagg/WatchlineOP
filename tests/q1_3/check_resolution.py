"""Replay the recorded Geosupport responses through the client and the graph lookup, and compare with fixtures.yaml.

Geosupport is replayed from tests/q1_3/recorded.json, so Docker is not needed; any request not in the recording
fails the run. The graph is read live (read-only). Every case must pass; nothing is skipped.
Run: uv run python tests/q1_3/check_resolution.py
"""
import json
import os
import sys
from pathlib import Path

import httpx
import yaml
from dotenv import load_dotenv
from neo4j import GraphDatabase

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "src"))
from watchline.geosupport import Client  # noqa: E402
from watchline.resolution import BoroughRequired, Neo4jGraph, parse_address, resolve_address, resolve_text  # noqa: E402

REQUIRED_ENV = ("NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD", "NEO4J_DATABASE")


def replay_client(recorded: dict) -> Client:
    index = {json.dumps(c["request"], sort_keys=True): c["response"] for c in recorded["cases"]}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/health":
            return httpx.Response(200, json={"release": recorded["release"]})
        key = json.dumps(json.loads(request.content), sort_keys=True)
        if key not in index:
            raise AssertionError(f"request not in recorded.json: {key}")
        return httpx.Response(200, json=index[key])

    return Client(url="http://replay", http=httpx.Client(transport=httpx.MockTransport(handler)))


def main() -> int:
    load_dotenv(HERE.parents[1] / ".env")
    missing = [k for k in REQUIRED_ENV if not os.environ.get(k)]
    if missing:
        print("missing env:", ", ".join(missing))
        return 1
    recorded = json.loads((HERE / "recorded.json").read_text())
    fixtures = yaml.safe_load((HERE / "fixtures.yaml").read_text())
    fails, total = [], 0
    if recorded["release"] != fixtures["release"]:
        fails.append(f"recorded release {recorded['release']} != fixtures {fixtures['release']}")
    ids = [c["id"] for c in recorded["cases"]]
    if sorted(ids) != sorted(fixtures["cases"]):
        fails.append(f"case ids differ: {sorted(set(ids) ^ set(fixtures['cases']))}")
    client = replay_client(recorded)
    driver = GraphDatabase.driver(os.environ["NEO4J_URI"], auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]))
    with driver:
        graph = Neo4jGraph(driver, os.environ["NEO4J_DATABASE"])
        for case in recorded["cases"]:
            exp = fixtures["cases"].get(case["id"])
            if exp is None:
                continue
            req = case["request"]
            ans = resolve_address(client, graph, req["house_number"], req["street_name"],
                                  borough=req.get("borough"), zip5=req.get("zip_code"))
            got = {"outcome": ans.outcome.value, "bbl": ans.bbl, "bin": ans.bin, "in_graph": ans.in_graph,
                   "related_lots": list(ans.related_lots), "candidates": list(ans.candidates), "grc": ans.grc,
                   "inferred": ans.inferred, "tried": len(ans.tried)}
            for k, v in exp.items():
                total += 1
                if got[k] != v:
                    fails.append(f"{case['id']}: {k} expected {v!r}, got {got[k]!r}")
        for t in fixtures.get("text_cases", []):
            try:
                ans = resolve_text(client, graph, t["input"], borough=t.get("borough"), zip5=t.get("zip"))
            except (BoroughRequired, ValueError) as exc:
                total += 1
                if type(exc).__name__ != t.get("raises"):
                    fails.append(f"text {t['input']!r}: raised {type(exc).__name__}, expected {t.get('raises')}")
                continue
            got = {"outcome": ans.outcome.value, "bbl": ans.bbl, "bin": ans.bin, "inferred": ans.inferred, "tried": len(ans.tried),
                   "borough_inferred_from": ans.borough_inferred_from}
            total += 1
            if t.get("raises"):
                fails.append(f"text {t['input']!r}: expected {t['raises']}, got an answer")
            for k, v in t.get("expect", {}).items():
                total += 1
                if got[k] != v:
                    fails.append(f"text {t['input']!r}: {k} expected {v!r}, got {got[k]!r}")
    for t in fixtures.get("parse_cases", []):
        p = parse_address(t["input"])
        for k in ("house", "street", "borough", "zip5"):
            total += 1
            if getattr(p, k) != t[k]:
                fails.append(f"parse {t['input']!r}: {k} expected {t[k]!r}, got {getattr(p, k)!r}")
        total += 1
        if list(p.locality) != t["locality"]:
            fails.append(f"parse {t['input']!r}: locality expected {t['locality']!r}, got {list(p.locality)!r}")
    for f in fails:
        print("FAIL", f)
    print(f"{total - len([f for f in fails if ': ' in f])}/{total} checks passed" if not fails else f"{len(fails)} failure(s)")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
