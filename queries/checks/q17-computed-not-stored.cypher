// Q17 rules outside what shacl2cypher compiles. Returns the violation count:
//  - no node or relationship stores a Q17 answer field (missing, lapsed, older-than-deed or stale condition, no-usable-registration flag,
//    threshold outcome, unit threshold, as-of date);
//  - no Lot, Building or Registration stores a status (a lapsed or in-force state is computed from the dates), and no HAS_REGISTRATION
//    link stores one (it keeps only lastRegistered and registrationEnd, checked by the Q14 check).
// Fast path: property-key tokens come from the catalog, so the full scans run only for a key that exists in the database.
CALL () { CALL db.propertyKeys() YIELD propertyKey WHERE propertyKey IN ['missing', 'lapsed', 'olderThanDeed', 'stale', 'noUsableRegistration', 'thresholdOutcome', 'meetsThreshold', 'unitThreshold', 'asOf', 'asOfDate'] RETURN collect(propertyKey) AS ks }
CALL (ks) { UNWIND ks AS k MATCH (n) WHERE n[k] IS NOT NULL RETURN count(n) AS a }
CALL (ks) { UNWIND ks AS k MATCH ()-[r]->() WHERE r[k] IS NOT NULL RETURN count(r) AS b }
CALL () { MATCH (n) WHERE (n:Lot OR n:Building OR n:Registration) AND n.status IS NOT NULL RETURN count(n) AS c }
CALL () { MATCH (:Building)-[h:HAS_REGISTRATION]->(:Registration) WHERE h.status IS NOT NULL RETURN count(h) AS d }
RETURN a + b + c + d AS violationCount;
