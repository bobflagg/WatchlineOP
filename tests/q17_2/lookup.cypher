// Q17.2: has every registration of this lot ended before the as-of date? $bbl is the lot, $asOf the registration data's snapshot date ('YYYY-MM-DD').
// lapsed: holds when the lot has registrations and every end date is before $asOf; does-not-hold when any registration has not ended;
// cannot-tell when the lot has no registration or an end date is absent (HPD's rows disagree) and none is running. Each registration is listed
// with its dates. The last registration date is not used. A lapsed period is HPD's record, not a ruling that the owner breaks the rules.
MATCH (l:Lot {bbl: $bbl})
CALL (l) {
  OPTIONAL MATCH (l)-[:HAS_BUILDING]->(b:Building)-[h:HAS_REGISTRATION]->(r:Registration)
  WITH b, r, h ORDER BY b.bin, r.registrationId
  RETURN collect(CASE WHEN r IS NULL THEN null ELSE {bin: b.bin, registrationId: r.registrationId, lastRegistered: h.lastRegistered, registrationEnd: h.registrationEnd} END) AS regs
}
WITH l, [x IN regs WHERE x IS NOT NULL] AS regs
RETURN l.bbl AS bbl, regs AS registrations,
       CASE WHEN size(regs) = 0 THEN 'cannot-tell'
            WHEN any(x IN regs WHERE x.registrationEnd >= date($asOf)) THEN 'does-not-hold'
            WHEN all(x IN regs WHERE x.registrationEnd < date($asOf)) THEN 'holds'
            ELSE 'cannot-tell' END AS lapsed;
