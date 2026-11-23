-- Q27.1 expected answers: the complaint problems recorded against a building in a period, by type, major category and status. Independent of the graph.
-- hpd_complaints_and_problems (data through 2026-07-07) and hpd_registrations (frozen baseline, data/README.md).
-- Rules (decision 2026-11-19, user choice): scope is every problem received on or after 2021-01-01 whose BBL is HPD-registered and whose BIN is a
-- registered, valid BIN (^[1-5][0-9]{6}$, not ending 000000). Others are excluded and counted. Open = problemstatus 'OPEN' at the snapshot.
-- Counting unit: problem records (problemid is unique), duplicate-flagged ones included and counted apart; distinct complaints (complaintid) are
-- returned too, since one complaint can have several problems. apartment is never returned. Period: receiveddate between %(start)s and %(end)s inclusive.
-- Expected for BIN 3013901 (anchor C), 2023-01-01 to 2025-12-31: 27 problems (EMERGENCY 12, IMMEDIATE EMERGENCY 2, NON EMERGENCY 13), none open, 1 flagged duplicate.
WITH rb AS (SELECT DISTINCT bbl FROM hpd_registrations WHERE bbl IS NOT NULL),
     rbin AS (SELECT DISTINCT bin FROM hpd_registrations WHERE bbl IS NOT NULL AND bin ~ '^[1-5][0-9]{6}$' AND bin !~ '000000$')
SELECT c.type, c.majorcategory, c.problemstatus, count(*) AS problems, count(*) FILTER (WHERE c.problemduplicateflag) AS duplicates,
       count(DISTINCT c.complaintid) AS complaints, min(c.receiveddate)::date AS first_received, max(c.receiveddate)::date AS last_received
FROM hpd_complaints_and_problems c JOIN rb ON rb.bbl = c.bbl JOIN rbin ON rbin.bin = c.bin
WHERE c.bin = %(bin)s AND c.receiveddate >= DATE '2021-01-01' AND c.receiveddate BETWEEN %(start)s AND %(end)s
GROUP BY c.type, c.majorcategory, c.problemstatus ORDER BY c.type, c.majorcategory, c.problemstatus;

-- Totals. Expected (queried 2026-11-19): 4,061,388 problems since 2021-01-01 on registered lots; 4,033,827 on a registered BIN (26,221 open, 682,192 flagged duplicate); 27,561 excluded.
SELECT count(*) AS on_registered_lots,
       count(*) FILTER (WHERE rbin.bin IS NOT NULL) AS loaded,
       count(*) FILTER (WHERE rbin.bin IS NOT NULL AND c.problemstatus = 'OPEN') AS loaded_open,
       count(*) FILTER (WHERE rbin.bin IS NOT NULL AND c.problemduplicateflag) AS loaded_duplicates,
       count(*) FILTER (WHERE rbin.bin IS NULL) AS excluded
FROM hpd_complaints_and_problems c
JOIN (SELECT DISTINCT bbl FROM hpd_registrations WHERE bbl IS NOT NULL) rb ON rb.bbl = c.bbl
LEFT JOIN (SELECT DISTINCT bin FROM hpd_registrations WHERE bbl IS NOT NULL AND bin ~ '^[1-5][0-9]{6}$' AND bin !~ '000000$') rbin ON rbin.bin = c.bin
WHERE c.receiveddate >= DATE '2021-01-01';
