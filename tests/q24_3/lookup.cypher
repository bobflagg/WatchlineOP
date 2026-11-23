// Q24.3: which other names look like this entity name, as leads separate from the matches of Q24.1? $key is the given name after rule N3;
// $core is the key without trailing legal-form words (LLC, INC, CORP, CO, LP, LTD, INCORPORATED, CORPORATION, COMPANY), from compare._core.
// A candidate is a different name key equal to the core or starting with the core and a space: a legal-suffix variant or a longer name. The caller
// classifies each candidate with compare.entity_name_comparison and drops "different". A spacing variant (S1), an abbreviation (AB1) or a misspelling
// does not start with the core and is not found: a documented limit. DOS records are not searched (only name-matched records are loaded).
// Names are shown with their record counts (HPD: distinct registrations; deeds: distinct deeds). Every row is a lead, never a link.
CALL () {
  MATCH (c:Contact) WHERE (c.nameKey = $core OR c.nameKey STARTS WITH $core + ' ') AND c.nameKey <> $key
  OPTIONAL MATCH (r:Registration)-[:HAS_CONTACT]->(c)
  RETURN 'hpd_contacts' AS source, c.nameKey AS nameKey, count(DISTINCT r) AS records
  UNION
  MATCH (g:Grantee) WHERE (g.nameKey = $core OR g.nameKey STARTS WITH $core + ' ') AND g.nameKey <> $key
  OPTIONAL MATCH (d:Deed)-[:HAS_GRANTEE]->(g)
  RETURN 'acris_parties' AS source, g.nameKey AS nameKey, count(DISTINCT d) AS records
}
RETURN source, nameKey, sum(records) AS records ORDER BY source, nameKey LIMIT 200;
