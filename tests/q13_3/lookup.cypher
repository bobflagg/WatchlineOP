// Q13.3: how many financing documents of this lot are there by document type, and which are satisfactions or terminations? The kind and the
// description come from the answer contract (a CASE here only for the check). Counts are distinct documents. A satisfaction is a recorded
// document, not proof a loan was paid off; a termination is not proof of payment; no satisfaction is not proof a loan is outstanding.
MATCH (:Lot {bbl: $bbl})-[:HAS_FINANCING_DOCUMENT]->(d:Document)
RETURN d.docType AS docType, count(DISTINCT d) AS documents
ORDER BY docType;
