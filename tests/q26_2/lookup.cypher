// Q26.2: does the NY DOS active-entity snapshot hold a record for the owner entity of this lot? $bbl is the lot.
// One row per owner name (corporation name, rule N3 key) on the lot's registrations; nameKey and the contact type are null for an owner with no
// corporation name (a person) and the lot returns one row with null contactType when it has no owner contact at all.
// dosRecords counts candidates under that key; 0 is "no record under this spelling" (a Q22 lead, never a finding that the entity does not exist).
// Snapshot date: 2026-07-06.
MATCH (l:Lot {bbl: $bbl})
OPTIONAL MATCH (l)-[:HAS_BUILDING]->(:Building)-[:HAS_REGISTRATION]->(:Registration)-[:HAS_CONTACT]->(c:Contact)
WHERE c.contactType IN ['CorporateOwner', 'IndividualOwner', 'JointOwner']
WITH l, collect(DISTINCT {contactType: c.contactType, corporationName: c.corporationName, nameKey: c.nameKey}) AS owners
UNWIND owners AS o
OPTIONAL MATCH (e:DosEntity {nameKey: o.nameKey})
RETURN l.bbl AS bbl, o.contactType AS contactType, o.corporationName AS corporationName, o.nameKey AS nameKey, count(e) AS dosRecords
ORDER BY corporationName;
