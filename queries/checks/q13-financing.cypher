// Q13 rules outside what shacl2cypher compiles. Returns the violation count:
//  - a financing document (target of HAS_FINANCING_DOCUMENT) has a documentType of MTGE, ASST, SAT, AGMT, AL&R, TL&R or SAGE;
//  - it names at least one party, and its recorded date is a date when present (absent stays absent);
//  - HAS_FINANCING_DOCUMENT starts on a lot only and carries no property;
//  - no lot, document, party, financing link or party link stores a kind, description, count by kind, other-lot count or outstanding-loan flag (computed at answer time);
//  - a party of a document loaded only by scope F carries no hub count (hub counts belong to scopes C and M).
// Speed (2026-11-18): property predicates are written out instead of `any(k IN keys(n) ...)`, which built a key list per element.
CALL () { MATCH (:Lot)-[:HAS_FINANCING_DOCUMENT]->(d:Document) WHERE NOT d.docType IN ['MTGE', 'ASST', 'SAT', 'AGMT', 'AL&R', 'TL&R', 'SAGE'] RETURN count(DISTINCT d) AS a }
CALL () { MATCH (:Lot)-[:HAS_FINANCING_DOCUMENT]->(d:Document) WHERE NOT EXISTS { (d)-[:HAS_PARTY]->(:DocumentParty) } RETURN count(DISTINCT d) AS b }
CALL () { MATCH (s)-[r:HAS_FINANCING_DOCUMENT]->() WHERE NOT s:Lot OR size(keys(r)) > 0 RETURN count(r) AS c }
CALL () { MATCH (n:Lot|Document|DocumentParty) WHERE n.kind IS NOT NULL OR n.description IS NOT NULL OR n.byKind IS NOT NULL OR n.otherLots IS NOT NULL OR n.outstanding IS NOT NULL OR n.financingCount IS NOT NULL RETURN count(n) AS d }
CALL () { MATCH ()-[r:HAS_FINANCING_DOCUMENT|HAS_PARTY]->() WHERE r.kind IS NOT NULL OR r.description IS NOT NULL OR r.byKind IS NOT NULL OR r.otherLots IS NOT NULL OR r.outstanding IS NOT NULL OR r.financingCount IS NOT NULL RETURN count(r) AS e }
CALL () { MATCH (d:Document)-[:HAS_PARTY]->(p:DocumentParty) WHERE (p.addressNames IS NOT NULL OR p.addressDocuments IS NOT NULL) AND p.mailingAddress IS NULL RETURN count(p) AS f }
RETURN a + b + c + d + e + f AS violationCount;
