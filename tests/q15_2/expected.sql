-- Q15.2 expected answers: open violations per residential unit for a building. Independent of the graph.
-- hpd_violations, hpd_registrations, pluto_latest 26v1 (frozen baseline, data/README.md).
-- Rules (decision 2026-11-18): numerator = open violations of the BIN whose own BBL is HPD-registered (the Q15.1 load scope); denominator = PLUTO unitsres of each lot the BIN is registered on
-- (lot-wide, not the building's own units). A BIN on several lots gets one row per lot, never a sum. unitsres 0 or absent (lot not in PLUTO)
-- gives "rate unavailable", never 0 or infinity. rate = open / unitsres, shown as recorded arithmetic.
-- Expected for BIN 3013901: lot 3008070024, 32 units, 4 open, rate 0.125. BIN 1052551: lot 1016650047, 0 units, 6 open, unavailable.
-- BIN 3343256: lot 3042719001 not in PLUTO, 1 open in scope (76 more open carry unregistered BBL 3042710001, excluded by scope), unavailable. BIN 3042334: two lots (3015570038 among them).
SELECT l.bbl::text AS bbl, p.unitsres,
       (SELECT count(*) FROM hpd_violations v WHERE v.bin = %(bin)s AND v.violationstatus = 'Open'
         AND v.bbl IN (SELECT bbl FROM hpd_registrations WHERE bbl IS NOT NULL)) AS open_violations
FROM (SELECT DISTINCT bbl FROM hpd_registrations WHERE bin = %(bin)s AND bbl IS NOT NULL) l
LEFT JOIN pluto_latest p ON p.bbl = l.bbl
ORDER BY l.bbl;
