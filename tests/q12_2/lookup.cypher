// Q12.2: which deeds are recorded in the period for the lots currently attributed to this lot's Owner Portfolio, counted once each?
// $bbl is the lot asked about; $start and $end are recorded-date bounds ('YYYY-MM-DD', inclusive) or null. Group ids are run-local (BOR run
// 2026-05-29-869bd299); the portfolio is an apparent-owner attribution, a lead to verify, never legal ownership, and current membership is not
// historical ownership. A lot in no portfolio has portfolioGroupId null and only its own deeds are returned (Q12.1). Lots are rental lots in the
// graph. A deed covering several portfolio lots is one deed: lots lists those it covers inside the set. Count deeds, not lots.
// notSale as in Q12.1 (amount 0, or type CORRD or CONDEED). An empty deeds list means no deed in the snapshot for the period.
MATCH (l0:Lot {bbl: $bbl})
OPTIONAL MATCH (l0)-[:IN_PORTFOLIO]->(p:OwnerPortfolio)
CALL (l0, p) {
  OPTIONAL MATCH (p)<-[:IN_PORTFOLIO]-(m:Lot)
  RETURN CASE WHEN p IS NULL THEN [l0] ELSE collect(m) END AS members
}
CALL (members) {
  UNWIND members AS m
  MATCH (m)-[:HAS_DEED]->(d:Deed)
  WHERE ($start IS NULL OR d.recordedDate >= date($start)) AND ($end IS NULL OR d.recordedDate <= date($end))
  WITH d, collect(DISTINCT m.bbl) AS lots
  CALL (d) { OPTIONAL MATCH (d)-[:HAS_GRANTOR]->(g:Grantor) RETURN collect(CASE WHEN g IS NULL THEN null ELSE g.name END) AS grantors }
  CALL (d) { OPTIONAL MATCH (d)-[:HAS_GRANTEE]->(g:Grantee) RETURN collect(CASE WHEN g IS NULL THEN null ELSE g.name END) AS grantees }
  RETURN collect({documentId: d.documentId, docType: d.docType, recordedDate: d.recordedDate, amount: d.amount,
                  notSale: (d.amount = 0 OR d.docType IN ['CORRD', 'CONDEED']), lots: lots, grantors: grantors, grantees: grantees}) AS deeds
}
RETURN l0.bbl AS bbl, p.groupId AS portfolioGroupId, p.composition AS portfolioComposition, [m IN members | m.bbl] AS portfolioLots, deeds;
