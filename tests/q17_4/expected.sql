-- Q17.4 expected answers: PLUTO's residential unit count and year built against the 3-unit threshold. Independent of the graph.
-- pluto_latest (26v1). unitsres is lot-wide and kept as recorded; 0 means PLUTO records none and null or a lot not in PLUTO is absent.
-- Year built 0 means unknown (absent). The check derives meets-threshold (3 or more), below-threshold (1 or 2) or units-not-recorded (0 or absent).
SELECT unitsres, nullif(yearbuilt, 0) AS year_built FROM pluto_latest WHERE bbl::text = %(bbl)s;
