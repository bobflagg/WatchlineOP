// Q15.2: what is the rate of open violations per residential unit for this building? $bin is the building.
// One row per lot the building sits on. Numerator: the building's open violations (open at the snapshot). Denominator: the lot's PLUTO residential
// units, which are lot-wide. rate is null ("rate unavailable") when unitsRes is absent or 0. Never sum across lots; never return 0 for no units.
MATCH (b:Building {bin: $bin})<-[:HAS_BUILDING]-(l:Lot)
CALL (b) { MATCH (b)-[:HAS_VIOLATION]->(v:Violation {status: 'Open'}) RETURN count(v) AS openViolations }
RETURN l.bbl AS bbl, l.unitsRes AS unitsRes, openViolations,
       CASE WHEN l.unitsRes IS NULL OR l.unitsRes = 0 THEN null ELSE toFloat(openViolations) / l.unitsRes END AS rate
ORDER BY bbl;
