// Q8.2: which lots, buildings and residential units are in this Operational Network?
// Counting units differ and are never mixed: lots (BBL), buildings (distinct BIN recorded by HPD on those lots),
// and residential units (PLUTO unitsRes summed over the lots). unitsRes is lot-wide, never summed across BINs.
// lotsMissingUnits: lots with no PLUTO unit count, so units is a partial total when it is above 0.
MATCH (n:OperationalNetwork {groupId: $groupId})<-[:IN_NETWORK]-(l:Lot)
WITH n, collect(l) AS lots
UNWIND lots AS lot
OPTIONAL MATCH (lot)-[:HAS_BUILDING]->(b:Building)
WITH n, lots, collect(DISTINCT b) AS buildings
RETURN n.groupId AS groupId, n.split AS split, size(lots) AS lots, size(buildings) AS buildings,
       reduce(u = 0, x IN lots | u + coalesce(x.unitsRes, 0)) AS units,
       size([x IN lots WHERE x.unitsRes IS NULL]) AS lotsMissingUnits;
