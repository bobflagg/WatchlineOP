-- Q2.1 expected answers for Registration nodes and HAS_REGISTRATION, from the frozen JustFix/WoW snapshot.
-- Independent of the loader. hpd_registrations (2026-05-29), checked read-only 2026-11-12.
-- verified against the frozen baseline recorded in data/README.md (2026-11-16).
--
-- Rules: a Registration exists for each registrationid on a row with a valid BIN (Q1.2 rule) and registrationid > 0.
-- registrationid 0 is a placeholder shared by 3 unrelated buildings (1056989, 2063477, 4238296) and is excluded and
-- counted (3 rows); those buildings have no registration in the graph. Each distinct
-- (BIN, registrationid) is one HAS_REGISTRATION. registrationid repeats and its rows can carry different dates
-- (23 registration ids), so dates belong to the (BIN, registrationid) pair. If the rows of a pair disagree,
-- or some are null, the date is absent, never picked (9 pairs disagree).
-- The registration period START is not in the source. A registration is "current" only relative to a stated date.

-- Registrations of one building. Replace the BIN to check another.
-- Expected 3014788 (anchor A): 316103, last 2025-09-30, end 2026-09-01.
-- Expected 3013901 (anchor C): 350423, last 2025-10-23, end 2026-09-01.
-- Expected 3324448 / 3324450 / 3324451 (anchor D): 302437 / 344220 / 331116, each last 2025-07-16, end 2026-09-01.
-- Expected 3014490 (234 54 St): 306882, last 2020-08-31, end 2021-09-01 (ended before the snapshot).
-- Expected 3014601: 345930, last absent (null in source), end 2025-09-01.
-- Expected 5114047: 15905, last absent and end absent (rows disagree: last 2025-04-22 / 2025-08-26, end 2025-09-01 / 2026-09-01).
-- Expected 4147320: 12 registrations (422780 to 422791).
-- Expected 1056989: none (its only registration id is the placeholder 0).
SELECT registrationid,
       CASE WHEN count(DISTINCT lastregistrationdate) = 1 AND count(lastregistrationdate) = count(*)
            THEN min(lastregistrationdate) END AS last_registered,
       CASE WHEN count(DISTINCT registrationenddate) = 1 AND count(registrationenddate) = count(*)
            THEN min(registrationenddate) END AS registration_end
FROM hpd_registrations
WHERE bin = '3014788' AND bin ~ '^[1-5][0-9]{6}$' AND bin !~ '000000$' AND registrationid > 0
GROUP BY registrationid ORDER BY registrationid;

-- Totals. Expected: 192808 registrations; 201763 (BIN, registration) pairs, of which 198525 have a last-registered
-- date and 201755 an end date (3 placeholder pairs, registrationid 0, excluded); 9 pairs have conflicting dates; 1059 BINs have more than one registration.
SELECT (SELECT count(DISTINCT registrationid) FROM hpd_registrations WHERE bbl IS NOT NULL AND bin ~ '^[1-5][0-9]{6}$' AND bin !~ '000000$' AND registrationid > 0) AS registrations,
       count(*) AS pairs,
       count(*) FILTER (WHERE has_last) AS with_last,
       count(*) FILTER (WHERE has_end) AS with_end,
       (SELECT count(*) FROM (SELECT bin FROM hpd_registrations WHERE bbl IS NOT NULL AND bin ~ '^[1-5][0-9]{6}$' AND bin !~ '000000$' AND registrationid > 0
                              GROUP BY bin HAVING count(DISTINCT registrationid) > 1) m) AS bins_multi
FROM (SELECT registrationid, bin,
             count(DISTINCT lastregistrationdate) = 1 AND count(lastregistrationdate) = count(*) AS has_last,
             count(DISTINCT registrationenddate) = 1 AND count(registrationenddate) = count(*) AS has_end
      FROM hpd_registrations WHERE bbl IS NOT NULL AND bin ~ '^[1-5][0-9]{6}$' AND bin !~ '000000$' AND registrationid > 0
      GROUP BY registrationid, bin) p;
