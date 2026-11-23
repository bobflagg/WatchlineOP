// Q8 rules: each COVERS has an integer registrationId; every lot in a network is covered by exactly one landlord;
// a landlord that covers a lot in a network covers lots in one network only (the Owner Portfolio layer adds covers of lots in no
// network, by landlords that are in no network). Returns the violation count.
CALL () {
  MATCH (:Landlord)-[c:COVERS]->(:Lot)
  WHERE c.registrationId IS NULL OR NOT c.registrationId IS :: INTEGER
  RETURN count(c) AS badRegistration
}
CALL () {
  MATCH (l:Lot)-[:IN_NETWORK]->(:OperationalNetwork)
  OPTIONAL MATCH (a:Landlord)-[:COVERS]->(l)
  WITH l, count(a) AS n
  WHERE n <> 1
  RETURN count(l) AS badCoverage
}
CALL () {
  MATCH (a:Landlord)-[:COVERS]->(l:Lot)
  OPTIONAL MATCH (l)-[:IN_NETWORK]->(n:OperationalNetwork)
  WITH a, count(l) AS lots, count(n) AS inNetwork, count(DISTINCT n) AS networks
  WHERE networks > 1 OR (networks = 1 AND inNetwork <> lots)
  RETURN count(a) AS badLandlord
}
RETURN badRegistration + badCoverage + badLandlord AS violationCount
