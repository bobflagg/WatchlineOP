-- Q11.1 expected answers: mortgages (current document type MTGE) naming the given entity, with every party's role.
-- real_property_master / real_property_parties (frozen baseline, data/README.md). Independent of the graph.
-- Role is the recorded partytype on a mortgage: 1 = borrower, 2 = lender (profiled 2026-11-16: an MTGE has only types 1 and 2).
-- A name match (rule N3) is a lead, not a finding of the same party. Amounts are whole dollars; the cents are not carried.
-- Scope M total (documents naming at least one HPD corporate owner, N3) is counted by scripts/profile_q11_scope.py: 492,092.
WITH cur AS (SELECT DISTINCT ON (documentid) documentid, doctype, docdate, recordedfiled, docamount
             FROM real_property_master WHERE documentid IN (SELECT documentid FROM real_property_parties WHERE upper(btrim(name)) = %(name)s)
             ORDER BY documentid, modifieddate DESC NULLS LAST, goodthroughdate DESC NULLS LAST)
SELECT c.documentid, c.recordedfiled::date AS recorded, c.docdate::date AS docdate, c.docamount,
       p.partytype, nullif(btrim(p.name), '') AS name, nullif(btrim(p.address1), '') AS address1, nullif(btrim(p.zip), '') AS zip
FROM cur c JOIN real_property_parties p USING (documentid)
WHERE c.doctype = 'MTGE'
ORDER BY c.recordedfiled DESC, c.documentid, p.partytype, 6;
