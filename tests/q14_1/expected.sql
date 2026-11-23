-- Q14.1 expected answers: the deeds that support the title holder of a lot on a date. Independent of the graph.
-- real_property_master, real_property_parties, real_property_legals (frozen baseline, data/README.md).
-- Rules (decision 2026-11-17): the deeds are those of Q12.1 (current version of each document, the eight deed types, a multi-lot deed is one deed).
-- The date of a deed depends on the basis. basis 'document': the document date, or the recorded date when the document date is absent
-- (as now known; the deed may have been unrecorded on the date). basis 'recorded': the recorded date (what public record showed on the date).
-- The supporting deeds are those with the latest date on or before the given date. Deeds that tie are all returned, none is chosen.
-- A grantee is a title holder lead, not proof of title. No deed on or before the date is "no title record in the snapshot", not "no owner".
WITH docs AS (SELECT DISTINCT l.documentid, l.bbl::text AS bbl FROM real_property_legals l WHERE l.bbl = ANY(%(bbls)s)),
cur AS (SELECT DISTINCT ON (m.documentid) m.documentid, m.doctype, m.docdate::date AS docdate, m.recordedfiled::date AS recorded, m.docamount
        FROM real_property_master m WHERE m.documentid IN (SELECT documentid FROM docs)
        ORDER BY m.documentid, m.modifieddate DESC NULLS LAST, m.goodthroughdate DESC NULLS LAST),
eff AS (SELECT d.bbl, c.*, CASE WHEN %(basis)s = 'recorded' THEN c.recorded ELSE coalesce(c.docdate, c.recorded) END AS eff_date
        FROM docs d JOIN cur c USING (documentid) WHERE c.doctype = ANY(%(types)s)),
sup AS (SELECT e.* FROM eff e WHERE e.eff_date <= %(date)s::date
        AND e.eff_date = (SELECT max(x.eff_date) FROM eff x WHERE x.bbl = e.bbl AND x.eff_date <= %(date)s::date))
SELECT s.bbl, s.documentid, s.doctype, s.docdate, s.recorded, s.docamount, s.eff_date,
       (s.docdate IS NULL) AS doc_date_absent, (s.recorded > %(date)s::date) AS recorded_after_date,
       (s.doctype IN ('CORRD', 'CONDEED')) AS confirmatory,
       p.name AS grantee
FROM sup s LEFT JOIN (SELECT DISTINCT documentid, nullif(btrim(name), '') AS name FROM real_property_parties
                      WHERE partytype = 2 AND documentid IN (SELECT documentid FROM docs)) p ON p.documentid = s.documentid
ORDER BY s.bbl, s.documentid, p.name;
