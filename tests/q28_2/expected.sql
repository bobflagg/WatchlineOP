-- Q28.2 expected answers: the registered owners of a building (HPD owner contacts across its registrations), to compare with a case's respondents.
-- Independent of the graph. hpd_registrations and hpd_contacts (frozen baseline, data/README.md); hpd_litigations for the respondent string.
-- Rules: registered owner = contact type CorporateOwner, IndividualOwner or JointOwner (decision 2026-11-12), over every registration of the BIN
-- (registrationid 0 excluded). The respondent string is split on commas; blank parts are dropped; each part and each owner name is compared with
-- rule N3 (src/watchline/compare.py). A case matches the registered owner when any respondent part equals an owner name after N3. A match by name
-- only is a lead (same string, not proof of identity); a respondent can be an agent or an individual, roles are as recorded. No respondent, or no
-- owner name, is "not comparable", never "different".
SELECT DISTINCT r.registrationid, c.type,
       CASE WHEN c.type = 'CorporateOwner' THEN nullif(btrim(c.corporationname), '')
            ELSE nullif(btrim(concat_ws(' ', nullif(btrim(c.firstname), ''), nullif(btrim(c.middleinitial), ''), nullif(btrim(c.lastname), ''))), '') END AS name
FROM hpd_registrations r JOIN hpd_contacts c ON c.registrationid = r.registrationid
WHERE r.bin = %(bin)s AND r.registrationid <> 0 AND c.type IN ('CorporateOwner', 'IndividualOwner', 'JointOwner')
ORDER BY 1, 2, 3;

SELECT litigationid, nullif(btrim(respondent), '') AS respondent FROM hpd_litigations WHERE bin = %(bin)s ORDER BY litigationid;
