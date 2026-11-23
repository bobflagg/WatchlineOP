// Q4.1: which contacts other than the registered owner does HPD list on each of this building's registrations, in what role?
// Owner contacts come from Q2.2. Contacts belong to the registration; a registration with none returns an empty list.
MATCH (b:Building {bin: $bin})-[:HAS_REGISTRATION]->(r:Registration)
OPTIONAL MATCH (r)-[:HAS_CONTACT]->(c:Contact)
WHERE NOT c.contactType IN ['CorporateOwner', 'IndividualOwner', 'JointOwner']
RETURN r.registrationId AS registrationId,
       collect(c {.contactType, .title, .corporationName, .personName}) AS contacts
ORDER BY registrationId;
