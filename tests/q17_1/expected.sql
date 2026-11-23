-- Q17.1 expected answers: is a lot's registration missing? Independent of the graph. hpd_registrations, pluto_latest (frozen baseline, 2026-05-29).
-- Rules (decision 2026-11-18): the lot has a registration row (hpd_row) or not. A registration is one (valid BIN, registrationid > 0) pair on a row of
-- the lot (Q2.1); placeholder id 0 and missing or placeholder BINs are not usable. A lot with rows but no usable pair is registered with
-- no usable registration. Registered buildings are the distinct valid BINs. PLUTO's building count is kept as recorded (absent when null or not in PLUTO).
SELECT EXISTS (SELECT 1 FROM hpd_registrations WHERE bbl::text = %(bbl)s) AS hpd_row,
       (SELECT count(*) FROM (SELECT DISTINCT registrationid, btrim(bin) FROM hpd_registrations
                              WHERE bbl::text = %(bbl)s AND bin ~ '^[1-5][0-9]{6}$' AND bin !~ '000000$' AND registrationid > 0) x) AS registrations,
       (SELECT count(DISTINCT btrim(bin)) FROM hpd_registrations
         WHERE bbl::text = %(bbl)s AND bin ~ '^[1-5][0-9]{6}$' AND bin !~ '000000$' AND registrationid > 0) AS registered_buildings,
       (SELECT numbldgs FROM pluto_latest WHERE bbl::text = %(bbl)s) AS pluto_num_buildings;
