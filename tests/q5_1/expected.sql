-- Q5.1 expected answers for DosEntity, from the frozen JustFix/WoW snapshot. Independent of the loader.
-- dos_active_corporations (data through 2026-07-06), profiled read-only 2026-11-12. Provisional until the dump is identified (data/README.md).
--
-- Rules: a record is loaded when its name key equals the key of a CorporateOwner OwnerContact name or a Grantee name in the graph.
-- Key (rule N3) = uppercase, periods removed, commas to spaces, apostrophes removed, whitespace collapsed; spaces inside a name stay.
-- dosid is unique (4,242,054 rows). Name, jurisdiction and entity type are never blank except jurisdiction (119 of the scoped rows are null:
-- kept absent). Filing dates run 1861-01-01 to 2026-07-01 and none is in the future; they are kept as recorded.
-- Several DOS records can share one key (15 keys among HPD owner names, e.g. 2010 NEWKIRK REALTY: ids 1917183 and 5298391): all are candidates.

-- Candidates for one name. Replace the literal.
-- Expected '5413 PLAZA LLC': 5857246. '2010 NEWKIRK REALTY LLC': 1917183, 5298391. '438 52ND ST OWNERS CORP': 2733264.
-- '438 52 ST OWNERS CORP' (HPD spelling): none. 'HP SUNSET PARK I HDFC INC.': none. 'KS TURNPIKE LLC': none (K S TURNPIKE LLC is 3574572).
SELECT dosid, currententityname, entitytype, jurisdiction, initialdosfilingdate::date
FROM dos_active_corporations
WHERE regexp_replace(upper(replace(replace(replace(btrim(currententityname),'.',''),',',' '),'''','')),'\s+',' ','g')
    = regexp_replace(upper(replace(replace(replace(btrim('438 52ND ST OWNERS CORP'),'.',''),',',' '),'''','')),'\s+',' ','g')
ORDER BY dosid;
