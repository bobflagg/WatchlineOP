-- Q4.2 expected business addresses of RoleContact nodes, from the frozen snapshot. Provisional until the dump is identified.
-- Address = house number and street name joined by one space (blank parts left out), plus apartment and ZIP as recorded.
-- If duplicates of one contact disagree on a part, or only some have it, that part is absent, never picked (360 contacts).
-- SiteManager never has an address. Same address on several roles is a record link only, not evidence of identity.
-- Expected 316103 (anchor A): Agent, HeadOfficer and Shareholder at "746 61ST STREET" 11220; SiteManager none.
-- Expected 350423 (anchor C): Agent "300 EAST2ND STREET" 11218 (HPD spelling, as recorded); HeadOfficer "300 EAST 2ND STREET" 11218.
-- Expected 10258 (5023962): a contact whose duplicates disagree, so its street line is absent.
-- Totals. Expected: 369472 contacts with an address of 526889; 360 with conflicting duplicates.
SELECT count(*) AS contacts, count(*) FILTER (WHERE nn = n AND na = 1) AS with_addr, count(*) FILTER (WHERE na > 1 OR (nn > 0 AND nn < n)) AS conflicting
FROM (SELECT c.registrationid, c.type, nullif(btrim(c.corporationname), '') corp,
             nullif(btrim(concat_ws(' ', nullif(btrim(c.firstname), ''), nullif(btrim(c.middleinitial), ''), nullif(btrim(c.lastname), ''))), '') person,
             nullif(btrim(c.title), '') title,
             count(DISTINCT nullif(btrim(concat_ws(' ', nullif(btrim(c.businesshousenumber), ''), nullif(btrim(c.businessstreetname), ''))), '')) na,
             count(nullif(btrim(concat_ws(' ', nullif(btrim(c.businesshousenumber), ''), nullif(btrim(c.businessstreetname), ''))), '')) nn, count(*) n
      FROM hpd_contacts c WHERE c.type NOT IN ('CorporateOwner','IndividualOwner','JointOwner')
        AND c.registrationid IN (SELECT registrationid FROM hpd_registrations WHERE bbl IS NOT NULL AND bin ~ '^[1-5][0-9]{6}$' AND bin !~ '000000$' AND registrationid > 0)
      GROUP BY 1, 2, 3, 4, 5) k;
