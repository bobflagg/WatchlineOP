// Q13.2: who are the parties of each financing document of this lot? partyType is the recorded code. On a mortgage (MTGE) 1 is the borrower and
// 2 the lender; on every other type the answer repeats the code and does not name a role. Name keys (rule N3) are lookup keys, not matches.
MATCH (l:Lot {bbl: $bbl})-[:HAS_FINANCING_DOCUMENT]->(d:Document)
CALL (d) {
  OPTIONAL MATCH (d)-[r:HAS_PARTY]->(p:DocumentParty)
  RETURN collect(CASE WHEN p IS NULL THEN null ELSE p {.name, .nameKey, .mailingAddress, .addressLine2, .zip, partyType: r.partyType} END) AS parties
}
RETURN d.documentId AS documentId, d.docType AS docType, d.recordedDate AS recordedDate, parties
ORDER BY recordedDate, documentId;
