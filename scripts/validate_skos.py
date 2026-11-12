"""Run validate_skos on the vocabulary from the command line.

Calls skoslib.validate_rdf, the function behind the skos MCP server's validate_skos tool, from a local clone of
Intentional Arrangement SKOS. It needs that repo's Python environment (rdflib, pyshacl), so run it through
`make vocab`, which uses the repo's own virtual environment. Nothing is written to the SKOS repo and nothing
is sent anywhere: the vocabulary file is read locally.

Exit code 0 only if the report is ok with 0 violations, 0 warnings and no structural findings. Info-level SHACL
notes (for example the optional dcterms:publisher) are printed and do not fail the run.

Usage: SKOS_REPO=/path/to/intentional-arrangement-skos python scripts/validate_skos.py [vocabulary.ttl]
"""
import json
import os
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    repo = os.environ.get("SKOS_REPO")
    if not repo or not (Path(repo) / "api" / "skoslib.py").exists():
        print("SKOS_REPO must point to a clone of intentional-arrangement-skos (needs api/skoslib.py)", file=sys.stderr)
        return 1
    sys.path.insert(0, str(Path(repo) / "api"))
    import skoslib

    path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "vocabulary" / "watchline.ttl"
    report = skoslib.validate_rdf(path.read_text(), None)
    summary = report["summary"]
    print(json.dumps({k: report[k] for k in ("ok", "triples", "structural_findings", "profile", "summary")}, indent=1))
    notes = sorted(set(re.findall(r'sh:resultMessage "([^"]+)"|Message: ([^\n]+)', str(report.get("shacl_report", "")))))
    for note in notes:
        print("info:", next(n for n in note if n))
    ok = (report["ok"] and summary["violations"] == 0 and summary["warnings"] == 0
          and not report["structural_findings"])
    print("validate_skos: " + ("clean" if ok else "FINDINGS - see above"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
