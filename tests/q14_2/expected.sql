-- Q14.2 expected answers: the HPD registrations of a lot's buildings and their status on a date, with the owner contacts. Independent of the graph.
-- hpd_registrations, hpd_contacts (frozen baseline, 2026-05-29).
-- Rules (decision 2026-11-17): a registration is one (valid BIN, registrationid > 0) pair on a row of the lot (Q2.1); the pair's dates are those of its
-- rows when they all agree, otherwise absent. The source has the last registration date and an end date, not a start, and keeps one row per
-- pair, so an earlier filing of the same registration is gone: the records are today's version of the past.
-- Status on the date: registered-later (last registered after the date), ended (end before the date), undated (no last registered date),
-- end-unknown (rows disagree on the end), in-force (last registered on or before the date and end on or after it). In force describes HPD's
-- registration period, not a finding that the owner was responsible.
-- Owner contacts are the CorporateOwner, IndividualOwner and JointOwner contacts (decision 2026-11-12); the corporate names carry rule N3 keys.
WITH rows AS (SELECT registrationid::bigint AS rid, btrim(bin) AS bin, bbl::text AS bbl, lastregistrationdate AS lr, registrationenddate AS re
              FROM hpd_registrations WHERE bbl IS NOT NULL AND bin ~ '^[1-5][0-9]{6}$' AND bin !~ '000000$' AND registrationid > 0),
pairs AS (SELECT rid, bin,
                 CASE WHEN count(DISTINCT lr) = 1 AND count(lr) = count(*) THEN min(lr) END AS last_registered,
                 CASE WHEN count(DISTINCT re) = 1 AND count(re) = count(*) THEN min(re) END AS reg_end,
                 array_agg(DISTINCT bbl) AS bbls
          FROM rows GROUP BY rid, bin),
pl AS (SELECT p.rid, p.bin, b AS bbl, p.last_registered, p.reg_end FROM pairs p, unnest(p.bbls) AS b WHERE b = ANY(%(bbls)s))
SELECT pl.bbl, pl.bin, pl.rid, pl.last_registered::date, pl.reg_end::date,
       CASE WHEN pl.last_registered > %(date)s::date THEN 'registered-later'
            WHEN pl.reg_end < %(date)s::date THEN 'ended'
            WHEN pl.last_registered IS NULL THEN 'undated'
            WHEN pl.reg_end IS NULL THEN 'end-unknown'
            ELSE 'in-force' END AS status,
       (SELECT array_agg(DISTINCT btrim(regexp_replace(replace(replace(replace(replace(upper(btrim(c.corporationname)), '.', ''), ',', ' '), '''', ''), E'\t', ' '), '\s+', ' ', 'g')))
          FROM hpd_contacts c WHERE c.registrationid = pl.rid AND c.type = 'CorporateOwner' AND nullif(btrim(c.corporationname), '') IS NOT NULL) AS corporate_keys,
       (SELECT count(*) FROM hpd_contacts c WHERE c.registrationid = pl.rid AND c.type IN ('IndividualOwner', 'JointOwner')) > 0 AS has_individual_owner
FROM pl ORDER BY pl.bbl, pl.bin, pl.rid;
