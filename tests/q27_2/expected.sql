-- Q27.2 expected answers: complaint problems per residential unit for a building in a period. Independent of the graph.
-- hpd_complaints_and_problems, hpd_registrations, pluto_latest 26v1 (frozen baseline, data/README.md).
-- Rules (decision 2026-11-19): numerator = problems of the BIN received in the period (on or after 2021-01-01, the load window) whose own BBL is
-- HPD-registered (the Q27.1 load scope); denominator = PLUTO unitsres of each lot the BIN is registered on (lot-wide). A BIN on several lots gets one
-- row per lot, never a sum. unitsres 0 or absent (lot not in PLUTO) gives "rate unavailable", never 0 or infinity. rate = problems / unitsres over
-- the whole period (not annualized). Flagged duplicates are included, as in Q27.1.
-- Expected for BIN 3013901, 2023-01-01 to 2025-12-31: lot 3008070024, 32 units, 27 problems, rate 0.84375.
SELECT l.bbl::text AS bbl, p.unitsres,
       (SELECT count(*) FROM hpd_complaints_and_problems c WHERE c.bin = %(bin)s AND c.receiveddate >= DATE '2021-01-01'
         AND c.receiveddate BETWEEN %(start)s AND %(end)s
         AND c.bbl IN (SELECT bbl FROM hpd_registrations WHERE bbl IS NOT NULL)) AS problems
FROM (SELECT DISTINCT bbl FROM hpd_registrations WHERE bin = %(bin)s AND bbl IS NOT NULL) l
LEFT JOIN pluto_latest p ON p.bbl = l.bbl
ORDER BY l.bbl;
