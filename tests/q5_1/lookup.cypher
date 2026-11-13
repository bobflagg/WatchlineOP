// Q5.1: which NY DOS active-entity records carry this owner entity's name? Candidates are all records whose name key (rule N3) equals
// the input's key; none is chosen. $key is compare.n3($name). The agreement outcome and rule are computed with compare.dos_name_agreement.
// No candidates means "no record in the active-entity snapshot", with the spellings tried (the answer contract adds that).
MATCH (e:DosEntity {nameKey: $key})
RETURN e.dosId AS dosId, e.name AS name, e.entityType AS entityType, e.jurisdiction AS jurisdiction, toString(e.filingDate) AS filingDate
ORDER BY dosId;
