// Q14.3: do the title holders and the registered owners supported for a date coincide? $bbl is the lot, $date the date, $basis as in Q14.1.
// Computed from the Q14.1 deeds and the Q14.2 registrations in force; nothing is stored. relation (a name lead, rule N3, never a finding of the
// same party or of responsibility): no-title-record (no deed on or before the date), no-registration-in-force (no registration in force),
// not-comparable (no corporate owner name, or no grantee name: an individual owner's name is spelled in a different order by HPD and ACRIS),
// coincide (a grantee of a supporting deed equals a corporate owner of a registration in force) or differ. A difference can be a spelling
// difference, so both name lists are returned labelled by source.
MATCH (l:Lot {bbl: $bbl})
CALL (l) {
  OPTIONAL MATCH (l)-[:HAS_DEED]->(d:Deed)
  WITH d, CASE WHEN d IS NULL THEN null WHEN $basis = 'recorded' THEN d.recordedDate ELSE coalesce(d.docDate, d.recordedDate) END AS effDate
  WHERE effDate IS NOT NULL AND effDate <= date($date)
  WITH max(effDate) AS latest, collect({deed: d, eff: effDate}) AS xs
  UNWIND (CASE WHEN latest IS NULL THEN [] ELSE [x IN xs WHERE x.eff = latest] END) AS x
  WITH x.deed AS dd
  OPTIONAL MATCH (dd)-[:HAS_GRANTEE]->(g:Grantee)
  RETURN collect(DISTINCT dd.documentId) AS deeds, collect(DISTINCT g.name) AS granteeNames, collect(DISTINCT g.nameKey) AS granteeKeys
}
CALL (l) {
  OPTIONAL MATCH (l)-[:HAS_BUILDING]->(:Building)-[h:HAS_REGISTRATION]->(r:Registration)
  WHERE h.lastRegistered IS NOT NULL AND h.lastRegistered <= date($date) AND h.registrationEnd IS NOT NULL AND h.registrationEnd >= date($date)
  OPTIONAL MATCH (r)-[:HAS_CONTACT]->(c:Contact {contactType: 'CorporateOwner'})
  RETURN count(DISTINCT r) AS registrationsInForce, collect(DISTINCT c.corporationName) AS ownerNames, collect(DISTINCT c.nameKey) AS ownerKeys
}
WITH deeds, granteeNames, [k IN granteeKeys WHERE k IS NOT NULL] AS granteeKeys, registrationsInForce, ownerNames, [k IN ownerKeys WHERE k IS NOT NULL] AS ownerKeys
RETURN deeds, granteeNames, registrationsInForce, ownerNames,
       CASE WHEN size(deeds) = 0 THEN 'no-title-record'
            WHEN registrationsInForce = 0 THEN 'no-registration-in-force'
            WHEN size(ownerKeys) = 0 OR size(granteeKeys) = 0 THEN 'not-comparable'
            WHEN any(k IN granteeKeys WHERE k IN ownerKeys) THEN 'coincide'
            ELSE 'differ' END AS relation;
