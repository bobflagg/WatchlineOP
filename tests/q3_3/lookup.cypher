// Q3.3: who is recorded as the owner on the registrations of this lot's buildings? Reuses the Q2 path.
// Every registration is returned with all of its owner contacts; none is chosen as the owner.
MATCH (l:Lot {bbl: $bbl})-[:HAS_BUILDING]->(b:Building)-[:HAS_REGISTRATION]->(r:Registration)
OPTIONAL MATCH (r)-[:HAS_OWNER_CONTACT]->(c:OwnerContact)
WITH r, collect(DISTINCT b.bin) AS bins, collect(c {.contactType, .name, .mailingAddress, .addressLine2, .zip}) AS owners
RETURN r.registrationId AS registrationId, bins, owners
ORDER BY registrationId;
