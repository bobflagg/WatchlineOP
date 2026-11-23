// Q26 rules outside what shacl2cypher compiles. Returns the violation count:
//  - no node or relationship stores a source absence (an absence flag, a derived reason for the registration, DOS or violation source, a violation outcome or a not-loaded flag);
//  - no Lot, Building, Contact, DosEntity, OperationalNetwork or OwnerPortfolio stores a status (only the Violation's own status exists);
//  - no node carries a SourceAbsence or Absence label (the absence statement is computed at answer time; only BOR's layer reasons are stored, as Lot.networkAbsence and Lot.portfolioAbsence).
// A label scan per label, never an OR of labels (that would scan every node, including the 1.9M violations).
// Fast path: property-key and label tokens come from the catalog, so the full scans run only for a key or label that exists in the database.
CALL () { CALL db.propertyKeys() YIELD propertyKey WHERE propertyKey IN ['sourceAbsence', 'absenceReason', 'absenceOutcome', 'registrationAbsence', 'dosAbsence', 'violationAbsence', 'violationOutcome', 'notLoaded', 'noRecord', 'dosRecords'] RETURN collect(propertyKey) AS ks }
CALL (ks) { UNWIND ks AS k MATCH (n) WHERE n[k] IS NOT NULL RETURN count(n) AS a }
CALL (ks) { UNWIND ks AS k MATCH ()-[r]->() WHERE r[k] IS NOT NULL RETURN count(r) AS b }
CALL () { UNWIND ['Lot', 'Building', 'Contact', 'DosEntity', 'OperationalNetwork', 'OwnerPortfolio'] AS l CALL (l) { MATCH (n) WHERE n:$(l) AND n.status IS NOT NULL RETURN count(n) AS k } RETURN sum(k) AS c }
CALL () { CALL db.labels() YIELD label WHERE label IN ['SourceAbsence', 'Absence'] RETURN count(label) AS d }
RETURN a + b + c + d AS violationCount;
