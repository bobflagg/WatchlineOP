// Q2.2: who is the registered owner on each of this building's registrations?
// Contacts belong to the registration; a registration with none returns an empty list.
MATCH (b:Building {bin: $bin})-[:HAS_REGISTRATION]->(r:Registration)
OPTIONAL MATCH (r)-[:HAS_CONTACT]->(c:Contact)
WHERE c.contactType IN ['CorporateOwner', 'IndividualOwner', 'JointOwner']
RETURN r.registrationId AS registrationId, collect(c {.contactType, .corporationName, .personName}) AS owners
ORDER BY registrationId;
