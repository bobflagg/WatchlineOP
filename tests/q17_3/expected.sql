-- Q17.3 expected answers: the latest deed of a lot (by recorded date) and the lot's latest registration date. Independent of the graph.
-- real_property_master, real_property_legals, hpd_registrations (frozen baseline, 2026-05-29). Deeds are those of Q12.1 (current version of each
-- document, the eight deed types, a multi-lot deed is one deed). Deeds recorded on the latest date all come back, none is chosen.
-- The check derives older-than-the-latest-deed: holds when the latest registration date is before the deed's recorded date, does-not-hold when
-- it is the same day or later, cannot-tell with no deed, no dated registration or no registration.
WITH docs AS (SELECT DISTINCT l.documentid FROM real_property_legals l WHERE l.bbl::text = %(bbl)s),
cur AS (SELECT DISTINCT ON (m.documentid) m.documentid, m.doctype, m.docdate::date AS docdate, m.recordedfiled::date AS recorded, m.docamount
        FROM real_property_master m WHERE m.documentid IN (SELECT documentid FROM docs)
        ORDER BY m.documentid, m.modifieddate DESC NULLS LAST, m.goodthroughdate DESC NULLS LAST),
deeds AS (SELECT * FROM cur WHERE doctype = ANY(%(types)s)),
regrows AS (SELECT registrationid::bigint AS rid, btrim(bin) AS bin, lastregistrationdate AS lr
            FROM hpd_registrations WHERE bbl::text = %(bbl)s AND bin ~ '^[1-5][0-9]{6}$' AND bin !~ '000000$' AND registrationid > 0),
pairs AS (SELECT rid, bin, CASE WHEN count(DISTINCT lr) = 1 AND count(lr) = count(*) THEN min(lr)::date END AS lr FROM regrows GROUP BY rid, bin),
latest AS (SELECT max(lr) AS latest_registered, count(*) AS n_pairs FROM pairs)
SELECT d.documentid, d.doctype, d.docdate, d.recorded, d.docamount, lt.latest_registered, lt.n_pairs
FROM latest lt LEFT JOIN deeds d ON d.recorded = (SELECT max(recorded) FROM deeds)
ORDER BY d.documentid;
