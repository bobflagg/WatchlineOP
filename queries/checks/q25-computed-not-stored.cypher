// Q25 rules outside what shacl2cypher compiles. Returns the violation count:
//  - no node or relationship stores a Q25 answer field (registry outcome, registry name, filing id, registry status, foreign filing date or foreign agent);
//  - no node carries a RegistrySearch, RegistryFinding or ForeignEntity label (registry findings are session evidence, not graph facts);
//  - no DosEntity stores a status (a registry status is reported with its retrieval date, never stored on a recorded entity).
// Fast path: property-key and label tokens come from the catalog, so the full scans run only for a name that exists in the database.
CALL () { CALL db.propertyKeys() YIELD propertyKey WHERE propertyKey IN ['registryOutcome', 'registryName', 'filingId', 'registryStatus', 'foreignFilingDate', 'foreignAgent'] RETURN collect(propertyKey) AS ks }
CALL (ks) { UNWIND ks AS k MATCH (n) WHERE n[k] IS NOT NULL RETURN count(n) AS a }
CALL (ks) { UNWIND ks AS k MATCH ()-[r]->() WHERE r[k] IS NOT NULL RETURN count(r) AS b }
CALL () { CALL db.labels() YIELD label WHERE label IN ['RegistrySearch', 'RegistryFinding', 'ForeignEntity'] RETURN count(label) AS c }
CALL () { MATCH (n:DosEntity) WHERE n.status IS NOT NULL RETURN count(n) AS d }
RETURN a + b + c + d AS violationCount;
