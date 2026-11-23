// Q18 rules outside what shacl2cypher compiles. Returns the violation count:
//  - no node or relationship stores a Q18 answer field (deed classification, zero-transfer or correction flag, restructuring verdict or signal,
//    signal count, grantee-named-for-lot, same-name, follow-on or registered-owner signal);
//  - no Deed, Grantor or Grantee stores a status (a classification is computed from the type and the recorded amount).
// Fast path: property-key tokens come from the catalog, so the full scans run only for a key that exists in the database.
CALL () { CALL db.propertyKeys() YIELD propertyKey WHERE propertyKey IN ['classification', 'deedClassification', 'zeroTransfer', 'restructuring', 'restructuringSignal', 'signals', 'signalCount', 'granteeNamedForLot', 'sameName', 'hasFollowOn', 'followOn', 'granteeRegisteredOwner', 'priced', 'correction'] RETURN collect(propertyKey) AS ks }
CALL (ks) { UNWIND ks AS k MATCH (n) WHERE n[k] IS NOT NULL RETURN count(n) AS a }
CALL (ks) { UNWIND ks AS k MATCH ()-[r]->() WHERE r[k] IS NOT NULL RETURN count(r) AS b }
CALL () { MATCH (n) WHERE (n:Deed OR n:Grantor OR n:Grantee) AND n.status IS NOT NULL RETURN count(n) AS c }
RETURN a + b + c AS violationCount;
