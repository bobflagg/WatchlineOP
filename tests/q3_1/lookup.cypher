// Q3.1: which deeds are recorded against this lot, newest first? The agent takes the first recordedDate and returns
// every deed that ties on it. otherLots counts the other graph lots the deed sits on, so it is never presented as lot-specific.
MATCH (l:Lot {bbl: $bbl})
OPTIONAL MATCH (l)-[:HAS_DEED]->(d:Deed)
OPTIONAL MATCH (d)<-[:HAS_DEED]-(other:Lot) WHERE other <> l
WITH l, d, count(other) AS otherLots
ORDER BY d.recordedDate DESC, d.documentId
RETURN l.bbl AS bbl,
       collect(CASE WHEN d IS NULL THEN null ELSE d {.documentId, .docType, docDate: toString(d.docDate),
                 recordedDate: toString(d.recordedDate), .amount, otherLots: otherLots} END) AS deeds;
