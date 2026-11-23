"""Check the Stage 2 schema (profiles/) against the vocabulary, data/sources.yaml and the live graph.

Fails (exit 1) if any check fails; nothing is skipped. Read-only on Neo4j; the source database is not touched.

1. YAML files are well-formed and carry the required keys.
2. Every concept ID resolves to a skos:Concept in vocabulary/watchline.ttl; enum values equal their scheme.
3. Every source column named in a schema is in its source profile and in data/sources.yaml columns_used,
   and every profiled column is in columns_used.
4. Files named in proved_by, lookup and recorded exist.
5. The graph holds exactly the declared labels, relationship types, properties, constraints and endpoints,
   with the declared value types, and every "never absent" property is present on every node.

Run: uv run python scripts/check_profiles.py
"""

import os
import re
import sys
from pathlib import Path

import yaml
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
from neo4j import GraphDatabase
from rdflib import Graph, Namespace, RDF, URIRef
from rdflib.namespace import SKOS

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_ENV = ("NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD", "NEO4J_DATABASE")
PROPERTY_KEYS = ("concept", "type", "source", "null_policy")
FIELD_KEYS = ("concept", "source", "type")
VALUE_TYPE = {"string": "STRING", "integer": "INTEGER", "float": "FLOAT", "boolean": "BOOLEAN", "date": "DATE", "list of string": "LIST<STRING>"}

results: list[bool] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  ({detail})" if detail and not ok else ""))


def load_yaml(path: Path):
    try:
        return yaml.safe_load(path.read_text())
    except Exception as exc:  # malformed or missing
        check(f"{path.relative_to(ROOT)} is readable YAML", False, str(exc)[:100])
        return None


def kebab(value: str) -> str:
    """CorporateOwner -> corporate-owner; no_linkage -> no-linkage; already-kebab values are unchanged."""
    return re.sub(r"(?<!^)(?=[A-Z])", "-", str(value)).replace("_", "-").replace(".", "-").lower()


def merge_schemas():
    """Merge every profiles/qNN.yaml into one schema: the graph is shared, so labels, relationship types,
    constraints and properties declared by different questions are checked as one set."""
    files = sorted((ROOT / "profiles").glob("q[0-9][0-9].yaml"))
    loaded = [load_yaml(f) for f in files]
    check(f"{len(files)} question schemas are readable", all(loaded) and bool(files))
    if not all(loaded):
        return None
    merged = {"concept_base": loaded[0]["concept_base"], "sources": [], "graph": {"constraints": [], "nodes": {}, "relationships": {}}, "answer": {}}
    for q in loaded:
        check(f"{q['question']}: concept_base matches", q["concept_base"] == merged["concept_base"])
        for src in q["sources"]:
            if src not in merged["sources"]:
                merged["sources"].append(src)
        merged["graph"]["constraints"] += q["graph"]["constraints"]
        for lab, node in q["graph"]["nodes"].items():
            have = merged["graph"]["nodes"].setdefault(lab, {**node, "properties": {}})
            clash = set(have["properties"]) & set(node["properties"])
            check(f"{q['question']}: {lab} redeclares no property of another question", not clash, f"redeclared: {sorted(clash)}")
            have["properties"].update(node["properties"])
        for name, rel in q["graph"]["relationships"].items():
            check(f"{q['question']}: {name} is declared once", name not in merged["graph"]["relationships"])
            merged["graph"]["relationships"][name] = rel
        merged["answer"].update(q["answer"])
    return merged


def label_expr(spec: str) -> str:
    """A label expression: 'A|B' means either label."""
    return "|".join(f"`{x}`" for x in spec.split("|"))


