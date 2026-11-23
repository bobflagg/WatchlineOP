// Q12 rules outside what shacl2cypher compiles. Returns the violation count:
//  - a grantor or grantee has a nameKey exactly when its name holds something besides periods, commas, apostrophes and spaces;
//  - a nameKey is rule N3 of the name: upper case, no periods or apostrophes, commas as spaces, single spaces, trimmed;
//  - no node or relationship stores a not-a-sale flag, an attribution or a count of deeds.
// Speed (2026-11-18): property predicates are written out and scoped by label or relationship type; `any(k IN keys(n) ...)` over every node and
// relationship built a key list per element. The label and type lists below are every label and type in the graph; add a new one here.
CALL () { MATCH (p:Grantor|Grantee) WHERE p.name IS NOT NULL AND p.nameKey IS NULL
                AND trim(replace(replace(replace(p.name, '.', ''), ',', ''), "'", '')) <> '' RETURN count(p) AS a }
CALL () { MATCH (p:Grantor|Grantee) WHERE p.nameKey IS NOT NULL AND p.name IS NULL RETURN count(p) AS b }
CALL () { MATCH (p:Grantor|Grantee) WHERE p.nameKey IS NOT NULL
                AND (p.nameKey <> toUpper(p.nameKey) OR p.nameKey CONTAINS '.' OR p.nameKey CONTAINS ',' OR p.nameKey CONTAINS "'"
                     OR p.nameKey CONTAINS '  ' OR p.nameKey <> trim(p.nameKey) OR p.nameKey = '') RETURN count(p) AS c }
CALL () { MATCH (n:Lot|Building|Registration|Deed|Grantee|DosEntity|OperationalNetwork|Landlord|OwnerPortfolio|NetworkMaskedAddress|MailDropAddress|PortfolioMaskedAddress|Contact|Document|DocumentParty|Grantor|Violation) WHERE n.notSale IS NOT NULL OR n.attributable IS NOT NULL OR n.deedCount IS NOT NULL OR n.notSaleCount IS NOT NULL RETURN count(n) AS d }
CALL () { MATCH ()-[r:HAS_BUILDING|HAS_REGISTRATION|HAS_DEED|HAS_GRANTEE|IN_NETWORK|COVERS|IN_PORTFOLIO|CONNECTED_BY_IDENTITY|CONNECTED_BY_DEED|CONNECTED_BY_NAME|CONNECTED_BY_ADDRESS|ANCHORED_BY|HAS_CONTACT|BASED_ON_CONTACT|HAS_PARTY|HAS_GRANTOR|HAS_FINANCING_DOCUMENT|HAS_VIOLATION]->() WHERE r.notSale IS NOT NULL OR r.attributable IS NOT NULL OR r.deedCount IS NOT NULL OR r.notSaleCount IS NOT NULL RETURN count(r) AS e }
RETURN a + b + c + d + e AS violationCount;
