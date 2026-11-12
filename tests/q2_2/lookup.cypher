// Q2.2: who is the registered owner on each of this building's registrations?
// Contacts belong to the registration; a registration with none returns an empty list.
MATCH (b:Building {bin: $bin})-[:HAS_REGISTRATION]->(r:Registration)
OPTIONAL MATCH (r)-[:HAS_OWNER_CONTACT]->(c:OwnerContact)
RETURN r.registrationId AS registrationId, collect(c {.contactType, .name}) AS owners
ORDER BY registrationId;
