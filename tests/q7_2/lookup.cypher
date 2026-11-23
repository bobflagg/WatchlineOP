// Q7.2: do the two entities' DOS records list the same process address, and how many active DOS entities list it?
// $nameKeyA and $nameKeyB are the given names after rule N3. Records are found by name key (a lead; several records can share a key and all are
// returned). The address key is the uppercase process street line plus the first five ZIP characters; line 2 is reported apart, never compared.
// entities is DosEntity.processAddressEntities, a count over the whole DOS active-entity table, fixed when loaded. No row for a side means no
// record in the active-entity snapshot, not that the entity does not exist.
OPTIONAL MATCH (a:DosEntity {nameKey: $nameKeyA})
WITH collect(a) AS recsA
OPTIONAL MATCH (b:DosEntity {nameKey: $nameKeyB})
WITH recsA, collect(b) AS recsB
RETURN [e IN recsA | e {.dosId, .name, .filingDate, .processAddress, .processAddressLine2, .processCity, .processState, .processZip,
                    entities: e.processAddressEntities}] AS recordsA,
       [e IN recsB | e {.dosId, .name, .filingDate, .processAddress, .processAddressLine2, .processCity, .processState, .processZip,
                    entities: e.processAddressEntities}] AS recordsB,
       [x IN recsA | [y IN recsB WHERE x.processAddress IS NOT NULL AND toUpper(x.processAddress) = toUpper(y.processAddress)
                   AND left(coalesce(x.processZip, ''), 5) = left(coalesce(y.processZip, ''), 5) | [x.dosId, y.dosId]]] AS sharedPairs;
