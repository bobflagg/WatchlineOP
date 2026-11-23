// Q18.2: for each zero-transfer deed on these lots, what supports a restructuring reading independently of any grouping? $bbls are the lots;
// $start and $end are recorded-date bounds or null. Derived (evidence Type II): name and record leads, never a finding. No signal reads
// Operational Network or Owner Portfolio membership, so the grouping is not its own evidence. Signals, all by name key (rule N3):
//  - granteeNamedForLot: a grantee's name starts with the house number of a covered lot's address (a single-purpose naming habit, not proof);
//  - sameName: a grantor and a grantee carry the same name;
//  - followOn: a grantee of this deed is a grantor of another deed on the same lot recorded the same day or later (documents listed, with amount);
//  - granteeRegisteredOwner: a grantee is a current HPD corporate owner of a covered lot (current registration is not historical ownership).
// signals counts the signals that hold. No signal holding means "no independent support found", not a clearance. A buyer with no recorded
// relationship is "no relationship established".
UNWIND $bbls AS bbl
MATCH (l:Lot {bbl: bbl})-[:HAS_DEED]->(d:Deed)
WHERE d.amount = 0 AND NOT d.docType IN ['CORRD', 'CONDEED']
  AND ($start IS NULL OR d.recordedDate >= date($start)) AND ($end IS NULL OR d.recordedDate <= date($end))
WITH d, collect(DISTINCT l) AS lots
CALL (d) { OPTIONAL MATCH (d)-[:HAS_GRANTOR]->(g:Grantor) RETURN collect(DISTINCT g.nameKey) AS grantorKeys }
CALL (d) { OPTIONAL MATCH (d)-[:HAS_GRANTEE]->(g:Grantee) RETURN collect(DISTINCT g.nameKey) AS granteeKeys }
CALL (lots, granteeKeys) {
  UNWIND lots AS l
  OPTIONAL MATCH (l)-[:HAS_BUILDING]->(:Building)-[:HAS_REGISTRATION]->(:Registration)-[:HAS_CONTACT]->(c:Contact {contactType: 'CorporateOwner'})
  WHERE c.nameKey IN granteeKeys
  RETURN collect(DISTINCT c.nameKey) AS ownerMatches
}
CALL (d, lots, granteeKeys) {
  UNWIND lots AS l
  OPTIONAL MATCH (l)-[:HAS_DEED]->(n:Deed)-[:HAS_GRANTOR]->(g:Grantor)
  WHERE n <> d AND n.recordedDate >= d.recordedDate AND g.nameKey IN granteeKeys
  RETURN collect(DISTINCT n {.documentId, .amount, .recordedDate}) AS followOn
}
WITH d, lots, grantorKeys, granteeKeys, ownerMatches, followOn,
     any(l IN lots WHERE any(k IN granteeKeys WHERE k STARTS WITH split(l.address, ' ')[0] + ' ')) AS named,
     any(k IN grantorKeys WHERE k IN granteeKeys) AS same
RETURN d.documentId AS documentId, d.recordedDate AS recordedDate, [l IN lots | l.bbl] AS lots,
       named AS granteeNamedForLot, same AS sameName, size(followOn) > 0 AS hasFollowOn, followOn,
       size(ownerMatches) > 0 AS granteeRegisteredOwner,
       (CASE WHEN named THEN 1 ELSE 0 END) + (CASE WHEN same THEN 1 ELSE 0 END) + (CASE WHEN size(followOn) > 0 THEN 1 ELSE 0 END) + (CASE WHEN size(ownerMatches) > 0 THEN 1 ELSE 0 END) AS signals
ORDER BY recordedDate, documentId;
