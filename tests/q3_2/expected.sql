-- Q3.2 expected answers for Grantee and HAS_GRANTEE, from the frozen JustFix/WoW snapshot.
-- Independent of the loader. real_property_parties (2026-05-31), checked read-only 2026-11-12.
-- verified against the frozen baseline recorded in data/README.md (2026-11-16).
--
-- Rules:
--  * A Grantee is a distinct party row of partytype 2 on a loaded deed (Q3.1 scope and deed types).
--    partytype 1 (grantor) and 3 are not loaded (decision 2026-11-12).
--  * name, mailingAddress (address1), addressLine2 (address2) and zip are as recorded, trimmed; a blank is absent.
--    Nothing is normalized in the graph: the comparison rules N1, N2 and A1 run at answer time (src/watchline/compare.py).
--  * Rows identical in document, name, address1, address2 and zip are one Grantee. The same name with a different
--    address on the same deed stays two Grantees; none is chosen.
--  * address1 is not always a street: it can hold a care-of line or a person's name. It is reported as recorded.

-- Grantees of one deed. Replace the document id to check another.
-- Expected 2025032100031001: '5413 PLAZA LLC', '746 61ST STREET', no line 2, '11220'.
-- Expected 2017061600025001: CLL2 LLC; NEIGHBORHOOD STABILIZATION ASSOCIATES I, L.P.; SUNSET IV EQUITIES LLC ('1465A FLATBUSH AVE', other two 'AVENUE').
-- Expected 2017061600025002: HP SUNSET PARK I HOUSING DEV FUND COMPANY, INC; SUNSET PARK OWNER I LLC (both '152 WEST 57TH STREET', '36TH FLOOR', '10019').
-- Expected 2018092900072001: AADVA REALTY LLC; K S TURNPIKE LLC (both '14 SINCLAIR DR', '11024').
-- Expected 2021022201130003: '5413 PLAZA LLC', '5 CROMWELL CIRCLE', '10304'.
-- Expected 2003020300253001: contains the name '5413  7TH AVENUE LLC' with a double space, kept as recorded.
SELECT DISTINCT nullif(btrim(name), ''), nullif(btrim(address1), ''), nullif(btrim(address2), ''), nullif(btrim(zip), '')
FROM real_property_parties
WHERE documentid = '2025032100031001' AND partytype = 2
ORDER BY 1, 2;

-- Totals over the whole scope: see check_grantees.py (SOURCE_TOTALS). Expected values are in fixtures.yaml.
