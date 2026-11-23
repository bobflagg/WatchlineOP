// Q12.1: which deeds are recorded for this lot in the period, and how many were not sales? $bbl is the lot; $start and $end are
// recorded-date bounds as 'YYYY-MM-DD' (inclusive) or null for open. A deed is one document, even when it covers several lots: otherLots
// counts the other graph lots it names, so a multi-lot deed is never read as lot-specific. Count deeds, not lots.
// notSale (decision 2026-11-16): the recorded amount is 0, or the type is a correction or confirmatory deed (CORRD, CONDEED). A deed with an
// amount is reported as recorded; the answer does not call it a sale of the building and says nothing about intent.
// Grantors and grantees are every distinct party row as recorded (a blank part is absent). An empty list means no deed in the snapshot,
// not that the lot never changed hands. The amount is whole dollars; the snapshot date is dataset-level.
MATCH (l:Lot {bbl: $bbl})-[:HAS_DEED]->(d:Deed)
WHERE ($start IS NULL OR d.recordedDate >= date($start)) AND ($end IS NULL OR d.recordedDate <= date($end))
CALL (d) {
  OPTIONAL MATCH (d)-[:HAS_GRANTOR]->(g:Grantor)
  RETURN collect(CASE WHEN g IS NULL THEN null ELSE g {.name, .nameKey, .mailingAddress, .addressLine2, .zip} END) AS grantors
}
CALL (d) {
  OPTIONAL MATCH (d)-[:HAS_GRANTEE]->(g:Grantee)
  RETURN collect(CASE WHEN g IS NULL THEN null ELSE g {.name, .nameKey, .mailingAddress, .addressLine2, .zip} END) AS grantees
}
CALL (d) { MATCH (d)<-[:HAS_DEED]-(o:Lot) RETURN count(o) - 1 AS otherLots }
RETURN d.documentId AS documentId, d.docType AS docType, d.docDate AS docDate, d.recordedDate AS recordedDate, d.amount AS amount,
       (d.amount = 0 OR d.docType IN ['CORRD', 'CONDEED']) AS notSale, otherLots, grantors, grantees
ORDER BY recordedDate, documentId;
