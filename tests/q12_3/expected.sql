-- Q12.3 expected answers: which deeds on given lots name a currently registered corporate owner of that lot as grantor or grantee. Independent of the graph.
-- hpd_registrations, hpd_contacts (2026-05-29); real_property_master, _parties, _legals (frozen baseline, data/README.md).
-- Rules (decision 2026-11-16): the current owners of a lot are the CorporateOwner contacts (corporation name, rule N3) on the HPD registrations whose bbl is
-- the lot (registrationid > 0, valid BIN). A deed party matches when its name equals an owner name under rule N3. The match is a lead, not a finding of
-- the same party. A transfer is attributable when a grantee or a grantor matches an owner of a lot the deed covers; it says which side. A lot with
-- no corporate owner (none registered, or only individuals, whose names HPD and ACRIS spell in different orders) is "owner not comparable".
-- Current registration is not historical ownership: an old deed can match the present owner by name only.
WITH owners AS (
  SELECT DISTINCT r.bbl::text AS bbl, btrim(regexp_replace(replace(replace(replace(replace(upper(btrim(c.corporationname)), '.', ''), ',', ' '), '''', ''), E'\t', ' '), '\s+', ' ', 'g')) AS k
  FROM hpd_registrations r JOIN hpd_contacts c ON c.registrationid = r.registrationid
  WHERE r.bbl = ANY(%(bbls)s) AND r.registrationid > 0 AND r.bin ~ '^[1-5][0-9]{6}$' AND r.bin !~ '000000$'
    AND c.type = 'CorporateOwner' AND nullif(btrim(c.corporationname), '') IS NOT NULL),
docs AS (SELECT DISTINCT l.documentid, l.bbl::text AS bbl FROM real_property_legals l WHERE l.bbl = ANY(%(bbls)s)),
cur AS (SELECT DISTINCT ON (m.documentid) m.documentid, m.doctype, m.recordedfiled
        FROM real_property_master m WHERE m.documentid IN (SELECT documentid FROM docs)
        ORDER BY m.documentid, m.modifieddate DESC NULLS LAST, m.goodthroughdate DESC NULLS LAST)
SELECT d.documentid, d.bbl,
       (SELECT count(DISTINCT o.k) FROM owners o WHERE o.bbl = d.bbl) AS corporate_owners,
       bool_or(p.partytype = 2 AND o.k IS NOT NULL) AS grantee_match,
       bool_or(p.partytype = 1 AND o.k IS NOT NULL) AS grantor_match
FROM docs d JOIN cur c USING (documentid)
LEFT JOIN (SELECT DISTINCT documentid, partytype, name FROM real_property_parties
                  WHERE partytype IN (1, 2) AND documentid IN (SELECT documentid FROM docs)) p ON p.documentid = d.documentid
LEFT JOIN owners o ON o.bbl = d.bbl AND o.k = btrim(regexp_replace(replace(replace(replace(replace(upper(btrim(p.name)), '.', ''), ',', ' '), '''', ''), E'\t', ' '), '\s+', ' ', 'g'))
WHERE c.doctype = ANY(%(types)s)
  AND (%(start)s::date IS NULL OR c.recordedfiled::date >= %(start)s::date)
  AND (%(end)s::date IS NULL OR c.recordedfiled::date <= %(end)s::date)
GROUP BY d.documentid, d.bbl
ORDER BY d.documentid, d.bbl;
