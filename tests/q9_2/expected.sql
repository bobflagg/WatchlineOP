-- Q9.2 expected counts for one Owner Portfolio, from the frozen JustFix/WoW snapshot. Independent of the loader.
-- The rental lots of a portfolio come from the BOR release (group_bbls.csv, rental true); the check passes them as %(bbls)s.
-- hpd_registrations (2026-05-29) and pluto_latest (26v1), checked read-only 2026-11-13.
-- verified against the frozen baseline recorded in data/README.md (2026-11-16).
--
-- lots: the number of lots listed. units: PLUTO unitsres summed over the lots that have a value.
-- lots_missing_units: lots with no PLUTO row or a null unitsres. buildings: distinct valid BINs
-- (^[1-5][0-9]{6}$, not ending 000000) registered on those lots.
-- Expected: OP-98617 5 / 5 / 116 / 0; OP-53559 33 / 42 / 454 / 0; OP-84986 6 / 6 / 105 / 0; OP-5346 4 / 4 / 12 / 0;
--           OP-10201 2 / 2 / 6 / 0; OP-100619 (its co-op lot is outside the footprint) 1 / 1 / 3 / 0.
WITH l AS (SELECT unnest(%(bbls)s::text[]) AS bbl)
SELECT (SELECT count(*) FROM l) AS lots,
       (SELECT count(DISTINCT r.bin) FROM l JOIN hpd_registrations r ON r.bbl = l.bbl
         WHERE r.bin ~ '^[1-5][0-9]{6}$' AND r.bin !~ '000000$') AS buildings,
       (SELECT coalesce(sum(p.unitsres), 0) FROM l JOIN pluto_latest p ON p.bbl = l.bbl) AS units,
       (SELECT count(*) FROM l LEFT JOIN pluto_latest p ON p.bbl = l.bbl WHERE p.unitsres IS NULL) AS lots_missing_units;
