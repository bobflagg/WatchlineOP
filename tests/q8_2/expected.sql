-- Q8.2 expected counts for one network, from the frozen JustFix/WoW snapshot. Independent of the loader.
-- The lots of a network come from the BOR release (group_bbls.csv); the check passes them as %(bbls)s.
-- hpd_registrations (2026-05-29) and pluto_latest (26v1), checked read-only 2026-11-13.
-- verified against the frozen baseline recorded in data/README.md (2026-11-16).
--
-- lots: the number of lots listed. units: PLUTO unitsres summed over the lots that have a value.
-- lots_missing_units: lots with no PLUTO row or a null unitsres. buildings: distinct valid BINs
-- (^[1-5][0-9]{6}$, not ending 000000) registered on those lots.
-- Expected: ON-98617 5 / 5 / 116 / 0; ON-18742 35 / 44 / 466 / 0; ON-675 27 / 28 / 562 / 0; ON-1 2 / 2 / 3 / 0;
--           ON-60782 2 / 2 / 16 / 0; ON-16213 (lot 3022117501 has null unitsres) 2 / 2 / 4 / 1.
WITH l AS (SELECT unnest(%(bbls)s::text[]) AS bbl)
SELECT (SELECT count(*) FROM l) AS lots,
       (SELECT count(DISTINCT r.bin) FROM l JOIN hpd_registrations r ON r.bbl = l.bbl
         WHERE r.bin ~ '^[1-5][0-9]{6}$' AND r.bin !~ '000000$') AS buildings,
       (SELECT coalesce(sum(p.unitsres), 0) FROM l JOIN pluto_latest p ON p.bbl = l.bbl) AS units,
       (SELECT count(*) FROM l LEFT JOIN pluto_latest p ON p.bbl = l.bbl WHERE p.unitsres IS NULL) AS lots_missing_units;
