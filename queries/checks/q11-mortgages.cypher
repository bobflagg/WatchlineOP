// Q11 rules outside what shacl2cypher compiles. Returns the violation count:
//  - a mortgage (docType MTGE) not loaded by scope F has only parties with partyType 1 (borrower) or 2 (lender)
//    (scope F records one mortgage, 2021011100242003, with a party of type 3, kept as recorded);
//  - a mortgage not loaded by scope F (no HAS_FINANCING_DOCUMENT link) names at least one party whose N3 name key equals an HPD CorporateOwner name key (scope M);
//  - no node or relationship stores an affiliation type or an evidence status (both are computed at answer time).
// Speed (2026-11-18): property predicates are written out and scoped by label or relationship type; `any(k IN keys(n) ...)` over every node and
// relationship built a key list per element. The label and type lists below are every label and type in the graph; add a new one here.
CALL () { MATCH (d:Document {docType: 'MTGE'})-[r:HAS_PARTY]->(:DocumentParty) WHERE (r.partyType IS NULL OR NOT r.partyType IN [1, 2])
          AND NOT EXISTS { ()-[:HAS_FINANCING_DOCUMENT]->(d) } RETURN count(r) AS a }
CALL () { MATCH (d:Document {docType: 'MTGE'})
          WHERE NOT EXISTS { ()-[:HAS_FINANCING_DOCUMENT]->(d) } AND NOT EXISTS { MATCH (d)-[:HAS_PARTY]->(p:DocumentParty) WHERE p.nameKey IS NOT NULL
                             MATCH (c:Contact {nameKey: p.nameKey, contactType: 'CorporateOwner'}) }
          RETURN count(d) AS b }
CALL () { MATCH (n:Lot|Building|Registration|Deed|Grantee|DosEntity|OperationalNetwork|Landlord|OwnerPortfolio|NetworkMaskedAddress|MailDropAddress|PortfolioMaskedAddress|Contact|Document|DocumentParty|Grantor|Violation) WHERE n.affiliationType IS NOT NULL OR n.evidenceStatus IS NOT NULL RETURN count(n) AS c }
CALL () { MATCH ()-[r:HAS_BUILDING|HAS_REGISTRATION|HAS_DEED|HAS_GRANTEE|IN_NETWORK|COVERS|IN_PORTFOLIO|CONNECTED_BY_IDENTITY|CONNECTED_BY_DEED|CONNECTED_BY_NAME|CONNECTED_BY_ADDRESS|ANCHORED_BY|HAS_CONTACT|BASED_ON_CONTACT|HAS_PARTY|HAS_GRANTOR|HAS_FINANCING_DOCUMENT|HAS_VIOLATION]->() WHERE r.affiliationType IS NOT NULL OR r.evidenceStatus IS NOT NULL RETURN count(r) AS d }
RETURN a + b + c + d AS violationCount;
