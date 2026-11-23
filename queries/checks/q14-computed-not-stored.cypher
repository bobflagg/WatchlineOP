// Q14 rules outside what shacl2cypher compiles. Returns the violation count:
//  - no node stores a computed answer field of Q14 (supporting-deed flag, basis, effective date, registration status, in-force flag, title and registration relation);
//  - no HAS_DEED, HAS_GRANTEE, HAS_REGISTRATION or HAS_CONTACT relationship stores one either (HAS_REGISTRATION keeps only lastRegistered and registrationEnd);
//  - (the 'no Violation node' rule was dropped 2026-11-18 when Q15 loaded violations; the violation date stays an input).
// Speed (2026-11-18): property predicates are written out instead of `any(k IN keys(n) ...)`, which built a key list per element.
CALL () { MATCH (n:Lot|Building|Deed|Grantee|Registration|Contact) WHERE n.supporting IS NOT NULL OR n.basis IS NOT NULL OR n.effDate IS NOT NULL OR n.recordedAfterDate IS NOT NULL OR n.confirmatory IS NOT NULL OR n.docDateAbsent IS NOT NULL OR n.status IS NOT NULL OR n.inForce IS NOT NULL OR n.relation IS NOT NULL OR n.titleHolder IS NOT NULL OR n.registeredOwner IS NOT NULL RETURN count(n) AS a }
CALL () { MATCH ()-[r:HAS_DEED|HAS_GRANTEE|HAS_REGISTRATION|HAS_CONTACT]->() WHERE r.supporting IS NOT NULL OR r.basis IS NOT NULL OR r.effDate IS NOT NULL OR r.recordedAfterDate IS NOT NULL OR r.confirmatory IS NOT NULL OR r.docDateAbsent IS NOT NULL OR r.status IS NOT NULL OR r.inForce IS NOT NULL OR r.relation IS NOT NULL OR r.titleHolder IS NOT NULL OR r.registeredOwner IS NOT NULL RETURN count(r) AS b }
CALL () { MATCH (r:Registration) WHERE r.lastRegistered IS NOT NULL OR r.registrationEnd IS NOT NULL RETURN count(r) AS c }
CALL () { MATCH ()-[h:HAS_REGISTRATION]->() WHERE any(k IN keys(h) WHERE NOT k IN ['lastRegistered', 'registrationEnd']) RETURN count(h) AS d }
RETURN a + b + c + d AS violationCount;
