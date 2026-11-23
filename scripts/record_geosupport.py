"""Record raw Geosupport responses for the Q1.3 fixtures. Needs the sidecar running (geosupport/README.md).

Writes tests/q1_3/recorded.json: one entry per case with the input, the verbatim sidecar response and the release.
No interpretation happens here; tests/q1_3 replays these files against the classifier, so no Docker is needed in CI.
"""
import json
import sys
import urllib.request
from pathlib import Path

URL = "http://localhost:8081"
OUT = Path(__file__).resolve().parent.parent / "tests" / "q1_3" / "recorded.json"

# (case id, house_number, street_name, borough, why)
CASES = [
    ("exact_D1", "218", "54 STREET", "Brooklyn", "registered form, lot D building 1"),
    ("exact_D2", "220", "54 STREET", "Brooklyn", "lot D building 2 (same lot, different house number)"),
    ("exact_D3", "224", "54 STREET", "Brooklyn", "lot D building 3"),
    ("exact_A", "5413", "7 AVENUE", "Brooklyn", "registered form, anchor A"),
    ("variant_A_named", "5413", "SEVENTH AVENUE", "Brooklyn", "anchor A, name instead of number"),
    ("variant_D_suffix", "224", "54TH STREET", "Brooklyn", "ordinal suffix"),
    ("variant_D_spelled", "224", "FIFTY-FOURTH STREET", "Brooklyn", "spelled ordinal (client retries as digits)"),
    ("variant_D_abbrev", "224", "54 ST", "Brooklyn", "abbreviated suffix"),
    ("exact_manhattan", "76", "3 AVENUE", "Manhattan", "lot 1005560059"),
    ("shared_bin_185", "185", "GRAND STREET", "Manhattan", "BIN 1003074 shared by two lots"),
    ("non_rental_lot", "712", "54 STREET", "Brooklyn", "lot 3008260011: valid lot, not in the graph"),
    ("misspelled_street", "224", "54 STREEET", "Brooklyn", "typo"),
    ("similar_names", "100", "BROAD", "Manhattan", "street name that matches several streets"),
    ("unknown_street", "123", "ZZZZZ STREET", "Brooklyn", "no such street"),
    ("house_out_of_range", "99999", "54 STREET", "Brooklyn", "street exists, number does not"),
    ("no_tax_lot_candidate", "1", "54 STREET", "Brooklyn", "number may fall between lots"),
    ("blank_house", "", "54 STREET", "Brooklyn", "invalid input"),
    ("apostrophe_typed", "10", "Hallett's Pt", "Queens", "apostrophe the city's name lacks (client retries without it)"),
    ("apostrophe_stripped", "10", "Halletts Pt", "Queens", "the retry request, also an input"),
    ("apostrophe_locality", "10", "Hallett's Pt, Astoria", "Queens", "neighborhood after a comma is dropped from the street"),
    ("apostrophe_wrong_borough", "10", "Hallett's Pt", "Brooklyn", "right street, wrong borough: stays ambiguous"),
    ("apostrophe_wrong_borough_stripped", "10", "Halletts Pt", "Brooklyn", "the retry request for the wrong borough"),
    ("apostrophe_zip", "10", "Hallett's Pt", "zip:11102", "ZIP instead of borough (resolve_text with a ZIP in the text)"),
    ("apostrophe_zip_stripped", "10", "Halletts Pt", "zip:11102", "the retry request for the ZIP"),
    ("zip_instead_of_borough", "224", "54 STREET", None, "uses zip_code 11220"),
]


def call(path, payload=None):
    req = urllib.request.Request(URL + path, data=None if payload is None else json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def main():
    release = call("/health")["release"]
    rows = []
    for _id, house, street, borough, _why in CASES:
        row = {"house_number": house, "street_name": street}
        if borough and borough.startswith("zip:"):
            row["zip_code"] = borough[4:]
        elif borough:
            row["borough"] = borough
        else:
            row["zip_code"] = "11220"
        rows.append(row)
    results = call("/resolve_batch", {"rows": rows})["results"]
    out = {"release": release, "cases": [
        {"id": c[0], "why": c[4], "request": r, "response": res} for c, r, res in zip(CASES, rows, results)]}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(f"release {release}; wrote {len(CASES)} cases to {OUT}")
    for case in out["cases"]:
        r = case["response"]
        print(f'{case["id"]:24} GRC={r.get("Geosupport Return Code (GRC)")!s:3} '
              f'BBL={r.get("BOROUGH BLOCK LOT (BBL)")!s:34.34} {str(r.get("Message") or "")[:50]}')


if __name__ == "__main__":
    sys.exit(main())
