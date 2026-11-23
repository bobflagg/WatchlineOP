// Q17.1: is this lot's registration missing? $bbl is the lot. No row means the lot is not in the graph (outside the rental scope: unregistered
// with under 3 units), which the answer says. missing: holds when the registration data has no row for the lot, does-not-hold otherwise. It is the
// dataset that has no registration, not a ruling that none exists; a new building can be unregistered for a legitimate reason.
// noUsableRegistration: the lot has rows but none is a usable registration (placeholder id or BIN), so lapsed and stale are cannot-tell.
// registrations and registeredBuildings come from the registration records; plutoNumBuildings is PLUTO's count, which differs on about 27% of lots.
MATCH (l:Lot {bbl: $bbl})
CALL (l) {
  OPTIONAL MATCH (l)-[:HAS_BUILDING]->(b:Building)-[h:HAS_REGISTRATION]->(:Registration)
  RETURN count(h) AS registrations, count(DISTINCT b) AS registeredBuildings
}
RETURN l.bbl AS bbl, CASE WHEN l.hpdRegistered THEN 'does-not-hold' ELSE 'holds' END AS missing, l.hpdRegistered AS hpdRegistered,
       l.hpdRegistered AND registrations = 0 AS noUsableRegistration, registrations, registeredBuildings, l.plutoNumBuildings AS plutoNumBuildings;
