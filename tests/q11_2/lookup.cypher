// Q11.2: which parties does HPD record alongside this entity, in which roles? $nameKey is the given name after rule N3
// (src/watchline/compare.py n3). An entity's registrations are those where a Contact with that name key appears (a lead found by name,
// never a stored link). givenTypes is the entity's own role(s) on the registration (an entity can be an owner, or a managing agent). Every
// other contact on the registration is a recorded party with its role (contactType), name, business address and, for officers, a title.
// Each is a documented (recorded) assertion by the registrant. Which relationship it is comes from the role, not from this query
// (answer contract, vocabulary scheme affiliation-types): owner roles and Shareholder = ownership, Agent and SiteManager = management,
// HeadOfficer, Officer and Lessee = other. A disclosed managing agent is not an owner; no HPD role records a parent company.
// Person names are returned for the answer only; checks never print them.
MATCH (:Contact {nameKey: $nameKey})<-[:HAS_CONTACT]-(r:Registration)
WITH DISTINCT r
CALL (r) {
  MATCH (r)-[:HAS_CONTACT]->(g:Contact {nameKey: $nameKey})
  RETURN collect(DISTINCT g.contactType) AS givenTypes
}
CALL (r) {
  MATCH (r)-[:HAS_CONTACT]->(c:Contact) WHERE c.nameKey IS NULL OR c.nameKey <> $nameKey
  RETURN collect(c {.contactType, .corporationName, .personName, .title, .mailingAddress, .zip}) AS others
}
RETURN r.registrationId AS registrationId, givenTypes, others
ORDER BY registrationId;
