-- Q7.1 expected answers: HPD contacts at a business address, with the hub count. Independent of the loader.
-- hpd_contacts (2026-05-29), profiled read-only 2026-11-14. verified against the frozen baseline recorded in data/README.md (2026-11-16).
-- Rules: address key = uppercase street line (house number + street name) + first five ZIP chars (same key as Q6.1). Registrations are distinct registrationid.
-- An entity's contacts are found by exact N3 name match (a lead, shown with evidence). People are never printed in fixtures.
-- Expected '746 61ST STREET' 11220: 2 registrations, 8 contact records; 5413 PLAZA LLC is a CorporateOwner there (registration 316103).
SELECT count(DISTINCT registrationid) AS registrations, count(*) AS contacts
FROM hpd_contacts
WHERE upper(btrim(coalesce(businesshousenumber,'')||' '||coalesce(businessstreetname,''))) = %(street)s
  AND left(btrim(coalesce(businesszip,'')),5) = %(zip5)s;
