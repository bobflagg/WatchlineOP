// Q22 rules outside what shacl2cypher compiles. Returns the violation count:
//  - no node or relationship stores a Q22 answer field (entity name outcome, comparison rule, same-entity flag, joining-record count);
//  - no Contact, Grantee, Grantor, DocumentParty or DosEntity stores a status (a name match is a lead, never a stored verdict);
//  - no relationship of type SAME_AS, SAME_ENTITY or MATCHES exists, and no node carries a NameComparison or EntityMatch label
//    (a name match is a lead, not a link: the comparison is computed at answer time).
// Fast path: property-key, label and type tokens come from the catalog, so the full scans run only for a name that exists in the database.
CALL () { CALL db.propertyKeys() YIELD propertyKey WHERE propertyKey IN ['nameOutcome', 'entityNameOutcome', 'nameAgreement', 'comparisonRule', 'matchRule', 'sameEntity', 'sameAs', 'joiningRecords', 'joiningRecordCount'] RETURN collect(propertyKey) AS ks }
CALL (ks) { UNWIND ks AS k MATCH (n) WHERE n[k] IS NOT NULL RETURN count(n) AS a }
CALL (ks) { UNWIND ks AS k MATCH ()-[r]->() WHERE r[k] IS NOT NULL RETURN count(r) AS b }
CALL () { UNWIND ['Contact', 'Grantee', 'Grantor', 'DocumentParty', 'DosEntity'] AS l CALL (l) { MATCH (n) WHERE n:$(l) AND n.status IS NOT NULL RETURN count(n) AS k } RETURN sum(k) AS c }
CALL () { CALL db.relationshipTypes() YIELD relationshipType WHERE relationshipType IN ['SAME_AS', 'SAME_ENTITY', 'MATCHES'] RETURN count(relationshipType) AS d }
CALL () { CALL db.labels() YIELD label WHERE label IN ['NameComparison', 'EntityMatch'] RETURN count(label) AS e }
RETURN a + b + c + d + e AS violationCount;
