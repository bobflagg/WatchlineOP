-- Q3.4 expected name agreement, computed in SQL so it is independent of src/watchline/compare.py.
-- Rules (decision 2026-11-12): N1 = uppercase, trim, collapse whitespace. N2 = N1, remove periods, turn commas into spaces,
-- collapse again. Spaces inside a name are never removed. Outcomes: exact-normalized (equal after N1), normalization-match
-- (equal after N2 only, rule N2), different, not-comparable (either name absent).
-- Expected: ('5413 PLAZA LLC','5413 PLAZA LLC') exact-normalized; ('HP SUNSET PARK I HDFC INC.','HP SUNSET PARK I HDFC INC')
-- normalization-match; ('K S TURNPIKE LLC','KS Turnpike LLC') different; ('ACME LLC', NULL) not-comparable.
WITH p(a, b) AS (VALUES ('HP SUNSET PARK I HDFC INC.', 'HP SUNSET PARK I HDFC INC'))
SELECT a, b,
  CASE WHEN nullif(btrim(a), '') IS NULL OR nullif(btrim(b), '') IS NULL THEN 'not-comparable'
       WHEN upper(btrim(regexp_replace(a, '\s+', ' ', 'g'))) = upper(btrim(regexp_replace(b, '\s+', ' ', 'g'))) THEN 'exact-normalized'
       WHEN upper(btrim(regexp_replace(replace(replace(a, '.', ''), ',', ' '), '\s+', ' ', 'g')))
          = upper(btrim(regexp_replace(replace(replace(b, '.', ''), ',', ' '), '\s+', ' ', 'g'))) THEN 'normalization-match'
       ELSE 'different' END AS outcome
FROM p;
