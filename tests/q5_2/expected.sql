-- Q5.2 expected process name and address, from dos_active_corporations (data through 2026-07-06). Provisional until the dump is identified.
-- Blank text is absent. Of the 55,694 records matched to HPD owner and ACRIS grantee names in an earlier profile (HPD owners only), 46 have no
-- process name and 47 no address, 62 no ZIP: kept absent. 'THE COMPANY' and 'THE LIMITED LIABILITY COMPANY' (94,012 domestic LLCs) are kept as recorded.
-- Expected 5857246: process name = the entity's own name, 5 CROMWELL CIRCLE, 10304.  6691492 (606 56TH ST LLC): THE COMPANY.
-- Expected 3574572 (K S TURNPIKE LLC): a person (name not repeated), 6 STEVEN LANE, 11024.
SELECT dosid, nullif(btrim(dosprocessname),'') AS process_name, nullif(btrim(dosprocessaddress1),'') AS line1, nullif(btrim(dosprocessaddress2),'') AS line2,
       nullif(btrim(dosprocesscity),'') AS city, nullif(btrim(dosprocessstate),'') AS state, nullif(btrim(dosprocesszip),'') AS zip
FROM dos_active_corporations WHERE dosid = 5857246;
