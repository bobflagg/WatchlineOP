// Q12.3: which deeds on these lots can be attributed to the lot's currently registered owner? $bbls are the lots (one lot, or the lots of an
// Owner Portfolio from Q12.2); $start and $end are recorded-date bounds ('YYYY-MM-DD', inclusive) or null.
// Derived (evidence Type II), a name lead and never a finding of the same party. The current owners of a lot are the HPD CorporateOwner contacts
// of the registrations of its buildings, compared with each grantee and grantor by name key (rule N3). Current registration is not historical
// ownership: an old deed can match the present owner by name only. attributable is true when a grantee or grantor of the deed matches an owner of
// a lot it covers; granteeMatches and grantorMatches name the matching parties. ownerNotComparable is true when the lot has no corporate owner
// (none registered, or only individuals, whose names HPD and ACRIS spell differently): the deed is then not attributable by name, and the answer
// says so. One row per deed and lot, so a multi-lot deed is counted once by documentId.
UNWIND $bbls AS bbl
MATCH (l:Lot {bbl: bbl})
CALL (l) {
  OPTIONAL MATCH (l)-[:HAS_BUILDING]->(:Building)-[:HAS_REGISTRATION]->(:Registration)-[:HAS_CONTACT]->(c:Contact {contactType: 'CorporateOwner'})
  WHERE c.nameKey IS NOT NULL
  RETURN collect(DISTINCT c.nameKey) AS ownerKeys
}
MATCH (l)-[:HAS_DEED]->(d:Deed)
WHERE ($start IS NULL OR d.recordedDate >= date($start)) AND ($end IS NULL OR d.recordedDate <= date($end))
CALL (d, ownerKeys) { OPTIONAL MATCH (d)-[:HAS_GRANTEE]->(g:Grantee) WHERE g.nameKey IN ownerKeys RETURN collect(DISTINCT g.name) AS granteeMatches }
CALL (d, ownerKeys) { OPTIONAL MATCH (d)-[:HAS_GRANTOR]->(g:Grantor) WHERE g.nameKey IN ownerKeys RETURN collect(DISTINCT g.name) AS grantorMatches }
RETURN d.documentId AS documentId, l.bbl AS bbl, size(ownerKeys) AS corporateOwners, size(ownerKeys) = 0 AS ownerNotComparable,
       granteeMatches, grantorMatches, size(granteeMatches) + size(grantorMatches) > 0 AS attributable
ORDER BY documentId, bbl;
