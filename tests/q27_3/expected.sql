-- Q27.3 expected answers: the pest complaint problems recorded against a building in a period, by pest (problemcode) and status. Independent of the graph.
-- hpd_complaints_and_problems (data through 2026-07-07) and hpd_registrations (frozen baseline, data/README.md).
-- Rules (Q27 pest extension, 2026-11-21): same scope as Q27.1 (problems received since 2021-01-01, BBL HPD-registered, BIN a registered valid BIN). A pest
-- complaint problem is one whose minorcategory is 'PESTS'; the pest is its problemcode as recorded (MICE, ROACHES, OTHER, BED BUGS, FLIES, TERMITES, FLEAS).
-- OTHER is not a pest name and never means mice. Open = problemstatus 'OPEN' at the snapshot. Counting unit: problem records (problemid unique),
-- duplicate-flagged ones included and counted apart; distinct complaints are returned too. apartment is never returned.
-- Period: receiveddate between %(start)s and %(end)s inclusive.
-- Expected for BIN 3013901 (anchor C), 2021-01-01 to 2026-12-31: 7 closed pest problems (MICE 1, ROACHES 3, OTHER 2, FLIES 1), none open.
WITH rb AS (SELECT DISTINCT bbl FROM hpd_registrations WHERE bbl IS NOT NULL),
     rbin AS (SELECT DISTINCT bin FROM hpd_registrations WHERE bbl IS NOT NULL AND bin ~ '^[1-5][0-9]{6}$' AND bin !~ '000000$')
SELECT c.problemcode, c.problemstatus, count(*) AS problems, count(*) FILTER (WHERE c.problemduplicateflag) AS duplicates,
       count(DISTINCT c.complaintid) AS complaints, min(c.receiveddate)::date AS first_received, max(c.receiveddate)::date AS last_received
FROM hpd_complaints_and_problems c JOIN rb ON rb.bbl = c.bbl JOIN rbin ON rbin.bin = c.bin
WHERE c.bin = %(bin)s AND c.minorcategory = 'PESTS' AND c.receiveddate >= DATE '2021-01-01' AND c.receiveddate BETWEEN %(start)s AND %(end)s
GROUP BY c.problemcode, c.problemstatus ORDER BY c.problemcode, c.problemstatus;

-- Totals per pest, loaded rows. Expected (queried 2026-11-21): MICE 147,185 (1,508 open, 313 duplicates); ROACHES 130,774 (1,385; 262); OTHER 41,677 (575; 90);
-- BED BUGS 15,259 (172; 38); FLIES 10,853 (170; 8); TERMITES 1,637 (32; 2); FLEAS 1,636 (32; 1). Total PESTS 349,021 (3,874 open, 714 duplicates).
SELECT c.problemcode, count(*) AS loaded, count(*) FILTER (WHERE c.problemstatus = 'OPEN') AS loaded_open, count(*) FILTER (WHERE c.problemduplicateflag) AS loaded_duplicates
FROM hpd_complaints_and_problems c
JOIN (SELECT DISTINCT bbl FROM hpd_registrations WHERE bbl IS NOT NULL) rb ON rb.bbl = c.bbl
JOIN (SELECT DISTINCT bin FROM hpd_registrations WHERE bbl IS NOT NULL AND bin ~ '^[1-5][0-9]{6}$' AND bin !~ '000000$') rbin ON rbin.bin = c.bin
WHERE c.receiveddate >= DATE '2021-01-01' AND c.minorcategory = 'PESTS'
GROUP BY c.problemcode ORDER BY c.problemcode;

-- Loaded rows: no null or blank minor category or problem code; distinct values. Expected: 4,033,827 loaded, 0 null or blank, 59 distinct minor categories.
SELECT count(*) AS loaded,
       count(*) FILTER (WHERE c.minorcategory IS NULL OR trim(c.minorcategory) = '' OR c.problemcode IS NULL OR trim(c.problemcode) = '') AS missing,
       count(DISTINCT c.minorcategory) AS minor_categories
FROM hpd_complaints_and_problems c
JOIN (SELECT DISTINCT bbl FROM hpd_registrations WHERE bbl IS NOT NULL) rb ON rb.bbl = c.bbl
JOIN (SELECT DISTINCT bin FROM hpd_registrations WHERE bbl IS NOT NULL AND bin ~ '^[1-5][0-9]{6}$' AND bin !~ '000000$') rbin ON rbin.bin = c.bin
WHERE c.receiveddate >= DATE '2021-01-01';
