// Q3.2: who is named as receiving title on this deed? Every grantee is returned; none is chosen.
// A name or address that is blank in the source is absent (null), not an empty string.
MATCH (d:Deed {documentId: $documentId})
OPTIONAL MATCH (d)-[:HAS_GRANTEE]->(g:Grantee)
RETURN d.documentId AS documentId,
       collect(CASE WHEN g IS NULL THEN null ELSE g {.name, .mailingAddress, .addressLine2, .zip} END) AS grantees;
