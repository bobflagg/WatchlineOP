-- Q11.3 expected answers: the DOS record of an entity, its process contact and the hub count of its process address. Independent of the graph.
-- dos_active_corporations (2026-07-06). Records are those whose entity name equals the given name under rule N3. Hub count = distinct dosid over the
-- whole table at the same upper-cased street line and first five ZIP characters. Expected '5413 PLAZA LLC' (5857246, filed 2020-10-14): process
-- address 5 CROMWELL CIRCLE 10304, listed by 5 active entities.
WITH d AS (SELECT *, btrim(regexp_replace(replace(replace(replace(replace(upper(btrim(currententityname)), '.', ''), ',', ' '), '''', ''),
                         E'\t', ' '), '\s+', ' ', 'g')) AS k FROM dos_active_corporations)
SELECT d.dosid, d.initialdosfilingdate::date AS filed, nullif(btrim(d.dosprocessname), '') IS NOT NULL AS has_process_name,
       nullif(btrim(d.dosprocessaddress1), '') AS street, left(btrim(coalesce(d.dosprocesszip, '')), 5) AS zip5,
       (SELECT count(DISTINCT x.dosid) FROM dos_active_corporations x
         WHERE upper(btrim(x.dosprocessaddress1)) = upper(btrim(d.dosprocessaddress1))
           AND left(btrim(coalesce(x.dosprocesszip, '')), 5) = left(btrim(coalesce(d.dosprocesszip, '')), 5)) AS entities
FROM d WHERE d.k = %(key)s ORDER BY d.dosid;
