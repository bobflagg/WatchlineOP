// Q21 rules outside what shacl2cypher compiles. Returns the violation count:
//  - no node or relationship stores a Q21 answer field (open violation count, count by class, rate per unit, rank, concentration share, top-lot count);
//  - no Lot, Building, OperationalNetwork or OwnerPortfolio stores a status (the Violation's own status is the only one);
//  - no node carries a Ranking or Concentration label (the ranking and the share are computed at answer time).
// A label scan per label, never an OR of labels (that would scan every node, including the 1.9M violations).
// Fast path: property-key and label tokens come from the catalog, so the full scans run only for a key or label that exists in the database.
CALL () { CALL db.propertyKeys() YIELD propertyKey WHERE propertyKey IN ['openViolations', 'openCount', 'open', 'classA', 'classB', 'classC', 'classI', 'violationRate', 'openRate', 'rate', 'rank', 'topShare', 'concentration', 'sumOpen', 'topOpen', 'distinctOpen', 'lotsWithOpen'] RETURN collect(propertyKey) AS ks }
CALL (ks) { UNWIND ks AS k MATCH (n) WHERE n[k] IS NOT NULL RETURN count(n) AS a }
CALL (ks) { UNWIND ks AS k MATCH ()-[r]->() WHERE r[k] IS NOT NULL RETURN count(r) AS b }
CALL () { UNWIND ['Lot', 'Building', 'OperationalNetwork', 'OwnerPortfolio'] AS l CALL (l) { MATCH (n) WHERE n:$(l) AND n.status IS NOT NULL RETURN count(n) AS k } RETURN sum(k) AS c }
CALL () { CALL db.labels() YIELD label WHERE label IN ['Ranking', 'Concentration', 'LotViolationRanking'] RETURN count(label) AS d }
RETURN a + b + c + d AS violationCount;
