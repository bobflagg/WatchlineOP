-- Q13.2 expected answers: the parties of financing documents, one row per distinct (documentid, partytype, name, address1, address2, zip).
-- real_property_parties (frozen baseline, data/README.md). A blank value is absent. The party type is the recorded code; only on a mortgage
-- (MTGE) does the answer name the role: 1 borrower, 2 lender (decision 2026-11-16, Q11.1).
SELECT DISTINCT documentid, partytype, nullif(btrim(name), ''), nullif(btrim(address1), ''), nullif(btrim(address2), ''), nullif(btrim(zip), '')
FROM real_property_parties WHERE documentid = ANY(%(docs)s);
