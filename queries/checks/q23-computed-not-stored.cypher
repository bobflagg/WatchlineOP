// Q23 rules outside what shacl2cypher compiles. Returns the violation count:
//  - no node or relationship stores a Q23 answer field (footprint count, layer state, commercial-service flag or operator verdict);
//  - no Contact, Registration, Building, Lot or mask node stores a status (a footprint is a lead, never a stored verdict);
//  - no relationship of type MANAGED_BY, MANAGES, SAME_AGENT or SAME_OWNER exists, and no node carries an AgentFootprint or ManagingAgent label
//    (shared management is a record link, not a grouping and not ownership: the footprint is computed at answer time).
// Fast path: property-key, label and type tokens come from the catalog, so the full scans run only for a name that exists in the database.
CALL () { CALL db.propertyKeys() YIELD propertyKey WHERE propertyKey IN ['agentFootprint', 'footprintLots', 'footprintBuildings', 'footprintRegistrations', 'layerState', 'networkSame', 'networkOther', 'networkNone', 'portfolioSame', 'portfolioOther', 'portfolioNone', 'commercialService', 'isCommercialService', 'operatorVerdict', 'agentKind', 'agentBuildings'] RETURN collect(propertyKey) AS ks }
CALL (ks) { UNWIND ks AS k MATCH (n) WHERE n[k] IS NOT NULL RETURN count(n) AS a }
CALL (ks) { UNWIND ks AS k MATCH ()-[r]->() WHERE r[k] IS NOT NULL RETURN count(r) AS b }
CALL () { UNWIND ['Contact', 'Registration', 'Building', 'Lot', 'NetworkMaskedAddress', 'PortfolioMaskedAddress'] AS l CALL (l) { MATCH (n) WHERE n:$(l) AND n.status IS NOT NULL RETURN count(n) AS k } RETURN sum(k) AS c }
CALL () { CALL db.relationshipTypes() YIELD relationshipType WHERE relationshipType IN ['MANAGED_BY', 'MANAGES', 'SAME_AGENT', 'SAME_OWNER'] RETURN count(relationshipType) AS d }
CALL () { CALL db.labels() YIELD label WHERE label IN ['AgentFootprint', 'ManagingAgent'] RETURN count(label) AS e }
RETURN a + b + c + d + e AS violationCount;
