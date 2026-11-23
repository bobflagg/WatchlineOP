// Q6.1: how many HPD contacts, registrations and buildings carry this business address?
// $street is the street line uppercased and trimmed; $zip5 is the first five characters of the ZIP. Both are as HPD records them,
// not abbreviated or corrected: "300 EAST2ND STREET" and "300 EAST 2ND STREET" are different addresses. A second line (unit, suite, floor)
// is not part of the key. Contacts whose duplicates disagree on a street line or ZIP have none and are not counted.
MATCH (c:Contact)
WHERE toUpper(c.mailingAddress) = $street AND left(c.zip, 5) = $zip5
OPTIONAL MATCH (r:Registration)-[:HAS_CONTACT]->(c)
OPTIONAL MATCH (b:Building)-[:HAS_REGISTRATION]->(r)
RETURN count(DISTINCT c) AS contacts,
       count(DISTINCT CASE WHEN c.contactType IN ['CorporateOwner', 'IndividualOwner', 'JointOwner'] THEN c END) AS ownerContacts,
       count(DISTINCT CASE WHEN NOT c.contactType IN ['CorporateOwner', 'IndividualOwner', 'JointOwner'] THEN c END) AS roleContacts,
       count(DISTINCT r) AS registrations,
       count(DISTINCT b) AS buildings;