def main() -> int:
    load_dotenv(ROOT / ".env")
    missing = [k for k in REQUIRED_ENV if not os.environ.get(k)]
    if missing:
        print(f"missing in .env: {', '.join(missing)}", file=sys.stderr)
        return 1

    sources = load_yaml(ROOT / "data" / "sources.yaml")["sources"]
    schema = merge_schemas()
    if schema is None:
        return 1
    vocab = Graph()
    vocab.parse(ROOT / "vocabulary" / "watchline.ttl")
    base = Namespace(schema["concept_base"])
    concepts = {str(c) for c in vocab.subjects(RDF.type, SKOS.Concept)}
    schemes = {str(c) for c in vocab.subjects(RDF.type, SKOS.ConceptScheme)}

    # 1. required keys and source profiles
    profiles = {}
    for key in schema["sources"]:
        p = load_yaml(ROOT / "profiles" / f"{key}.yaml")
        check(f"profiles/{key}.yaml has source_key and columns", bool(p) and p.get("source_key") == key and bool(p.get("columns")))
        profiles[key] = p or {"columns": []}
        names = [c.get("name") for c in profiles[key]["columns"]]
        check(f"profiles/{key}.yaml: every column has a name, type and used_by",
              all(c.get("name") and c.get("physical_type") and c.get("used_by") for c in profiles[key]["columns"]))
        if key in sources and "columns_used" in sources[key]:  # a service such as Geosupport has none
            used = {c.strip() for c in str(sources[key]["columns_used"]).split(",")}
            extra = [n for n in names if n not in used]
            check(f"profiles/{key}.yaml columns are all in data/sources.yaml columns_used", not extra, f"not in columns_used: {extra}")

    nodes = schema["graph"]["nodes"]
    rels = schema["graph"]["relationships"]
    fields = [(q, n, f) for q, a in schema["answer"].items() for n, f in a["fields"].items()]
    props = [(lab, n, p) for lab, node in nodes.items() for n, p in node["properties"].items()]

    for lab, n, p in props:
        check(f"{lab}.{n} declares concept, type, source and null_policy", all(p.get(k) for k in PROPERTY_KEYS))
    for q, n, f in fields:
        check(f"{q} field {n} declares concept, source and type", all(f.get(k) for k in FIELD_KEYS))

    # 2. concepts and enums
    ids = {n["concept"] for n in nodes.values()} | {r["concept"] for r in rels.values()}
    ids |= {p["concept"] for _, _, p in props} | {f["concept"] for _, _, f in fields}
    rel_props = [(name, n, p) for name, r in rels.items() for n, p in r.get("properties", {}).items()]
    ids |= {p["concept"] for _, _, p in rel_props}
    for name, n, p in rel_props:
        check(f"{name}.{n} declares concept, type, source and null_policy", all(p.get(k) for k in PROPERTY_KEYS))
    bad = sorted(i for i in ids if str(base[i]) not in concepts)
    check(f"all {len(ids)} concept IDs exist in vocabulary/watchline.ttl", not bad, f"unknown: {bad}")
    for q, n, f in fields + [(lab, n, p) for lab, n, p in props]:
        if "allowed_scheme" in f:
            scheme = URIRef(base[f["allowed_scheme"]])
            level = f.get("allowed_level")  # "top": the scheme's top concepts; "detail": the concepts with a broader concept
            in_scheme = list(vocab.subjects(SKOS.inScheme, scheme))
            if level == "top":
                in_scheme = [c for c in in_scheme if (c, SKOS.topConceptOf, scheme) in vocab]
            elif level == "detail":
                in_scheme = [c for c in in_scheme if (c, SKOS.broader, None) in vocab]
            members = sorted(str(c).rsplit("/", 1)[-1] for c in in_scheme)
            hidden = {str(h): str(c).rsplit("/", 1)[-1] for c in in_scheme for h in vocab.objects(c, SKOS.hiddenLabel)}
            mapped = sorted(hidden.get(str(v), kebab(v)) for v in f["allowed"])  # the source's code is a hidden label, else its kebab form
            check(f"{q} {n}: scheme {f['allowed_scheme']} exists", str(scheme) in schemes)
            if f.get("allowed_subset"):  # one scheme shared by two layers: each property lists the codes its layer uses
                check(f"{q} {n}: allowed values are distinct concepts of the scheme", len(set(mapped)) == len(mapped) and set(mapped) <= set(members),
                      f"schema {sorted(f['allowed'])} vs scheme {members}")
            else:
                check(f"{q} {n}: allowed values equal the scheme's concepts", mapped == members,
                      f"schema {sorted(f['allowed'])} vs scheme {members}")

    # 3. source columns named in the schema
    text = [str(p["source"]) for _, _, p in props] + [str(f["source"]) for _, _, f in fields]
    text += [str(r["source"]) for r in rels.values()]
    text += [str(p["source"]) for r in rels.values() for p in r.get("properties", {}).values()]
    named = set()
    for s in text:
        named |= set(re.findall(r"\b(pluto|hpd_registrations|hpd_contacts|hpd_violations|hpd_litigations|hpd_complaints|acris_master|acris_parties|acris_legals|nys_corporations|mail_drop_list)\.([a-z0-9_]+)", s))
        named |= {("bor_layers", c) for c in re.findall(r"\bbor_layers\.([a-z_]+\.[a-z_]+)", s)}
        named |= {("geosupport", c) for c in re.findall(r'geosupport\."([^"]+)"', s)}
    for key, col in sorted(named):
        in_profile = col in {c["name"] for c in profiles.get(key, {"columns": []})["columns"]}
        in_sources = key == "geosupport" or col in {c.strip() for c in str(sources[key]["columns_used"]).split(",")}
        check(f"{key}.{col} is in its source profile and columns_used", in_profile and in_sources)

    # 4. referenced files
    paths = [n["proved_by"] for n in nodes.values()] + [p["proved_by"] for _, _, p in props if "proved_by" in p]
    paths += [r["proved_by"] for r in rels.values()]
    paths += [p["proved_by"] for r in rels.values() for p in r.get("properties", {}).values() if "proved_by" in p]
    paths += [a[k] for a in schema["answer"].values() for k in ("lookup", "recorded") if k in a]
    paths += [p for a in schema["answer"].values() for p in a.get("lookups", [])]
    gone = sorted({p for p in paths if not (ROOT / p).exists()})
    check(f"all {len(set(paths))} referenced test files exist", not gone, f"missing: {gone}")

    # 5. the live graph
    driver = GraphDatabase.driver(os.environ["NEO4J_URI"], auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]))
    with driver, driver.session(database=os.environ["NEO4J_DATABASE"], default_access_mode="READ") as s:
        # Fast path: names come from the catalog and are confirmed by a LIMIT 1 probe, so a stale name is not counted.
        labels = {r["l"] for r in s.run("CALL db.labels() YIELD label AS l RETURN l")}
        labels = {l for l in labels if s.run(f"MATCH (n:`{l}`) RETURN 1 LIMIT 1").single()}
        check("graph labels equal the declared labels", labels == set(nodes), f"graph {sorted(labels)} vs schema {sorted(nodes)}")
        types = {r["t"] for r in s.run("CALL db.relationshipTypes() YIELD relationshipType AS t RETURN t")}
        types = {t for t in types if s.run(f"MATCH ()-[r:`{t}`]->() RETURN 1 LIMIT 1").single()}
        check("graph relationship types equal the declared types", types == set(rels), f"graph {sorted(types)} vs schema {sorted(rels)}")

        # The heavy scans (one per label and per relationship type) are independent and read-only: run them in parallel, each in its own session.
        def run(query):
            with driver.session(database=os.environ["NEO4J_DATABASE"], default_access_mode="READ") as ss:
                return ss.run(query).data()

        jobs = {}
        for lab in nodes:
            jobs[("n", lab)] = (f"MATCH (n:`{lab}`) UNWIND keys(n) AS k WITH k, n[k] AS v "
                                "RETURN k, collect(DISTINCT valueType(v)) AS types, count(*) AS present")
            jobs[("c", lab)] = f"MATCH (n:`{lab}`) RETURN count(n) AS c"
        for name, rel in rels.items():
            jobs[("r", name)] = (f"MATCH ()-[r:`{name}`]->() UNWIND keys(r) AS k WITH k, r[k] AS v "
                                 "RETURN k, collect(DISTINCT valueType(v)) AS types")
            jobs[("w", name)] = (f"MATCH (a)-[r:`{name}`]->(b) WHERE NOT (a:{label_expr(rel['from'])} AND b:{label_expr(rel['to'])}) "
                                 "RETURN count(r) AS c")
        with ThreadPoolExecutor(max_workers=int(os.environ.get("JOBS", "6"))) as pool:
            futures = {k: pool.submit(run, q) for k, q in jobs.items()}
            out = {k: f.result() for k, f in futures.items()}

        for lab, node in nodes.items():
            declared = node["properties"]
            in_graph = {r["k"]: r for r in out[("n", lab)]}
            check(f"{lab}: properties in the graph equal the declared properties", set(in_graph) == set(declared),
                  f"undeclared {sorted(set(in_graph) - set(declared))}, missing {sorted(set(declared) - set(in_graph))}")
            total = out[("c", lab)][0]["c"]
            for name, p in declared.items():
                row = in_graph.get(name)
                if row:
                    want = VALUE_TYPE[p["type"]]
                    got = {t.replace(" NOT NULL", "") for t in row["types"]}
                    check(f"{lab}.{name} holds only {p['type']} values", got == {want}, f"graph types {sorted(got)}")
                    if "never absent" in str(p["null_policy"]):
                        check(f"{lab}.{name} is present on every node", row["present"] == total, f"{row['present']} of {total}")
        for name, rel in rels.items():
            declared_rp = rel.get("properties", {})
            in_graph = {r["k"]: r for r in out[("r", name)]}
            check(f"{name}: properties in the graph equal the declared properties", set(in_graph) == set(declared_rp),
                  f"undeclared {sorted(set(in_graph) - set(declared_rp))}, missing {sorted(set(declared_rp) - set(in_graph))}")
            for pname, p in declared_rp.items():
                if pname in in_graph:
                    got = {t.replace(" NOT NULL", "") for t in in_graph[pname]["types"]}
                    check(f"{name}.{pname} holds only {p['type']} values", got == {VALUE_TYPE[p["type"]]}, f"graph types {sorted(got)}")
            wrong = out[("w", name)][0]["c"]
            check(f"{name} runs only from {rel['from']} to {rel['to']}", wrong == 0, f"{wrong} edges elsewhere")
        found = {r["name"]: r for r in s.run("SHOW CONSTRAINTS YIELD name, type, labelsOrTypes, properties")}
        declared = {c["name"]: c for c in schema["graph"]["constraints"]}
        check("graph constraints equal the declared constraints", set(found) == set(declared),
              f"graph {sorted(found)} vs schema {sorted(declared)}")
        for name, c in declared.items():
            r = found.get(name)
            check(f"constraint {name} is a uniqueness constraint on {c['label']}.{c['property']}",
                  bool(r) and r["type"] == "NODE_PROPERTY_UNIQUENESS" and r["labelsOrTypes"] == [c["label"]] and r["properties"] == [c["property"]],
                  f"graph reports type={r and r['type']!r}, labelsOrTypes={r and r['labelsOrTypes']!r}, properties={r and r['properties']!r}")

    failed = results.count(False)
    print(f"{len(results) - failed}/{len(results)} checks passed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
