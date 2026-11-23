// Q14.2: which HPD registrations of this lot's buildings are in force on a date, and who are their owner contacts? $bbl is the lot, $date the date.
// Every registration of the lot's buildings is returned with a status, none is chosen. status: registered-later (last registered after the date),
// ended (end before the date), undated (no last registered date), end-unknown (HPD rows disagree on the end), in-force (last registered on or before
// the date and end on or after it). HPD keeps one row per registration with only the last registration date and an end date: the records are today's
// version of the past, there is no period start, and an earlier filing of the same registration is gone. In force is HPD's registration period,
// not a finding that the owner was responsible. Owner contacts are the three owner types; a person's name is never repeated outside the answer.
MATCH (l:Lot {bbl: $bbl})-[:HAS_BUILDING]->(b:Building)-[h:HAS_REGISTRATION]->(r:Registration)
WITH l, b, h, r,
     CASE WHEN h.lastRegistered IS NOT NULL AND h.lastRegistered > date($date) THEN 'registered-later'
          WHEN h.registrationEnd IS NOT NULL AND h.registrationEnd < date($date) THEN 'ended'
          WHEN h.lastRegistered IS NULL THEN 'undated'
          WHEN h.registrationEnd IS NULL THEN 'end-unknown'
          ELSE 'in-force' END AS status
CALL (r) {
  OPTIONAL MATCH (r)-[:HAS_CONTACT]->(c:Contact) WHERE c.contactType IN ['CorporateOwner', 'IndividualOwner', 'JointOwner']
  RETURN collect(CASE WHEN c IS NULL THEN null ELSE c {.contactType, .corporationName, .nameKey, .personName} END) AS owners
}
RETURN b.bin AS bin, r.registrationId AS registrationId, h.lastRegistered AS lastRegistered, h.registrationEnd AS registrationEnd, status, owners
ORDER BY bin, registrationId;
