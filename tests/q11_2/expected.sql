-- Q11.2 expected answers: the contacts HPD records on the registrations where the entity is named, by role. Independent of the graph.
-- hpd_contacts (2026-05-29). Registrations are those with a contact whose corporation name equals the given name under rule N3.
-- Contacts are distinct (registrationid, type, corporation name, person name, title), as the graph keys them; the entity's own rows (corporation
-- name equal under N3) are returned as `own`.
WITH n AS (SELECT btrim(regexp_replace(replace(replace(replace(replace(upper(btrim(corporationname)), '.', ''), ',', ' '), '''', ''),
                  E'\t', ' '), '\s+', ' ', 'g')) AS k, registrationid FROM hpd_contacts WHERE corporationname IS NOT NULL),
regs AS (SELECT DISTINCT registrationid FROM n WHERE k = %(key)s)
SELECT c.registrationid, c.type,
       (btrim(regexp_replace(replace(replace(replace(replace(upper(btrim(coalesce(c.corporationname, ''))), '.', ''), ',', ' '), '''', ''),
            E'\t', ' '), '\s+', ' ', 'g')) = %(key)s) AS own,
       count(DISTINCT (c.corporationname, c.firstname, c.middleinitial, c.lastname, c.title)) AS contacts
FROM hpd_contacts c JOIN regs USING (registrationid)
GROUP BY 1, 2, 3 ORDER BY 1, 2, 3;
