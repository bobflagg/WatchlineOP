"""Submit the TBox (only) to the OOPS! web service and summarise the pitfalls.

Sends ontology/watchline-onto.ttl (converted to RDF/XML) to
https://oops.linkeddata.es/rest. Saves the raw response to
ontology/oops-report.rdf and prints one line per pitfall.
Nothing else in the project is sent.
"""
import sys
from pathlib import Path
from xml.sax.saxutils import escape

import httpx
from rdflib import Graph, Namespace, RDF

ROOT = Path(__file__).resolve().parent.parent
TBOX = ROOT / "ontology" / "watchline-onto.ttl"
REPORT = ROOT / "ontology" / "oops-report.rdf"
URL = "https://oops.linkeddata.es/rest"
OOPS = Namespace("http://oops.linkeddata.es/def#")
OOPS_ERR = Namespace("http://www.oeg-upm.net/oops#")


def main() -> int:
    rdfxml = Graph().parse(TBOX, format="turtle").serialize(format="xml")
    wrappers = {"cdata": lambda x: f"<![CDATA[{x}]]>", "escaped": escape}
    attempts = [(w, fmt) for w in wrappers for fmt in ("RDF/XML", "XML")]
    print(f"Submitting {TBOX.relative_to(ROOT)} to {URL} ...")
    for wrap, fmt in attempts:
        body = ('<?xml version="1.0" encoding="UTF-8"?><OOPSRequest>'
                "<OntologyUrl></OntologyUrl>"
                f"<OntologyContent>{wrappers[wrap](rdfxml)}</OntologyContent>"
                f"<Pitfalls></Pitfalls><OutputFormat>{fmt}</OutputFormat></OOPSRequest>")
        try:
            r = httpx.post(URL, content=body.encode(), timeout=120,
                           headers={"Content-Type": "application/xml"})
        except httpx.HTTPError as e:
            print(f"FAIL  request error: {e}")
            return 1
        REPORT.write_text(r.text)
        if r.status_code == 200 and "went wrong" not in r.text:
            print(f"(accepted: content={wrap}, OutputFormat={fmt})")
            break
        print(f"  rejected: content={wrap}, OutputFormat={fmt}, HTTP {r.status_code}")
    else:
        print(f"FAIL  every variant was rejected (last response in {REPORT.relative_to(ROOT)})")
        return 1
    g = Graph().parse(data=r.text, format="xml")
    for title in g.objects(None, OOPS_ERR.hasTitle):
        if "went wrong" in str(title):
            print(f"FAIL  OOPS! returned its error response (see {REPORT.relative_to(ROOT)})")
            return 1
    found = []
    for p in g.subjects(RDF.type, OOPS.pitfall):
        val = lambda pred: str(next(iter(g.objects(p, pred)), ""))
        found.append((val(OOPS.hasCode), val(OOPS.hasImportanceLevel),
                      val(OOPS.hasName), val(OOPS.hasNumberAffectedElements)))
    if not found:
        print("No pitfalls reported.")
    for code, level, name, n in sorted(found):
        print(f"{code:6} {level:10} {name}  (affected: {n or '?'})")
    for p in g.subjects(RDF.type, OOPS.pitfall):
        for el in g.objects(p, OOPS.hasAffectedElement):
            print(f"       {next(iter(g.objects(p, OOPS.hasCode)), '')}: {el}")
    print(f"{len(found)} pitfall(s). Raw report: {REPORT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
