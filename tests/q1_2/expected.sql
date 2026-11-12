-- Q1.2 expected answers for Building nodes and HAS_BUILDING, from the frozen JustFix/WoW snapshot.
-- Independent of the loader. hpd_registrations (2026-05-29) and pluto_latest (26v1), checked read-only 2026-11-11.
-- Provisional until the dump is identified (data/README.md).
--
-- Rules: a valid BIN matches ^[1-5][0-9]{6}$ and does not end in 000000; other BINs are excluded.
-- A Lot has a Building for each distinct valid BIN registered on its BBL. Building.address = house number and
-- street name from that BIN's most recent registrations (lastregistrationdate, then registrationid, descending).
-- registrationid repeats, so they can tie; if they name more than one address, Building.address is absent.
-- Lot.plutoNumBuildings = PLUTO numbldgs as recorded; it is PLUTO's count, not the number of Buildings.

-- Buildings of one lot. Replace the BBL to check another.
-- Expected for 3008210012 (anchor D, PLUTO numbldgs 3): 3324448 '218 54TH STREET', 3324450 '220 54TH STREET', 3324451 '224 54TH STREET'.
-- Expected for 3008260002 (anchor A, numbldgs 1): 3014788 '5413 SEVENTH AVENUE'.
-- Expected for 3008970014 (anchor F, numbldgs 1): no buildings (no registration).
-- Expected for 3008000009 (numbldgs 3): 3337249 '506 51ST STREET', 3337250 '5103 FIFTH AVENUE' (PLUTO counts more than registered).
-- Expected for 3008360065 (numbldgs 1): no buildings (its only BIN is the placeholder 3000000).
-- Expected for 1002360018 (not in PLUTO, so no plutoNumBuildings) and 1002367504 (numbldgs 1): both have 1003074 '185 GRAND STREET' (one BIN on two lots).
-- Expected for 4087430102 (numbldgs 75): includes 4445478 with NO address. That BIN is on 103 registrations of one registrationid
--   with different house numbers, so the tied most recent registrations name many addresses.
SELECT b.bin,
       (SELECT CASE WHEN count(DISTINCT a) = 1 THEN min(a) END
        FROM (SELECT nullif(btrim(concat_ws(' ', r2.housenumber, r2.streetname)), '') AS a,
                     rank() OVER (ORDER BY r2.lastregistrationdate DESC NULLS LAST, r2.registrationid DESC) AS rk
              FROM hpd_registrations r2 WHERE r2.bin = b.bin AND r2.bbl IS NOT NULL) x
        WHERE rk = 1) AS address
FROM (SELECT DISTINCT bin FROM hpd_registrations
      WHERE bbl = '3008210012' AND bin ~ '^[1-5][0-9]{6}$' AND bin !~ '000000$') b
ORDER BY b.bin;

-- Totals. Expected: 200408 distinct valid BINs; 200648 distinct (BBL, BIN) pairs; 761 registration rows excluded for an invalid or placeholder BIN.
SELECT (SELECT count(DISTINCT bin) FROM hpd_registrations WHERE bbl IS NOT NULL AND bin ~ '^[1-5][0-9]{6}$' AND bin !~ '000000$') AS buildings,
       (SELECT count(*) FROM (SELECT DISTINCT bbl, bin FROM hpd_registrations
                              WHERE bbl IS NOT NULL AND bin ~ '^[1-5][0-9]{6}$' AND bin !~ '000000$') x) AS pairs,
       (SELECT count(*) FROM hpd_registrations
        WHERE bbl IS NOT NULL AND NOT (bin ~ '^[1-5][0-9]{6}$' AND bin !~ '000000$')) AS excluded_rows;
