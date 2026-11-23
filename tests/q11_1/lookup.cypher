// Q11.1: which recorded mortgages name this entity, in which role, with which counterparties? $nameKey is the given name after rule N3
// (src/watchline/compare.py n3). Role is the recorded partytype on a mortgage: 1 borrower, 2 lender. A lender is a financing
// relationship, not control or parenthood; a co-borrower is a shared-borrower record, not common control. A name match is a lead.
// The amount is whole dollars as recorded. Scope M: mortgages naming at least one HPD corporate owner (decision 2026-11-16).
MATCH (d:Document {docType: 'MTGE'})-[r:HAS_PARTY]->(:DocumentParty {nameKey: $nameKey})
WITH d, collect(DISTINCT r.partyType) AS givenRoles
CALL (d) {
  MATCH (d)-[r2:HAS_PARTY]->(p:DocumentParty)
  RETURN collect(p {.name, .nameKey, partyType: r2.partyType, .mailingAddress, .zip}) AS parties
}
RETURN d.documentId AS documentId, d.recordedDate AS recordedDate, d.docDate AS docDate, d.amount AS amount, givenRoles, parties
ORDER BY recordedDate DESC, documentId;
