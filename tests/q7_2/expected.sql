-- Q7.2 expected answers: DOS process address shared by two records, with the hub count. Independent of the loader.
-- dos_active_corporations (2026-07-06), profiled read-only 2026-11-14. verified against the frozen baseline recorded in data/README.md (2026-11-16).
-- Rule: process address key = uppercase dosprocessaddress1 + first five ZIP chars; line 2 reported apart. Count = distinct dosid across the whole table.
-- Expected '5413 PLAZA LLC' (5857246) and '702 PLAZA LLC' (5857608): both '5 CROMWELL CIRCLE' 10304, no line 2; 5 active entities list it.
SELECT count(DISTINCT dosid) AS entities
FROM dos_active_corporations
WHERE upper(btrim(dosprocessaddress1)) = %(street)s AND left(btrim(coalesce(dosprocesszip,'')),5) = %(zip5)s;
