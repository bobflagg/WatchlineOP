// Q13.1: which financing documents (mortgage, assignment, satisfaction, termination, agreement) are recorded against this lot?
// $bbl is the lot. A document is one document even when it covers several lots: otherLots counts the other graph lots it names. Count documents,
// not lots. Dates are as recorded (docDate can be absent), the amount is whole dollars and 0 is kept as recorded. An empty list means no financing
// document in the snapshot, not that the lot has no loan. The answer reports documents; it does not say which loan is outstanding.
MATCH (l:Lot {bbl: $bbl})-[:HAS_FINANCING_DOCUMENT]->(d:Document)
CALL (d) { MATCH (d)<-[:HAS_FINANCING_DOCUMENT]-(o:Lot) RETURN count(o) - 1 AS otherLots }
RETURN d.documentId AS documentId, d.docType AS docType, d.docDate AS docDate, d.recordedDate AS recordedDate, d.amount AS amount, otherLots
ORDER BY recordedDate, documentId;
