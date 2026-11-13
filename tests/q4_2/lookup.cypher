// Q4.2: what business address does HPD record for each of those contacts? Absent means none recorded (or duplicates disagreed).
MATCH (b:Building {bin: $bin})-[:HAS_REGISTRATION]->(r:Registration)
OPTIONAL MATCH (r)-[:HAS_ROLE_CONTACT]->(c:RoleContact)
RETURN r.registrationId AS registrationId,
       collect(c {.contactType, .corporationName, .personName, .mailingAddress, .addressLine2, .zip}) AS contacts
ORDER BY registrationId;
