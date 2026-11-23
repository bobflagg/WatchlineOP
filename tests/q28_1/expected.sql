-- Q28.1 expected answers: the Housing Court cases HPD recorded against a building, with type, dates, status, harassment finding, penalty and respondent.
-- Independent of the graph. hpd_litigations (data through 2026-07-09) and hpd_registrations (frozen baseline, data/README.md).
-- Rules: scope is every case whose BBL is HPD-registered and whose BIN is a registered, valid BIN (^[1-5][0-9]{6}$, not ending 000000); others are
-- excluded and counted. Counting unit: cases (litigationid is unique). Values are as recorded; blank is absent. A case is an action brought, not a finding
-- of fault. A harassment finding is a recorded value of After Inquest or After Trial; 'No Harassment' is a recorded outcome, not a finding.
-- Dates that cannot be right (before 1990, after the snapshot) are kept as recorded and counted, never corrected or dropped.
-- Expected for BIN 3013901 (anchor C): one Tenant Action case (424938), opened 2023-05-15, CLOSED, open judgement NO, no finding, no penalty.
SELECT l.litigationid, nullif(btrim(l.casetype), '') AS casetype, l.caseopendate::date AS opened, nullif(btrim(l.casestatus), '') AS status,
       nullif(btrim(l.openjudgement), '') AS judgement, nullif(btrim(l.findingofharassment), '') AS finding, l.findingdate::date AS found,
       nullif(btrim(l.penalty), '')::int AS penalty, nullif(btrim(l.respondent), '') AS respondent
FROM hpd_litigations l
WHERE l.bin = %(bin)s
  AND l.bbl IN (SELECT bbl FROM hpd_registrations WHERE bbl IS NOT NULL)
  AND l.bin IN (SELECT bin FROM hpd_registrations WHERE bbl IS NOT NULL AND bin ~ '^[1-5][0-9]{6}$' AND bin !~ '000000$')
ORDER BY l.caseopendate NULLS LAST, l.litigationid;

-- Totals. Expected (check 2026-11-20): 211,652 cases on registered lots; 210,169 on a registered lot and BIN; 1,483 excluded.
-- Within the loaded cases: 289 with no open date, 3 before 1990, 1 after 2026-07-31, 217 with a harassment finding (1 without a finding date),
-- 5,990 'No Harassment', 2,919 with no respondent, 217 with a penalty.
SELECT count(*) AS on_registered_lots,
       count(*) FILTER (WHERE rbin.bin IS NOT NULL) AS loaded,
       count(*) FILTER (WHERE rbin.bin IS NULL) AS excluded,
       count(*) FILTER (WHERE rbin.bin IS NOT NULL AND l.caseopendate IS NULL) AS no_open_date,
       count(*) FILTER (WHERE rbin.bin IS NOT NULL AND l.caseopendate < '1990-01-01') AS before_1990,
       count(*) FILTER (WHERE rbin.bin IS NOT NULL AND l.caseopendate > '2026-07-31') AS after_snapshot,
       count(*) FILTER (WHERE rbin.bin IS NOT NULL AND l.findingofharassment IN ('After Inquest', 'After Trial')) AS findings,
       count(*) FILTER (WHERE rbin.bin IS NOT NULL AND l.findingofharassment = 'No Harassment') AS no_harassment,
       count(*) FILTER (WHERE rbin.bin IS NOT NULL AND (l.respondent IS NULL OR btrim(l.respondent) = '')) AS no_respondent
FROM hpd_litigations l
JOIN (SELECT DISTINCT bbl FROM hpd_registrations WHERE bbl IS NOT NULL) rb ON rb.bbl = l.bbl
LEFT JOIN (SELECT DISTINCT bin FROM hpd_registrations WHERE bbl IS NOT NULL AND bin ~ '^[1-5][0-9]{6}$' AND bin !~ '000000$') rbin ON rbin.bin = l.bin;
