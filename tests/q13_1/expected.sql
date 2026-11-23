-- Q13.1 expected answers: the financing documents recorded against a lot. Independent of the graph.
-- real_property_master, real_property_legals (frozen baseline, data/README.md).
-- Rules (decision 2026-11-17): a financing document is a document whose CURRENT version (latest modifieddate, then goodthroughdate) has type
-- MTGE, ASST, SAT, AGMT, AL&R, TL&R or SAGE. A document on several lots is one document. Dates and amount are as recorded (docdate may be
-- null; amount is whole dollars, 0 kept). Anchor C lot 3008070024: 17 documents; anchor A lot 3008260002: 11 documents.
WITH docs AS (SELECT DISTINCT l.documentid, l.bbl::text AS bbl FROM real_property_legals l WHERE l.bbl = ANY(%(bbls)s)),
cur AS (SELECT DISTINCT ON (m.documentid) m.documentid, m.doctype, m.docdate, m.recordedfiled, m.docamount
        FROM real_property_master m WHERE m.documentid IN (SELECT documentid FROM docs)
        ORDER BY m.documentid, m.modifieddate DESC NULLS LAST, m.goodthroughdate DESC NULLS LAST)
SELECT c.documentid, c.doctype, c.docdate::date, c.recordedfiled::date, c.docamount,
       (SELECT array_agg(DISTINCT d.bbl ORDER BY d.bbl) FROM docs d WHERE d.documentid = c.documentid) AS lots
FROM cur c WHERE c.doctype = ANY(%(types)s)
ORDER BY c.recordedfiled, c.documentid;
