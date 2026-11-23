// Q28.2: do a building's case respondents match its registered owner? $bin is the building.
// Returns each case's respondent keys (N3 of each comma-separated part, a lead and not an identity) and the building's registered owner contacts
// (CorporateOwner, IndividualOwner, JointOwner) with the registration they belong to. The agent applies rule N3 (src/watchline/compare.py) to the
// owner names and answers: matched (which respondent, which owner, which registration), not matched, or not comparable (no respondent, or no owner
// name). A name match is a lead; it does not show the respondent is the owner, and a respondent may be an agent or an individual.
MATCH (b:Building {bin: $bin})-[:HAS_LITIGATION]->(c:Litigation)
WITH b, collect(c {.litigationId, .respondent, .respondentKeys}) AS cases
CALL (b) {
  OPTIONAL MATCH (b)-[:HAS_REGISTRATION]->(r:Registration)-[:HAS_CONTACT]->(o:Contact)
  WHERE o.contactType IN ['CorporateOwner', 'IndividualOwner', 'JointOwner']
  RETURN collect(o {registrationId: r.registrationId, .contactType, .corporationName, .personName}) AS owners
}
RETURN cases, owners;
