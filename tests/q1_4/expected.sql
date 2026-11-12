-- Q1.4 expected characteristics for one lot, from the frozen source (PLUTO 26v1). Parameter: %(bbl)s.
-- No row means the lot is not in PLUTO, so every characteristic is absent.
-- PLUTO yearbuilt 0 means unknown (absent); a blank building class is absent; units and assessed value keep 0.
SELECT nullif(yearbuilt, 0)           AS "yearBuilt",
       nullif(btrim(bldgclass), '')   AS "buildingClass",
       unitsres                       AS "unitsRes",
       assesstot                      AS "assessedTotal"
FROM pluto_latest
WHERE bbl = %(bbl)s;
