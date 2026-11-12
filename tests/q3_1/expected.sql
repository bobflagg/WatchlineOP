-- Q3.1 expected answers for Deed nodes and HAS_DEED, from the frozen JustFix/WoW snapshot.
-- Independent of the loader. real_property_master (2026-05-29), real_property_legals (2026-05-31), checked read-only 2026-11-12.
-- Provisional until the dump is identified (data/README.md).
--
-- Rules:
--  * Scope: lots in the rental-market scope (HPD-registered, plus unregistered pluto_latest lots with unitsres >= 3).
--  * Deed types (decision 2026-11-12): DEED, DEED TS, DEED LE, DEED RC, DEEDO, DEEDP, CORRD, CONDEED.
--    DEED COR (index correction, office use), RPTT, ASST and every other type are not deeds here.
--  * real_property_master repeats a documentid (14957 documents). The current version is the row with the latest
--    modifieddate (then goodthroughdate); the type test is applied to that version. No ties occur (profiled).
--  * Deed.recordedDate = recordedfiled (never null on deeds). docDate is absent when null (95344 deed rows).
--    amount is kept as recorded; 0 does not mean a free sale.
--  * HAS_DEED = distinct (bbl, documentid) in real_property_legals. A deed can sit on several lots.
--  * "Most recent" = latest recordedDate. Deeds that tie on it are all returned, none chosen.

-- Deeds of one lot, newest first. Replace the BBL to check another.
-- Expected 3008260002 (anchor A): 2025032100031001 recorded 2025-04-02 (doc date 2025-03-14, amount 0), then 2021022201130003 (2021-02-26, 5000000).
-- Expected 3008210012 (anchor D): TWO deeds tied on 2017-06-28: 2017061600025001 (amount 0) and 2017061600025002 (amount 45839605).
-- Expected 3008080025 (anchor G): 2018092900072001 recorded 2018-10-18 (doc date 2018-09-26, amount 4000000).
-- Expected 3008150031: latest eligible is FT_3250000923125 (1982-08-18); the later DEED COR 2005072601564001 is excluded.
-- Expected 3008000019: latest is 2025071300004001, type 'DEED, LE' (a variant type, kept and shown).
-- Expected 3008010039: 2015081800619001 recorded 2015-09-03 on four lots (a multi-lot deed).
WITH cur AS (
  SELECT DISTINCT ON (m.documentid) m.documentid, m.doctype, m.docdate, m.recordedfiled, m.docamount
  FROM real_property_master m
  WHERE m.documentid IN (SELECT documentid FROM real_property_legals WHERE bbl = '3008260002')
  ORDER BY m.documentid, m.modifieddate DESC NULLS LAST, m.goodthroughdate DESC NULLS LAST)
SELECT c.documentid, c.doctype, c.docdate, c.recordedfiled, c.docamount
FROM cur c
WHERE c.doctype IN ('DEED','DEED, TS','DEED, LE','DEED, RC','DEEDO','DEEDP','CORRD','CONDEED')
ORDER BY c.recordedfiled DESC, c.documentid;

-- Totals over the whole scope: see check_deeds.py (SOURCE_TOTALS). Expected values are in fixtures.yaml.
