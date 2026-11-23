// Q28 rules outside what shacl2cypher compiles. Returns the violation count:
//  - HAS_LITIGATION starts on a building only (never a lot) and carries no property;
//  - no lot, building, case or HAS_LITIGATION link stores a computed answer field (counts, owner match, totals);
//  - a finding date exists only with a harassment finding of After Inquest or After Trial, never with No Harassment (a finding may lack a date: allowed; a missing finding is treated as none);
//  - respondentKeys is a non-empty list of strings and exists only with a respondent; a respondent is never an empty string;
//  - a case node carries only its ten properties (no address, coordinates, judgement amount or respondent role).
CALL () { MATCH (s)-[r:HAS_LITIGATION]->() WHERE NOT s:Building OR size(keys(r)) > 0 RETURN count(r) AS a }
CALL () { MATCH (n) WHERE (n:Lot OR n:Building OR n:Litigation) AND any(k IN keys(n) WHERE k IN ['litigationCount', 'cases', 'openCases', 'byType', 'byStatus', 'respondentMatch', 'ownerMatch', 'matchesOwner', 'harassmentCount']) RETURN count(n) AS b }
CALL () { MATCH ()-[r:HAS_LITIGATION]->() WHERE any(k IN keys(r) WHERE k IN ['caseCount', 'byType', 'ownerMatch']) RETURN count(r) AS c }
CALL () { MATCH (c:Litigation) WHERE c.findingDate IS NOT NULL AND NOT coalesce(c.harassmentFinding, '') IN ['After Inquest', 'After Trial'] RETURN count(c) AS d }
CALL () { MATCH (c:Litigation) WHERE c.respondentKeys IS NOT NULL AND (c.respondent IS NULL OR size(c.respondentKeys) = 0 OR any(k IN c.respondentKeys WHERE k IS NULL OR k = '')) OR c.respondent = '' RETURN count(c) AS e }
CALL () { MATCH (c:Litigation) WHERE any(k IN keys(c) WHERE NOT k IN ['litigationId', 'caseType', 'caseOpenDate', 'caseStatus', 'openJudgement', 'harassmentFinding', 'findingDate', 'penalty', 'respondent', 'respondentKeys']) RETURN count(c) AS f }
RETURN a + b + c + d + e + f AS violationCount;
