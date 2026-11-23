-- Q6.1 expected counts for one business address, from the frozen snapshot. verified against the frozen baseline recorded in data/README.md (2026-11-16).
-- Parameters: %(street)s (uppercase street line), %(zip5)s (first five characters of the ZIP).
-- Contacts follow the graph's identity rules: every contact is distinct on (registration, type, corporation, person, title). A contact's street line or ZIP is absent when its duplicates disagree or only some
-- have it. Only contacts on a loaded registration (valid BIN, bbl present, registrationid > 0) count; buildings are the valid BINs of
-- those registrations. A second line is not part of the key. Owner and role counts are reported apart.
-- Expected: 746 61ST STREET 11220 -> 8 contacts (2 owner, 6 role), 2 registrations, 2 buildings;
--           418 BROADWAY 12207 -> 66 (27, 39), 32, 32; 418 BROADWAY 11207 -> 8 (2, 6), 3, 3 (a different address on the same street);
--           300 EAST 2ND STREET 11218 -> 2 (1, 1), 1, 1; 300 EAST2ND STREET 11218 -> 1 (0, 1), 1, 1 (HPD's other spelling, kept apart).
WITH valid AS (SELECT DISTINCT registrationid, bin FROM hpd_registrations
               WHERE bbl IS NOT NULL AND bin ~ '^[1-5][0-9]{6}$' AND bin !~ '000000$' AND registrationid > 0),
st AS (SELECT c.registrationid, c.type,
              nullif(btrim(concat_ws(' ', nullif(btrim(c.businesshousenumber), ''), nullif(btrim(c.businessstreetname), ''))), '') AS street,
              nullif(btrim(c.businesszip), '') AS zp,
              nullif(btrim(c.corporationname), '') AS corp,
              nullif(btrim(concat_ws(' ', nullif(btrim(c.firstname), ''), nullif(btrim(c.middleinitial), ''), nullif(btrim(c.lastname), ''))), '') AS person,
              nullif(btrim(c.title), '') AS ttl
       FROM hpd_contacts c WHERE c.registrationid IN (SELECT registrationid FROM valid)),
st2 AS (SELECT * FROM st),
own AS (SELECT registrationid, 'owner' AS kind,
               CASE WHEN count(DISTINCT street) = 1 AND count(street) = count(*) THEN min(street) END AS street,
               CASE WHEN count(DISTINCT zp) = 1 AND count(zp) = count(*) THEN min(zp) END AS zp
        FROM st2 WHERE type IN ('CorporateOwner', 'IndividualOwner', 'JointOwner') GROUP BY registrationid, type, corp, person, ttl),
rol AS (SELECT registrationid, 'role' AS kind,
               CASE WHEN count(DISTINCT street) = 1 AND count(street) = count(*) THEN min(street) END AS street,
               CASE WHEN count(DISTINCT zp) = 1 AND count(zp) = count(*) THEN min(zp) END AS zp
        FROM st2 WHERE type NOT IN ('CorporateOwner', 'IndividualOwner', 'JointOwner') GROUP BY registrationid, type, corp, person, ttl),
hit AS (SELECT * FROM (SELECT * FROM own UNION ALL SELECT * FROM rol) a
        WHERE upper(street) = %(street)s AND left(zp, 5) = %(zip5)s)
SELECT count(*) AS contacts,
       count(*) FILTER (WHERE kind = 'owner') AS owner_contacts,
       count(*) FILTER (WHERE kind = 'role') AS role_contacts,
       count(DISTINCT registrationid) AS registrations,
       (SELECT count(DISTINCT bin) FROM valid WHERE registrationid IN (SELECT registrationid FROM hit)) AS buildings
FROM hit;
