// Q24 rules outside what shacl2cypher compiles. Returns the violation count:
//  - no node or relationship stores a Q24 answer field (match basis, near-name kind, lead flag, name-search outcome, person key or match count);
//  - no Contact, Grantee, Grantor or DosEntity stores a status (a name match is a lead, never a stored verdict);
//  - no relationship of type SAME_PERSON, NAME_MATCH or NEAR_MATCH exists, and no node carries a NameSearch, NameMatch or Lead label
//    (a name match is a lead, not a link: the search is computed at answer time).
// Fast path: property-key, label and type tokens come from the catalog, so the full scans run only for a name that exists in the database.
CALL () { CALL db.propertyKeys() YIELD propertyKey WHERE propertyKey IN ['matchBasis', 'nameBasis', 'nearKind', 'leadKind', 'isLead', 'searchOutcome', 'personKey', 'matchCount', 'nameMatches', 'reversedName'] RETURN collect(propertyKey) AS ks }
CALL (ks) { UNWIND ks AS k MATCH (n) WHERE n[k] IS NOT NULL RETURN count(n) AS a }
CALL (ks) { UNWIND ks AS k MATCH ()-[r]->() WHERE r[k] IS NOT NULL RETURN count(r) AS b }
CALL () { UNWIND ['Contact', 'Grantee', 'Grantor', 'DosEntity'] AS l CALL (l) { MATCH (n) WHERE n:$(l) AND n.status IS NOT NULL RETURN count(n) AS k } RETURN sum(k) AS c }
CALL () { CALL db.relationshipTypes() YIELD relationshipType WHERE relationshipType IN ['SAME_PERSON', 'NAME_MATCH', 'NEAR_MATCH'] RETURN count(relationshipType) AS d }
CALL () { CALL db.labels() YIELD label WHERE label IN ['NameSearch', 'NameMatch', 'Lead'] RETURN count(label) AS e }
RETURN a + b + c + d + e AS violationCount;
