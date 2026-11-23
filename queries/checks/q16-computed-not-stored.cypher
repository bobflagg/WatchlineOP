// Q16 rules outside what shacl2cypher compiles. Returns the violation count:
//  - no node carries a Q16 session-evidence label (retrieved item, reported claim, report, filing document, claim);
//  - no node or relationship stores a Q16-only answer-contract field (publisher, quoted claim, extracted value, extraction method,
//    source category, fact relation, match basis, search log);
//  - no Lot, Building, Registration, Contact or DosEntity stores a review status (the Q6 MailDropAddress list entry keeps its own).
// Speed (2026-11-18): property predicates are written out and scoped by label or relationship type. A predicate on a property key that
// does not exist is known empty to the planner (the DBMS warns, the driver mutes it), so absence is cheap; the label and type lists are every
// label and type in the graph, so add a new one here.
CALL () { CALL db.labels() YIELD label WHERE label IN ['RetrievedItem', 'ReportedClaim', 'Report', 'FilingDocument', 'Claim', 'WebDocument'] RETURN count(label) AS a }
CALL () { MATCH (n:Lot|Building|Registration|Deed|Grantee|DosEntity|OperationalNetwork|Landlord|OwnerPortfolio|NetworkMaskedAddress|MailDropAddress|PortfolioMaskedAddress|Contact|Document|DocumentParty|Grantor|Violation) WHERE n.publisher IS NOT NULL OR n.quotedClaim IS NOT NULL OR n.extractedValue IS NOT NULL OR n.extractionMethod IS NOT NULL OR n.sourceCategory IS NOT NULL OR n.factRelation IS NOT NULL OR n.matchBasis IS NOT NULL OR n.searchLog IS NOT NULL RETURN count(n) AS b }
CALL () { MATCH ()-[r:HAS_BUILDING|HAS_REGISTRATION|HAS_DEED|HAS_GRANTEE|IN_NETWORK|COVERS|IN_PORTFOLIO|CONNECTED_BY_IDENTITY|CONNECTED_BY_DEED|CONNECTED_BY_NAME|CONNECTED_BY_ADDRESS|ANCHORED_BY|HAS_CONTACT|BASED_ON_CONTACT|HAS_PARTY|HAS_GRANTOR|HAS_FINANCING_DOCUMENT|HAS_VIOLATION]->() WHERE r.publisher IS NOT NULL OR r.quotedClaim IS NOT NULL OR r.extractedValue IS NOT NULL OR r.extractionMethod IS NOT NULL OR r.sourceCategory IS NOT NULL OR r.factRelation IS NOT NULL OR r.matchBasis IS NOT NULL OR r.searchLog IS NOT NULL RETURN count(r) AS c }
CALL () { CALL () { MATCH (n:Lot) WHERE n.reviewStatus IS NOT NULL RETURN n UNION ALL MATCH (n:Building) WHERE n.reviewStatus IS NOT NULL RETURN n UNION ALL MATCH (n:Registration) WHERE n.reviewStatus IS NOT NULL RETURN n UNION ALL MATCH (n:Contact) WHERE n.reviewStatus IS NOT NULL RETURN n UNION ALL MATCH (n:DosEntity) WHERE n.reviewStatus IS NOT NULL RETURN n } RETURN count(n) AS d }
RETURN a + b + c + d AS violationCount;
