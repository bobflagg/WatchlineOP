-- Q4.1 expected answers for non-owner Contact nodes and HAS_CONTACT, from the frozen JustFix/WoW snapshot.
-- Independent of the loader. hpd_contacts (2026-05-29), profiled read-only 2026-11-12.
-- verified against the frozen baseline recorded in data/README.md (2026-11-16).
--
-- Rules: a Contact exists for each distinct (registrationid, type, corporation name, person name, title) of a
-- contact whose type is NOT CorporateOwner/IndividualOwner/JointOwner, on a registration loaded in Q2.1.
-- Blank name parts and blank titles are absent. Person name = first, middle initial, last joined by single spaces.
-- Agent and Lessee rows can carry both a corporation and a person (83,526 of 155,280 agents); both are kept, neither dropped.
-- Rows with neither name stay as contacts with the name absent (1,497 contacts): the role is still a recorded fact.
-- SiteManager rows never carry a business address (162,187 of 162,187). A title is recorded on HeadOfficer, Officer and a
-- few Shareholder rows only. Exact duplicates are one contact.

-- Contacts of one registration. Replace the id to check another.
-- Expected 316103 (anchor A): Agent, HeadOfficer (PRESIDENT), Shareholder, SiteManager; the owner is Q2.2.
-- Expected 350423 (anchor C): Agent (corporation + person), HeadOfficer (PRESIDENT OF CO), SiteManager.
-- Expected 10067 (5032172): a Lessee beside two joint owners.
-- Expected 386590 (3346270): an Officer with no name.
-- Expected 10061 (5048404): none.
SELECT c.type, nullif(btrim(c.title), '') AS title, nullif(btrim(c.corporationname), '') AS corporation,
       nullif(btrim(concat_ws(' ', nullif(btrim(c.firstname), ''), nullif(btrim(c.middleinitial), ''), nullif(btrim(c.lastname), ''))), '') AS person
FROM hpd_contacts c
WHERE c.registrationid = 316103 AND c.type NOT IN ('CorporateOwner','IndividualOwner','JointOwner')
GROUP BY 1, 2, 3, 4 ORDER BY 1;

-- Totals. Expected: 526889 contacts; 1497 with no name; 119312 with a title; 176618 registrations with at least one.
SELECT count(*) AS contacts, count(*) FILTER (WHERE corp IS NULL AND person IS NULL) AS unnamed,
       count(*) FILTER (WHERE title IS NOT NULL) AS titled, count(DISTINCT registrationid) AS regs
FROM (SELECT c.registrationid, c.type, nullif(btrim(c.corporationname), '') corp,
             nullif(btrim(concat_ws(' ', nullif(btrim(c.firstname), ''), nullif(btrim(c.middleinitial), ''), nullif(btrim(c.lastname), ''))), '') person,
             nullif(btrim(c.title), '') title
      FROM hpd_contacts c
      WHERE c.type NOT IN ('CorporateOwner','IndividualOwner','JointOwner')
        AND c.registrationid IN (SELECT registrationid FROM hpd_registrations WHERE bbl IS NOT NULL AND bin ~ '^[1-5][0-9]{6}$' AND bin !~ '000000$' AND registrationid > 0)
      GROUP BY 1, 2, 3, 4, 5) k;
