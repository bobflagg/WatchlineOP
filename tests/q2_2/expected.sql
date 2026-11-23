-- Q2.2 expected answers for owner-type Contact nodes and HAS_CONTACT, from the frozen JustFix/WoW snapshot.
-- Independent of the loader. hpd_contacts joined to hpd_registrations on registrationid (2026-05-29), checked read-only 2026-11-12.
-- verified against the frozen baseline recorded in data/README.md (2026-11-16).
--
-- Rules: the "registered owner" contacts are those of type CorporateOwner, IndividualOwner or JointOwner
-- (decision 2026-11-12). Other types (Agent, HeadOfficer, Officer, Shareholder, SiteManager, Lessee) are not owners here.
-- name = corporationname for CorporateOwner; first name, middle initial and last name joined for the other two.
-- A blank name is absent (183 corporate + 239 individual/joint contacts, counted over all registrations).
-- Contacts belong to a registration, not a building. A registration can have several owner contacts (joint owners,
-- an LLC and an LP); all are listed. Exact duplicates (same registration, type, name) are one contact.
-- registrationcontactid is NOT unique in the snapshot (733038 distinct in 782024 rows), so it is not used as a key.
-- registrationid 0 (placeholder, 27 contacts of which 6 are owner type) is excluded with its registration.
-- A registration with no owner contact has none listed: the answer says "no owner contact recorded", infers none.

-- Owner contacts of one registration. Replace the id to check another.
-- Expected 316103: CorporateOwner '5413 PLAZA LLC'.   350423: CorporateOwner '438 52 ST OWNERS CORP'.
-- Expected 302437 and 344220: 'HP SUNSET PARK I HDFC INC.'; 331116: 'HP SUNSET PARK I HDFC INC' (spellings as recorded).
-- Expected 121720: two contacts, 'HP PLAZA LLC' and 'HP PLAZA LP' (both CorporateOwner).
-- Expected 10067: two JointOwner contacts. 332569: CorporateOwner with name absent plus one IndividualOwner. 345930: no owner contact.
SELECT DISTINCT type,
       CASE WHEN type = 'CorporateOwner' THEN nullif(btrim(corporationname), '')
            ELSE nullif(btrim(concat_ws(' ', nullif(btrim(firstname), ''), nullif(btrim(middleinitial), ''),
                                         nullif(btrim(lastname), ''))), '') END AS name
FROM hpd_contacts
WHERE registrationid = 316103 AND type IN ('CorporateOwner', 'IndividualOwner', 'JointOwner')
ORDER BY 1, 2;

-- Totals over registrations with a valid-BIN row. Expected: 203804 owner contacts (203414 with a name; key is registration, type, corporation, person, title);
-- 12827 registrations over all rows have none (of which some lack a valid BIN, so the graph count differs; see the check).
SELECT count(*) AS contacts, count(name) AS named
FROM (SELECT DISTINCT c.registrationid, c.type, nullif(btrim(c.corporationname), '') AS corp,
             nullif(btrim(concat_ws(' ', nullif(btrim(c.firstname), ''), nullif(btrim(c.middleinitial), ''), nullif(btrim(c.lastname), ''))), '') AS person,
             nullif(btrim(c.title), '') AS title,
             CASE WHEN c.type = 'CorporateOwner' THEN nullif(btrim(c.corporationname), '')
                  ELSE nullif(btrim(concat_ws(' ', nullif(btrim(c.firstname), ''), nullif(btrim(c.middleinitial), ''),
                                               nullif(btrim(c.lastname), ''))), '') END AS name
      FROM hpd_contacts c
      WHERE c.type IN ('CorporateOwner', 'IndividualOwner', 'JointOwner')
        AND c.registrationid IN (SELECT registrationid FROM hpd_registrations
                                 WHERE bbl IS NOT NULL AND bin ~ '^[1-5][0-9]{6}$' AND bin !~ '000000$' AND registrationid > 0)) x;
