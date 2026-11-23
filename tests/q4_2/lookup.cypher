// Q4.2: what business address does HPD record for each of those contacts? Absent means none recorded (or duplicates disagreed).
MATCH (b:Building {bin: $bin})-[:HAS_REGISTRATION]->(r:Registration)
OPTIONAL MATCH (r)-[:HAS_CONTACT]->(c:Contact)
WHERE NOT c.contactType IN ['CorporateOwner', 'IndividualOwner', 'JointOwner']
RETURN r.registrationId AS registrationId,
       collect(c {.contactType, .corporationName, .personName, .mailingAddress, .addressLine2, .zip}) AS contacts
ORDER BY registrationId;
