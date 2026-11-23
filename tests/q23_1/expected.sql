-- Q23.1 expected footprint of a managing agent name, from the frozen JustFix/WoW snapshot. Parameter: %(prefix)s (an upper-case LIKE prefix to narrow rows;
-- the check then keeps rows whose name has the fixture's N3 key, so the spelling rule is applied in code, not here).
-- Independent of the loader. verified against the frozen baseline recorded in data/README.md (2026-11-16).
--
-- Rules: a managing agent is a contact of type Agent with a corporation name. Registrations count only if the graph holds them (valid BIN, not a
-- placeholder, registrationid > 0, lot present). Counting units: distinct registrations, distinct BIN, distinct BBL.
-- Expected 'BRIGHTON MANAGEMENT': 40 registrations, 40 buildings, 39 lots; 'BRIGHTON MANAGEMENT LLC': 2, 2, 2 (a different N3 key).
-- Lots are the lots of those buildings (every lot on which HPD records the BIN, via q23_support.lots_of_bins), as in the graph's Lot-HAS_BUILDING->Building.
-- Expected 'DOUGLAS ELLIMAN PROPERTY MANAGEMENT': 435 registrations, 508 buildings, 309 lots.
SELECT DISTINCT c.registrationid, c.type, nullif(btrim(c.corporationname), '') AS corporation, r.bbl::text, r.bin
FROM hpd_contacts c
JOIN hpd_registrations r ON r.registrationid = c.registrationid
WHERE c.type = 'Agent' AND nullif(btrim(c.corporationname), '') IS NOT NULL
  AND upper(btrim(c.corporationname)) LIKE %(prefix)s
  AND r.bbl IS NOT NULL AND r.bin ~ '^[1-5][0-9]{6}$' AND r.bin !~ '000000$' AND r.registrationid > 0;
