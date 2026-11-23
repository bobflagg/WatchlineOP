// Q9.2: which lots, buildings and residential units are attributed to this Owner Portfolio?
// Counting units differ and are never mixed: lots (BBL), buildings (distinct BIN recorded by HPD on those lots),
// and residential units (PLUTO unitsRes summed over the lots). unitsRes is lot-wide, never summed across BINs.
// Only rental lots are counted: co-op and condo lots outside the footprint are not members.
// lotsMissingUnits: lots with no PLUTO unit count, so units is a partial total when it is above 0.
MATCH (n:OwnerPortfolio {groupId: $groupId})<-[:IN_PORTFOLIO]-(l:Lot)
WITH n, collect(l) AS lots
UNWIND lots AS lot
OPTIONAL MATCH (lot)-[:HAS_BUILDING]->(b:Building)
WITH n, lots, collect(DISTINCT b) AS buildings
RETURN n.groupId AS groupId, n.composition AS composition, size(lots) AS lots, size(buildings) AS buildings,
       reduce(u = 0, x IN lots | u + coalesce(x.unitsRes, 0)) AS units,
       size([x IN lots WHERE x.unitsRes IS NULL]) AS lotsMissingUnits;
