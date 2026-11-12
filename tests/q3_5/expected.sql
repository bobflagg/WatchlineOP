-- Q3.5 expected address agreement, computed in SQL so it is independent of src/watchline/compare.py.
-- Rule A1 (decision 2026-11-12): same = street line equal after N1 (uppercase, trim, collapse whitespace) AND the first five
-- digits of the ZIP equal; differs = both street lines and both ZIPs present and at least one differs; absent = either street
-- line or either ZIP absent. The second line (a unit, a suite, a floor, a care-of line) is reported apart, never compared.
-- Abbreviations (AVE and AVENUE) are a difference: a near match is not a finding.
-- Expected: ('746 61ST STREET','11220','746 61ST STREET','11220') same; ('1465A FLATBUSH AVE','11210','1465A FLATBUSH AVENUE','11210') differs;
-- (NULL,'11220','746 61ST STREET','11220') absent.
WITH p(la, za, lb, zb) AS (VALUES ('746 61ST STREET', '11220', '746 61st  Street', '11220-1234'))
SELECT CASE WHEN nullif(btrim(la), '') IS NULL OR nullif(btrim(lb), '') IS NULL
              OR substring(za from '^\s*(\d{5})') IS NULL OR substring(zb from '^\s*(\d{5})') IS NULL THEN 'absent'
            WHEN upper(btrim(regexp_replace(la, '\s+', ' ', 'g'))) = upper(btrim(regexp_replace(lb, '\s+', ' ', 'g')))
             AND substring(za from '^\s*(\d{5})') = substring(zb from '^\s*(\d{5})') THEN 'same'
            ELSE 'differs' END AS outcome
FROM p;
