-- Q3.3 expected answers: the recorded owners on the registrations of a lot's buildings. Reuses the Q2 graph; no new element.
-- Independent of the loader. hpd_registrations and hpd_contacts (2026-05-29), checked read-only 2026-11-12.
-- Rules (Q2): valid BIN, registrationid > 0, owner types CorporateOwner/IndividualOwner/JointOwner, names as recorded,
-- exact duplicates one contact. A lot's owners are those of all its buildings' registrations; none is chosen.
-- Expected 3008260002 (anchor A): registration 316103, CorporateOwner '5413 PLAZA LLC'.
-- Expected 3008210012 (anchor D): 302437 and 344220 'HP SUNSET PARK I HDFC INC.', 331116 'HP SUNSET PARK I HDFC INC'.
-- Expected 3008080025 (anchor G): registration 305188, CorporateOwner 'KS Turnpike LLC'.
SELECT DISTINCT r.registrationid, c.type,
       CASE WHEN c.type = 'CorporateOwner' THEN nullif(btrim(c.corporationname), '')
            ELSE nullif(btrim(concat_ws(' ', nullif(btrim(c.firstname), ''), nullif(btrim(c.middleinitial), ''),
                                         nullif(btrim(c.lastname), ''))), '') END AS name
FROM hpd_registrations r JOIN hpd_contacts c ON c.registrationid = r.registrationid
WHERE r.bbl = '3008260002' AND r.bin ~ '^[1-5][0-9]{6}$' AND r.bin !~ '000000$' AND r.registrationid > 0
  AND c.type IN ('CorporateOwner', 'IndividualOwner', 'JointOwner')
ORDER BY 1, 2, 3;
