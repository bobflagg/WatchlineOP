// Q15 rules outside what shacl2cypher compiles. Returns the violation count:
//  - HAS_VIOLATION starts on a building only (never a lot) and carries no property;
//  - no lot, building, violation or HAS_VIOLATION link stores a computed answer field (counts, oldest open date, rate, units);
//  - a violation node carries only violationId, violationClass, status, inspectionDate and orderNumber (no apartment, description, pest kind, notice date or status detail).
CALL () { MATCH (s)-[r:HAS_VIOLATION]->() WHERE NOT s:Building OR size(keys(r)) > 0 RETURN count(r) AS a }
CALL () { MATCH (n) WHERE (n:Lot OR n:Building OR n:Violation) AND any(k IN keys(n) WHERE k IN ['openCount', 'openViolations', 'violationCount', 'byClass', 'oldestOpen', 'oldestInspection', 'rate', 'openRate', 'violationsPerUnit', 'pestKind', 'pestViolations', 'pestCount']) RETURN count(n) AS b }
CALL () { MATCH ()-[r:HAS_VIOLATION]->() WHERE any(k IN keys(r) WHERE k IN ['openCount', 'byClass', 'oldestOpen', 'rate', 'openRate']) RETURN count(r) AS c }
CALL () { MATCH (v:Violation) WHERE any(k IN keys(v) WHERE NOT k IN ['violationId', 'violationClass', 'status', 'inspectionDate', 'orderNumber']) RETURN count(v) AS d }
RETURN a + b + c + d AS violationCount;
