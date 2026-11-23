-- Q6.3 expected HPD contacts and ZIPs whose street line plus second line equals one derived masked address text, from the frozen snapshot.
-- verified against the frozen baseline recorded in data/README.md (2026-11-16). Parameter: %(address)s (the derived text, uppercase). Same rules as tests/q6_2/expected.sql;
-- the text and its degree come from the release (see check_portfolio_masked.py), not from the database.
-- Contacts follow the graph's identity rules (as tests/q6_1/expected.sql). A contact's second line is absent when its duplicates
-- disagree or are blank, so it then counts as the street line alone. The text names no ZIP, so ZIPs are listed, not matched.
WITH valid AS (SELECT DISTINCT registrationid FROM hpd_registrations
               WHERE bbl IS NOT NULL AND bin ~ '^[1-5][0-9]{6}$' AND bin !~ '000000$' AND registrationid > 0),
st AS (SELECT c.registrationid, c.type,
              nullif(btrim(concat_ws(' ', nullif(btrim(c.businesshousenumber), ''), nullif(btrim(c.businessstreetname), ''))), '') AS street,
              nullif(btrim(c.businessapartment), '') AS apt, nullif(btrim(c.businesszip), '') AS zp,
              nullif(btrim(c.corporationname), '') AS corp,
              nullif(btrim(concat_ws(' ', nullif(btrim(c.firstname), ''), nullif(btrim(c.middleinitial), ''), nullif(btrim(c.lastname), ''))), '') AS person,
              nullif(btrim(c.title), '') AS ttl
       FROM hpd_contacts c WHERE c.registrationid IN (SELECT registrationid FROM valid)),
st2 AS (SELECT *, CASE WHEN type = 'CorporateOwner' THEN corp ELSE person END AS nm FROM st),
own AS (SELECT CASE WHEN count(DISTINCT street) = 1 AND count(street) = count(*) THEN min(street) END AS street,
               CASE WHEN count(DISTINCT apt) = 1 AND count(apt) = count(*) THEN min(apt) END AS apt,
               CASE WHEN count(DISTINCT zp) = 1 AND count(zp) = count(*) THEN min(zp) END AS zp
        FROM st2 WHERE type IN ('CorporateOwner', 'IndividualOwner', 'JointOwner') GROUP BY registrationid, type, nm),
rol AS (SELECT CASE WHEN count(DISTINCT street) = 1 AND count(street) = count(*) THEN min(street) END AS street,
               CASE WHEN count(DISTINCT apt) = 1 AND count(apt) = count(*) THEN min(apt) END AS apt,
               CASE WHEN count(DISTINCT zp) = 1 AND count(zp) = count(*) THEN min(zp) END AS zp
        FROM st2 WHERE type NOT IN ('CorporateOwner', 'IndividualOwner', 'JointOwner') GROUP BY registrationid, type, corp, person, ttl),
hit AS (SELECT upper(CASE WHEN apt IS NULL THEN street ELSE street || ' ' || apt END) AS txt, left(zp, 5) AS z5
        FROM (SELECT * FROM own UNION ALL SELECT * FROM rol) x WHERE street IS NOT NULL)
SELECT count(*) AS contacts,
       coalesce(array_agg(DISTINCT z5 ORDER BY z5) FILTER (WHERE z5 IS NOT NULL), '{}') AS zips
FROM hit WHERE txt = %(address)s;
