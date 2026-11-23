-- Q23.2 expected lots of the reference building (by BIN) from the frozen snapshot; the footprint is Q23.1's expected.sql.
-- Layer membership comes from the pinned BOR release (see check_layers.py), not the database. verified against the frozen baseline (data/README.md, 2026-11-16).
-- Parameter: %(bin)s. A BIN on two lots returns both lots (one answer row each).
SELECT DISTINCT bbl::text FROM hpd_registrations
WHERE bin = %(bin)s AND bbl IS NOT NULL AND bin ~ '^[1-5][0-9]{6}$' AND bin !~ '000000$' AND registrationid > 0;
