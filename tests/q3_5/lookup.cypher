// Q3.4 and Q3.5: the values the comparison runs on. For one lot: the grantees of its newest deed(s) (all deeds that tie on the
// newest recorded date) and the owner contacts on the registrations of its buildings. The comparison itself is code
// (src/watchline/compare.py), not stored in the graph.
MATCH (l:Lot {bbl: $bbl})
OPTIONAL MATCH (l)-[:HAS_DEED]->(d:Deed)
WITH l, max(d.recordedDate) AS newest
OPTIONAL MATCH (l)-[:HAS_DEED]->(d2:Deed {recordedDate: newest})-[:HAS_GRANTEE]->(g:Grantee)
WITH l, collect(DISTINCT g {documentId: d2.documentId, .name, .mailingAddress, .addressLine2, .zip}) AS grantees
OPTIONAL MATCH (l)-[:HAS_BUILDING]->(:Building)-[:HAS_REGISTRATION]->(r:Registration)-[:HAS_CONTACT]->(c:Contact)
WHERE c.contactType IN ['CorporateOwner', 'IndividualOwner', 'JointOwner']
RETURN l.bbl AS bbl, grantees,
       collect(DISTINCT c {registrationId: r.registrationId, .contactType, .corporationName, .personName, .mailingAddress, .addressLine2, .zip}) AS owners;
