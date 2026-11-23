// Q22.2: records naming an entity, per name key ($key is compare.n3 of the name; the lead is a name match, never a link).
// Run once per name. The agent intersects the two result sets: a lot, registration or document in both is a joining record.
// A shared mailing address is returned as a lead only; masked or mail-drop addresses support no identity (Q6 tools decide).
CALL () {
  MATCH (l:Lot)-[:HAS_DEED]->(:Deed)-[:HAS_GRANTEE|HAS_GRANTOR]->(p {nameKey: $key})
  RETURN 'deed-party' AS kind, l.bbl AS ref, null AS address
  UNION
  MATCH (l:Lot)-[:HAS_BUILDING]->(:Building)-[:HAS_REGISTRATION]->(r:Registration)-[:HAS_CONTACT]->(c:Contact {nameKey: $key})
  RETURN 'registration-contact' AS kind, l.bbl AS ref, c.mailingAddress AS address
  UNION
  MATCH (d:Document)-[:HAS_PARTY]->(:DocumentParty {nameKey: $key})
  RETURN 'document-party' AS kind, d.documentId AS ref, null AS address
  UNION
  MATCH (e:DosEntity {nameKey: $key})
  RETURN 'dos-entity' AS kind, toString(e.dosId) AS ref, e.processAddress AS address
}
RETURN DISTINCT kind, ref, address ORDER BY kind, ref;
