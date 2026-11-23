// Q18.1: which deeds are recorded on these lots, and how is each classified? $bbls are the lots asked about (one lot, or the lots of an Owner
// Portfolio taken from Q12.2); $start and $end are recorded-date bounds ('YYYY-MM-DD', inclusive) or null. Group membership only chooses the lots:
// nothing here reads it. A deed is one document even when it covers several lots (lots lists those it covers inside $bbls). Count deeds, not lots.
// classification (computed, never stored): 'correction' = type CORRD or CONDEED; 'zero-transfer' = recorded amount 0 and not a correction;
// 'priced' = an amount above 0 and not a correction. 'priced' is not a finding of an arm's-length sale, and 'zero-transfer' is a hint, not a
// finding of restructuring. Grantors and grantees are every distinct party row as recorded; a person's name is shown with role and source, never repeated in notes.
UNWIND $bbls AS bbl
MATCH (l:Lot {bbl: bbl})-[:HAS_DEED]->(d:Deed)
WHERE ($start IS NULL OR d.recordedDate >= date($start)) AND ($end IS NULL OR d.recordedDate <= date($end))
WITH d, collect(DISTINCT l.bbl) AS lots
CALL (d) { OPTIONAL MATCH (d)-[:HAS_GRANTOR]->(g:Grantor) RETURN collect(CASE WHEN g IS NULL THEN null ELSE g.name END) AS grantors }
CALL (d) { OPTIONAL MATCH (d)-[:HAS_GRANTEE]->(g:Grantee) RETURN collect(CASE WHEN g IS NULL THEN null ELSE g.name END) AS grantees }
RETURN d.documentId AS documentId, d.docType AS docType, d.docDate AS docDate, d.recordedDate AS recordedDate, d.amount AS amount,
       CASE WHEN d.docType IN ['CORRD', 'CONDEED'] THEN 'correction' WHEN d.amount = 0 THEN 'zero-transfer' ELSE 'priced' END AS classification,
       lots, grantors, grantees
ORDER BY recordedDate, documentId;
