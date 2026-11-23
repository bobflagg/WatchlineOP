-- Q17.2 expected answers: the registrations of a lot with their dates, from which lapsed is derived. Independent of the graph.
-- hpd_registrations (frozen baseline, 2026-05-29). Same registration rule as Q14.2: one (valid BIN, registrationid > 0) pair on a row of the lot;
-- the pair's last registration and end dates are those of its rows when they all agree, otherwise absent. Lapsed is derived by the check from the
-- end dates against the as-of date: holds when every registration ended before it, does-not-hold when any has not, cannot-tell otherwise.
WITH rows AS (SELECT registrationid::bigint AS rid, btrim(bin) AS bin, lastregistrationdate AS lr, registrationenddate AS re
              FROM hpd_registrations WHERE bbl::text = %(bbl)s AND bin ~ '^[1-5][0-9]{6}$' AND bin !~ '000000$' AND registrationid > 0)
SELECT bin, rid,
       CASE WHEN count(DISTINCT lr) = 1 AND count(lr) = count(*) THEN min(lr)::date END AS last_registered,
       CASE WHEN count(DISTINCT re) = 1 AND count(re) = count(*) THEN min(re)::date END AS registration_end
FROM rows GROUP BY rid, bin ORDER BY bin, rid;
