// Q1.2: which buildings are recorded for this tax lot? After the BBL is known:
MATCH (l:Lot {bbl: $bbl})
OPTIONAL MATCH (l)-[:HAS_BUILDING]->(b:Building)
RETURN l.bbl AS bbl, l.plutoNumBuildings AS plutoNumBuildings, collect(b {.bin, .address}) AS buildings;
