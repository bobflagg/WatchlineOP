-- Q7.3 expected answers: ACRIS documents naming two given parties, with each party's role and address and the hub count. Independent of the loader.
-- real_property_parties (2026-05-31), profiled read-only 2026-11-14. verified against the frozen baseline recorded in data/README.md (2026-11-16).
-- Rules (decision 2026-11-16, scope C): a document is loaded when two or more distinct party N3 names equal HPD CorporateOwner N3 names (96,901 documents).
-- Role is the recorded partytype (1, 2 or 3). Names are exact N3 matches (a lead). Hub count = distinct N3 party names (and documents) at the same
-- upper-cased street line + first five ZIP chars, across all of ACRIS (stored as addressNames and addressDocuments).
-- Anchor pair 5413 PLAZA LLC / 702 PLAZA LLC: both are HPD owners under N3 (HPD spells one "702 Plaza LLC"), so the three joint documents
-- 2021031601183001, 2021031601183002 and 2023061200959001 are in scope C.
SELECT p.documentid, p.partytype, p.name, nullif(btrim(p.address1),'') a1, nullif(btrim(p.address2),'') a2, nullif(btrim(p.zip),'') zip
FROM real_property_parties p
WHERE p.documentid IN (SELECT documentid FROM real_property_parties WHERE upper(btrim(name)) = %(a)s
                       INTERSECT SELECT documentid FROM real_property_parties WHERE upper(btrim(name)) = %(b)s)
ORDER BY 1,2,3;

-- Hub count for one address.
-- SELECT count(DISTINCT upper(btrim(name))), count(DISTINCT documentid) FROM real_property_parties
--  WHERE upper(btrim(address1)) = %(street)s AND left(btrim(coalesce(zip,'')),5) = %(zip5)s;
