-- Q1.1 expected answers for the Lot nodes, from the frozen JustFix/WoW snapshot.
-- Independent of the loader: plain SQL on pluto_latest (26v1) and hpd_registrations (2026-05-29).
-- Values below were checked read-only on 2026-11-11 and are provisional until the dump is identified.
--
-- Lot rules: a Lot exists for every BBL in hpd_registrations, plus every pluto_latest lot with
-- unitsres >= 3 that is not registered. address = PLUTO address; if the BBL is not in PLUTO, the address of its
-- most recent registrations (lastregistrationdate, then registrationid, descending). registrationid repeats, so
-- they can tie; if they name more than one address, address is absent.
-- hpdRegistered = the BBL has at least one row in hpd_registrations.

-- Case 1: anchors A, D and F (F is the unregistered 3+ unit lot).
-- Expected:
--   3008210012  '224 54 STREET'  hpd_registered = true    (anchor D)
--   3008260002  '5413 7 AVENUE'  hpd_registered = true    (anchor A)
--   3008970014  '259 22 STREET'  hpd_registered = false   (anchor F, 40 units)
SELECT p.bbl, p.address,
       EXISTS (SELECT 1 FROM hpd_registrations r WHERE r.bbl = p.bbl) AS hpd_registered
FROM pluto_latest p
WHERE p.bbl IN ('3008260002', '3008210012', '3008970014')
ORDER BY p.bbl;

-- Case 2: registered BBL missing from PLUTO, two registrations on the same date.
-- Expected: BBL 1005560059, address '76 THIRD AVENUE' (registration 115445 beats 115444), hpd_registered = true.
SELECT r.bbl, r.registrationid, r.lastregistrationdate,
       btrim(concat_ws(' ', r.housenumber, r.streetname)) AS address
FROM hpd_registrations r
WHERE r.bbl = '1005560059'
ORDER BY r.lastregistrationdate DESC NULLS LAST, r.registrationid DESC;

-- Case 3: totals. Expected: registered 181863; unregistered 3+ unit PLUTO lots 32936; total Lot nodes 214799.
SELECT (SELECT count(DISTINCT bbl) FROM hpd_registrations WHERE bbl IS NOT NULL) AS registered_bbl,
       (SELECT count(*) FROM (SELECT bbl FROM pluto_latest WHERE unitsres >= 3
                              EXCEPT SELECT bbl FROM hpd_registrations) x) AS unregistered_3plus,
       (SELECT count(*) FROM (SELECT bbl FROM pluto_latest WHERE unitsres >= 3
                              UNION SELECT bbl FROM hpd_registrations WHERE bbl IS NOT NULL) y) AS total_lots;
