-- Q15.3 expected answers: the pest violations of a building, by pest kind and status. Independent of the graph.
-- hpd_violations (data through 2026-07-02) and hpd_registrations (frozen baseline, data/README.md).
-- Rules (Q15 pest extension, 2026-11-21): same scope as Q15.1 (BBL HPD-registered, BIN a registered valid BIN). A pest violation is one whose
-- order code (ordernumber) is listed in data/hpd_pest_orders.yaml; the kind comes from that list, never from the description. Descriptions name
-- apartments and are not used. Open = violationstatus 'Open' at the snapshot. Counting unit: distinct violations. %(codes)s is the listed codes.
-- Expected: anchor C (BIN 3013901): roaches 1 open (oldest 2023-03-25), no mice; anchor A (BIN 3014788): none.
WITH rbin AS (SELECT DISTINCT bin FROM hpd_registrations WHERE bbl IS NOT NULL AND bin ~ '^[1-5][0-9]{6}$' AND bin !~ '000000$'),
     rb AS (SELECT DISTINCT bbl FROM hpd_registrations WHERE bbl IS NOT NULL)
SELECT v.ordernumber, v.violationstatus, count(*) AS violations, min(v.inspectiondate)::date AS oldest_inspection
FROM hpd_violations v JOIN rb ON rb.bbl = v.bbl JOIN rbin ON rbin.bin = v.bin
WHERE v.bin = %(bin)s AND v.ordernumber = ANY(%(codes)s)
GROUP BY v.ordernumber, v.violationstatus ORDER BY v.ordernumber, v.violationstatus;

-- Totals by order code in scope. Expected loaded rows: 566 6,366; 567 3,697; 568 65,004; 569 56,562; 866 640; 867 184; 868 2,562; 869 2,631
-- (queried 2026-11-21); every loaded row has an order code (0 null, 0 non-numeric; 364 distinct codes).
SELECT v.ordernumber, count(*) AS loaded, count(*) FILTER (WHERE v.violationstatus = 'Open') AS loaded_open
FROM hpd_violations v
JOIN (SELECT DISTINCT bbl FROM hpd_registrations WHERE bbl IS NOT NULL) rb ON rb.bbl = v.bbl
JOIN (SELECT DISTINCT bin FROM hpd_registrations WHERE bbl IS NOT NULL AND bin ~ '^[1-5][0-9]{6}$' AND bin !~ '000000$') rbin ON rbin.bin = v.bin
WHERE v.ordernumber = ANY(%(codes)s)
GROUP BY v.ordernumber ORDER BY v.ordernumber;

-- Order codes on loaded rows: no null, blank or non-numeric code.
SELECT count(*) AS loaded, count(*) FILTER (WHERE v.ordernumber IS NULL OR v.ordernumber !~ '^[0-9]+$') AS bad_order
FROM hpd_violations v
JOIN (SELECT DISTINCT bbl FROM hpd_registrations WHERE bbl IS NOT NULL) rb ON rb.bbl = v.bbl
JOIN (SELECT DISTINCT bin FROM hpd_registrations WHERE bbl IS NOT NULL AND bin ~ '^[1-5][0-9]{6}$' AND bin !~ '000000$') rbin ON rbin.bin = v.bin;
