// Q27.2: what is the rate of complaint problems per residential unit for this building in a period? $bin is the building; $start, $end are dates.
// One row per lot the building sits on. Numerator: the building's problems received in the period (loaded window starts 2021-01-01). Denominator: the lot's
// PLUTO residential units, which are lot-wide. rate is over the whole period, not annualized, and is null ("rate unavailable") when unitsRes is absent or 0.
// Never sum across lots; never return 0 for no units.
MATCH (b:Building {bin: $bin})<-[:HAS_BUILDING]-(l:Lot)
CALL (b) { MATCH (b)-[:HAS_PROBLEM]->(p:Problem) WHERE p.receivedDate >= date($start) AND p.receivedDate <= date($end) RETURN count(p) AS problems }
RETURN l.bbl AS bbl, l.unitsRes AS unitsRes, problems,
       CASE WHEN l.unitsRes IS NULL OR l.unitsRes = 0 THEN null ELSE toFloat(problems) / l.unitsRes END AS rate
ORDER BY bbl;
