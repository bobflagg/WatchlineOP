-- Q12.1 expected answers: the deeds recorded against given lots in a period, with grantors and grantees. Independent of the graph.
-- real_property_master, real_property_parties, real_property_legals (frozen baseline, data/README.md). verified against it 2026-11-16.
-- Rules: a deed is a document whose CURRENT version (latest modifieddate, then goodthroughdate) has type DEED, DEED, TS, DEED, LE, DEED, RC, DEEDO,
-- DEEDP, CORRD or CONDEED (decision 2026-11-12). A deed on several lots is one deed. Period filter is on recordedfiled (inclusive, null = open).
-- Not a sale (decision 2026-11-16): amount 0, or type CORRD or CONDEED (a correction or confirmation re-records an earlier transfer).
-- Parties are distinct (name, address1, address2, zip) rows of partytype 1 (grantor) and 2 (grantee); a blank value is absent.
-- Anchor A lot 3008260002: 7 deeds, 2 since 2015-01-01 (2021022201130003 for $5,000,000; 2025032100031001 for $0, same name both sides).
WITH docs AS (SELECT DISTINCT l.documentid, l.bbl::text AS bbl FROM real_property_legals l WHERE l.bbl = ANY(%(bbls)s)),
cur AS (SELECT DISTINCT ON (m.documentid) m.documentid, m.doctype, m.docdate, m.recordedfiled, m.docamount
        FROM real_property_master m WHERE m.documentid IN (SELECT documentid FROM docs)
        ORDER BY m.documentid, m.modifieddate DESC NULLS LAST, m.goodthroughdate DESC NULLS LAST)
SELECT c.documentid, c.doctype, c.docdate::date, c.recordedfiled::date, c.docamount,
       (SELECT array_agg(DISTINCT d.bbl ORDER BY d.bbl) FROM docs d WHERE d.documentid = c.documentid) AS lots,
       p.partytype, nullif(btrim(p.name), '') AS name, nullif(btrim(p.address1), '') AS address1,
       nullif(btrim(p.address2), '') AS address2, nullif(btrim(p.zip), '') AS zip
FROM cur c LEFT JOIN (SELECT DISTINCT documentid, partytype, name, address1, address2, zip FROM real_property_parties
                  WHERE partytype IN (1, 2) AND documentid IN (SELECT documentid FROM docs)) p
     ON p.documentid = c.documentid
WHERE c.doctype = ANY(%(types)s)
  AND (%(start)s::date IS NULL OR c.recordedfiled::date >= %(start)s::date)
  AND (%(end)s::date IS NULL OR c.recordedfiled::date <= %(end)s::date)
ORDER BY c.recordedfiled, c.documentid, p.partytype, 8;
