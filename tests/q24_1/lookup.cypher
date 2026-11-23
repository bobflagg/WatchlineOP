// Q24.1: which records carry this entity name, in what role, on which registration, deed or DOS record, and for which building and lot?
// $key is the given name after rule N3 (src/watchline/compare.py n3): uppercase, no periods or apostrophes, commas to spaces, single spaces.
// Found by name only: every row is a lead, never a stored link. The basis (exact or normalized) is decided by the caller from `name`
// against the name as given. A role is as recorded: a name in a role is not a finding about ownership. DOS records are in the graph only when
// their name equals an HPD owner or deed grantee name, so no DOS row means "no record in the loaded DOS scope", not "no filing".
CALL () {
  MATCH (c:Contact {nameKey: $key})<-[:HAS_CONTACT]-(r:Registration)
  OPTIONAL MATCH (b:Building)-[:HAS_REGISTRATION]->(r)
  OPTIONAL MATCH (l:Lot)-[:HAS_BUILDING]->(b)
  RETURN 'hpd_contacts' AS source, c.contactType AS role, c.corporationName AS name, toString(r.registrationId) AS ref, b.bin AS bin, l.bbl AS bbl
  UNION
  MATCH (l:Lot)-[:HAS_DEED]->(d:Deed)-[:HAS_GRANTEE]->(g:Grantee {nameKey: $key})
  RETURN 'acris_parties' AS source, 'grantee' AS role, g.name AS name, d.documentId AS ref, null AS bin, l.bbl AS bbl
  UNION
  MATCH (l:Lot)-[:HAS_DEED]->(d:Deed)-[:HAS_GRANTOR]->(g:Grantor {nameKey: $key})
  RETURN 'acris_parties' AS source, 'grantor' AS role, g.name AS name, d.documentId AS ref, null AS bin, l.bbl AS bbl
  UNION
  MATCH (e:DosEntity {nameKey: $key})
  RETURN 'nys_corporations' AS source, 'filed entity' AS role, e.name AS name, toString(e.dosId) AS ref, null AS bin, null AS bbl
}
RETURN DISTINCT source, role, name, ref, bin, bbl ORDER BY source, role, ref, bbl, bin;
