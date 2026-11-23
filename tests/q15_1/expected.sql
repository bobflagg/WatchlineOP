-- Q15.1 expected answers: the violations recorded against a building, counted by class and status. Independent of the graph.
-- hpd_violations (data through 2026-07-02) and hpd_registrations (frozen baseline, data/README.md).
-- Rules (decision 2026-11-18, user choice): scope is every violation whose BBL is HPD-registered and whose BIN is a registered, valid BIN
-- (^[1-5][0-9]{6}$, not ending 000000). Others are excluded and counted. Open = violationstatus 'Open' at the snapshot; closed = 'Close'.
-- Counting unit: distinct violations (violationid is unique). The class is the inspector's class (A, B, C, I). apartment is never returned.
-- Expected for BIN 3013901 (anchor C): open B 2, C 2, oldest open inspection 2023-03-25; closed A 1, B 3, C 2.
WITH rb AS (SELECT DISTINCT bbl FROM hpd_registrations WHERE bbl IS NOT NULL),
     rbin AS (SELECT DISTINCT bin FROM hpd_registrations WHERE bbl IS NOT NULL AND bin ~ '^[1-5][0-9]{6}$' AND bin !~ '000000$')
SELECT v.class, v.violationstatus, count(*) AS violations, min(v.inspectiondate)::date AS oldest_inspection
FROM hpd_violations v JOIN rb ON rb.bbl = v.bbl JOIN rbin ON rbin.bin = v.bin
WHERE v.bin = %(bin)s
GROUP BY v.class, v.violationstatus ORDER BY v.class, v.violationstatus;

-- Totals. Expected (queried 2026-11-18): 1,912,362 violations on registered lots (471,058 open); 1,901,592 on a registered BIN; 10,770 excluded.
SELECT count(*) AS on_registered_lots,
       count(*) FILTER (WHERE rbin.bin IS NOT NULL) AS loaded,
       count(*) FILTER (WHERE rbin.bin IS NOT NULL AND v.violationstatus = 'Open') AS loaded_open,
       count(*) FILTER (WHERE rbin.bin IS NULL) AS excluded
FROM hpd_violations v
JOIN (SELECT DISTINCT bbl FROM hpd_registrations WHERE bbl IS NOT NULL) rb ON rb.bbl = v.bbl
LEFT JOIN (SELECT DISTINCT bin FROM hpd_registrations WHERE bbl IS NOT NULL AND bin ~ '^[1-5][0-9]{6}$' AND bin !~ '000000$') rbin ON rbin.bin = v.bin;
