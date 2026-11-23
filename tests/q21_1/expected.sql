-- Q21.1 expected answers: open violations by class per lot, and PLUTO units. Independent of the graph. hpd_violations (through 2026-07-02),
-- hpd_registrations and pluto_latest 26v1 (frozen baseline, data/README.md). Same scope as Q15 (violation BBL registered, BIN registered and valid).
-- Counting unit: distinct violations of the BINs registered on the lot. A BIN on several lots counts toward each lot. Layer membership comes from the BOR release, not SQL.
SELECT rb.bbl::text AS bbl, v.class, count(DISTINCT v.violationid) AS open_violations
FROM (SELECT DISTINCT bbl, bin FROM hpd_registrations WHERE bbl IS NOT NULL AND bin ~ '^[1-5][0-9]{6}$' AND bin !~ '000000$' AND bbl::text = ANY(%(bbls)s)) rb
JOIN hpd_violations v ON v.bin = rb.bin AND v.violationstatus = 'Open'
WHERE v.bbl IN (SELECT bbl FROM hpd_registrations WHERE bbl IS NOT NULL)
GROUP BY 1, 2;
