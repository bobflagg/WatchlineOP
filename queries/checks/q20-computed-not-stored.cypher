// Q20 rules outside what shacl2cypher compiles. Returns the violation count:
//  - no node carries a Dossier, Finding, Claim, Lead, StopReason or BeneficialOwner label (the dossier is assembled at answer time);
//  - no node or relationship stores a lead status, stop reason, claim label, dossier section or ownership conclusion
//    (leadStatus, stopReason, claimLabel, dossier, finding, owner, ownedBy, beneficialOwner);
//  - no Lot, Building, Registration, Contact, Deed, Document, DocumentParty, DosEntity, OperationalNetwork or OwnerPortfolio stores a status.
// Fast path: label and property-key tokens come from the catalog, so the full scans run only for a name that exists in the database.
CALL () { CALL db.labels() YIELD label WHERE label IN ['Dossier', 'Finding', 'Claim', 'Lead', 'StopReason', 'BeneficialOwner'] RETURN collect(label) AS ls }
CALL (ls) { UNWIND ls AS l MATCH (n) WHERE l IN labels(n) RETURN count(n) AS a }
CALL () { CALL db.propertyKeys() YIELD propertyKey WHERE propertyKey IN ['leadStatus', 'stopReason', 'claimLabel', 'dossier', 'finding', 'owner', 'ownedBy', 'beneficialOwner'] RETURN collect(propertyKey) AS ks }
CALL (ks) { UNWIND ks AS k MATCH (n) WHERE n[k] IS NOT NULL RETURN count(n) AS b }
CALL (ks) { UNWIND ks AS k MATCH ()-[r]->() WHERE r[k] IS NOT NULL RETURN count(r) AS c }
CALL () { MATCH (n) WHERE (n:Lot OR n:Building OR n:Registration OR n:Contact OR n:Deed OR n:Document OR n:DocumentParty OR n:DosEntity OR n:OperationalNetwork OR n:OwnerPortfolio) AND n.status IS NOT NULL RETURN count(n) AS d }
RETURN a + b + c + d AS violationCount;
