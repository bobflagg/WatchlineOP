// Q11.3: which party does the NY DOS record name to receive service of process for this entity, and how many active DOS entities list that
// address? $nameKey is the given name after rule N3. Records are found by name key (a lead; several records can share a key and all are returned).
// The process contact is a recorded assertion by the filer, an "other" affiliation (service of process), never ownership, parenthood or
// management. A process address listed by many entities is a service-address lead: `entities` is DosEntity.processAddressEntities, a count over
// the whole active-entity table fixed at load. The process name can be a person or a company; person names are returned for the answer only.
// No row means no record in the active-entity snapshot, not that the entity does not exist.
OPTIONAL MATCH (e:DosEntity {nameKey: $nameKey})
RETURN e.dosId AS dosId, e.name AS name, e.entityType AS entityType, e.jurisdiction AS jurisdiction, e.filingDate AS filingDate,
       e.processName AS processName, e.processAddress AS processAddress, e.processCity AS processCity, e.processState AS processState,
       e.processZip AS processZip, e.processAddressEntities AS entities
ORDER BY dosId;
