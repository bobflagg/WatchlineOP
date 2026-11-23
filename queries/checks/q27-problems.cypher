// Q27 rules outside what shacl2cypher compiles. Returns the violation count:
//  - HAS_PROBLEM starts on a building only (never a lot) and carries no property;
//  - no lot, building, problem or HAS_PROBLEM link stores a computed answer field (counts, period totals, rate, units);
//  - a problem received before the loaded window (2021-01-01) is never present;
//  - a problem node carries only its nine properties, including minorCategory and problemCode (no apartment, unit or space type, anonymity, coordinates, pest kind, complaint status);
//  - a problem whose minor category is PESTS carries one of the seven pest codes (MICE, ROACHES, OTHER, BED BUGS, FLIES, TERMITES, FLEAS).
CALL () { MATCH (s)-[r:HAS_PROBLEM]->() WHERE NOT s:Building OR size(keys(r)) > 0 RETURN count(r) AS a }
CALL () { MATCH (n) WHERE (n:Lot OR n:Building OR n:Problem) AND any(k IN keys(n) WHERE k IN ['problemCount', 'problems', 'openProblems', 'complaintCount', 'byType', 'byCategory', 'complaintRate', 'rate', 'problemsPerUnit', 'pestKind', 'pestCount', 'pestComplaints']) RETURN count(n) AS b }
CALL () { MATCH ()-[r:HAS_PROBLEM]->() WHERE any(k IN keys(r) WHERE k IN ['problemCount', 'byType', 'rate', 'complaintRate']) RETURN count(r) AS c }
CALL () { MATCH (p:Problem) WHERE p.receivedDate < date('2021-01-01') RETURN count(p) AS d }
CALL () { MATCH (p:Problem) WHERE any(k IN keys(p) WHERE NOT k IN ['problemId', 'complaintId', 'problemType', 'majorCategory', 'minorCategory', 'problemCode', 'status', 'receivedDate', 'duplicate']) RETURN count(p) AS e }
CALL () { MATCH (p:Problem) WHERE p.minorCategory = 'PESTS' AND NOT coalesce(p.problemCode, '') IN ['MICE', 'ROACHES', 'OTHER', 'BED BUGS', 'FLIES', 'TERMITES', 'FLEAS'] RETURN count(p) AS f }
RETURN a + b + c + d + e + f AS violationCount;
