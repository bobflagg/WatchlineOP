// Q7.1: which business addresses and people on HPD registration contacts do the two entities share, and how many other registrations
// carry each address? $nameKeyA and $nameKeyB are the given names after rule N3 (src/watchline/compare.py n3). An entity's registrations
// are those where a Contact with that name key appears (found by name: a lead, never a stored link). Both sides then take every contact on
// those registrations, whatever its type. An address is the uppercase street line plus the first five ZIP characters (as Q6.1); a person is
// equal by uppercase person name. The second line is not compared. Person names are returned for the answer only; checks never print them.
MATCH (:Contact {nameKey: $nameKeyA})<-[:HAS_CONTACT]-(ra:Registration)
WITH collect(DISTINCT ra) AS regsA
MATCH (:Contact {nameKey: $nameKeyB})<-[:HAS_CONTACT]-(rb:Registration)
WITH regsA, collect(DISTINCT rb) AS regsB
CALL (regsA, regsB) {
  UNWIND regsA AS r
  MATCH (r)-[:HAS_CONTACT]->(c:Contact) WHERE c.mailingAddress IS NOT NULL AND c.zip IS NOT NULL
  WITH regsB, toUpper(c.mailingAddress) AS street, left(c.zip, 5) AS zip5, collect(DISTINCT c.contactType) AS typesA
  CALL (regsB, street, zip5) {
    UNWIND regsB AS r2
    MATCH (r2)-[:HAS_CONTACT]->(c2:Contact) WHERE toUpper(c2.mailingAddress) = street AND left(c2.zip, 5) = zip5
    RETURN collect(DISTINCT c2.contactType) AS typesB
  }
  WITH street, zip5, typesA, typesB WHERE size(typesB) > 0
  CALL (street, zip5) {
    MATCH (h:Contact) WHERE toUpper(h.mailingAddress) = street AND left(h.zip, 5) = zip5
    OPTIONAL MATCH (hr:Registration)-[:HAS_CONTACT]->(h)
    RETURN count(DISTINCT hr) AS registrations
  }
  RETURN collect({street: street, zip5: zip5, typesA: typesA, typesB: typesB, registrations: registrations}) AS sharedAddresses
}
CALL (regsA, regsB) {
  UNWIND regsA AS r
  MATCH (r)-[:HAS_CONTACT]->(c:Contact) WHERE c.personName IS NOT NULL
  WITH regsB, toUpper(c.personName) AS person, collect(DISTINCT c.contactType) AS typesA
  CALL (regsB, person) {
    UNWIND regsB AS r2
    MATCH (r2)-[:HAS_CONTACT]->(c2:Contact) WHERE toUpper(c2.personName) = person
    RETURN collect(DISTINCT c2.contactType) AS typesB
  }
  WITH person, typesA, typesB WHERE size(typesB) > 0
  RETURN collect({personName: person, typesA: typesA, typesB: typesB}) AS sharedPeople
}
RETURN size(regsA) AS registrationsA, size(regsB) AS registrationsB, sharedAddresses, sharedPeople;
