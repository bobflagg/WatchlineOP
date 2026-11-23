// Q7.3: which loaded ACRIS documents name both given parties, with each party's recorded role and address and the hub counts?
// $nameKeyA and $nameKeyB are the given names after rule N3 (src/watchline/compare.py n3). A name match is a lead, not a finding of the same party.
// Every party of each document is returned; the two given ones are marked. A blank name or address is absent (null).
MATCH (d:Document)-[:HAS_PARTY]->(:DocumentParty {nameKey: $nameKeyA})
MATCH (d)-[:HAS_PARTY]->(:DocumentParty {nameKey: $nameKeyB})
WITH DISTINCT d
CALL (d) {
  MATCH (d)-[r:HAS_PARTY]->(p:DocumentParty)
  RETURN collect(p {.name, partyType: r.partyType, .mailingAddress, .addressLine2, .zip, .addressNames, .addressDocuments,
                    given: p.nameKey IN [$nameKeyA, $nameKeyB]}) AS parties
}
RETURN d.documentId AS documentId, d.docType AS docType, d.recordedDate AS recordedDate, parties
ORDER BY recordedDate DESC, documentId;
