// Q19 rules outside what shacl2cypher compiles. Returns the violation count:
//  - no node or relationship stores a Q19 answer field (pair state, same-network flag, path or step count, connectivity before subdivision,
//    cut-crossing flag, component id, stage precision, probability or confidence, evaluated or provisional flag);
//  - no Landlord, OperationalNetwork, OwnerPortfolio or Lot stores a status (pair state and absence are computed or kept as the two BOR absence properties).
// Fast path: property-key tokens come from the catalog, so the full scans run only for a key that exists in the database.
CALL () { CALL db.propertyKeys() YIELD propertyKey WHERE propertyKey IN ['pairState', 'pairLayerState', 'sameNetwork', 'samePortfolio', 'steps', 'pathLength', 'connected', 'crossesCut', 'componentId', 'precision', 'stagePrecision', 'probability', 'confidence', 'evaluated', 'provisional'] RETURN collect(propertyKey) AS ks }
CALL (ks) { UNWIND ks AS k MATCH (n) WHERE n[k] IS NOT NULL RETURN count(n) AS a }
CALL (ks) { UNWIND ks AS k MATCH ()-[r]->() WHERE r[k] IS NOT NULL RETURN count(r) AS b }
CALL () { MATCH (n) WHERE (n:Landlord OR n:OperationalNetwork OR n:OwnerPortfolio OR n:Lot) AND n.status IS NOT NULL RETURN count(n) AS c }
CALL () { MATCH ()-[r]->() WHERE type(r) STARTS WITH 'CONNECTED_BY' AND r.status IS NOT NULL RETURN count(r) AS d }
RETURN a + b + c + d AS violationCount;
