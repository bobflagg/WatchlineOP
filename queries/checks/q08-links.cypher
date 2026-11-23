// Q8 rules for the links of Operational Networks (CONNECTED_BY_NAME, CONNECTED_BY_ADDRESS, and the network side of CONNECTED_BY_IDENTITY):
// a link joins two different landlords, lower nodeId first; a name or address link has a networkEdgeId string and a weight above 0;
// an identity link that the network used (networkEdgeId set) has weight 100, and weight and networkEdgeId go together; networkGroupId is
// a string and is absent exactly when the two landlords are in different networks; every network has at least one link inside it.
// Returns the violation count.
CALL () {
  MATCH (a:Landlord)-[k:CONNECTED_BY_NAME|CONNECTED_BY_ADDRESS|CONNECTED_BY_IDENTITY]->(b:Landlord)
  WHERE a.nodeId >= b.nodeId
  RETURN count(k) AS badOrder
}
CALL () {
  MATCH (:Landlord)-[k:CONNECTED_BY_NAME|CONNECTED_BY_ADDRESS]->(:Landlord)
  WHERE k.networkEdgeId IS NULL OR NOT k.networkEdgeId IS :: STRING
     OR k.weight IS NULL OR NOT k.weight IS :: FLOAT OR k.weight <= 0
     OR (k.networkGroupId IS NOT NULL AND NOT k.networkGroupId IS :: STRING)
  RETURN count(k) AS badValue
}
CALL () {
  MATCH (:Landlord)-[k:CONNECTED_BY_IDENTITY]->(:Landlord)
  WHERE (k.networkEdgeId IS NULL) <> (k.weight IS NULL)
     OR (k.networkEdgeId IS NOT NULL AND (NOT k.networkEdgeId IS :: STRING OR NOT k.weight IS :: FLOAT OR k.weight <> 100.0))
     OR (k.networkGroupId IS NOT NULL AND (k.networkEdgeId IS NULL OR NOT k.networkGroupId IS :: STRING))
  RETURN count(k) AS badIdentity
}
CALL () {
  MATCH (a:Landlord)-[k:CONNECTED_BY_NAME|CONNECTED_BY_ADDRESS|CONNECTED_BY_IDENTITY]->(b:Landlord)
  WHERE k.networkEdgeId IS NOT NULL
  CALL (a) { MATCH (a)-[:COVERS]->(:Lot)-[:IN_NETWORK]->(n:OperationalNetwork) RETURN n AS na LIMIT 1 }
  CALL (b) { MATCH (b)-[:COVERS]->(:Lot)-[:IN_NETWORK]->(n:OperationalNetwork) RETURN n AS nb LIMIT 1 }
  WITH k, na, nb
  WHERE (k.networkGroupId IS NULL) <> (na <> nb) OR (k.networkGroupId IS NOT NULL AND k.networkGroupId <> na.groupId)
  RETURN count(k) AS badBoundary
}
CALL () {
  MATCH (n:OperationalNetwork)
  WHERE NOT EXISTS {
    MATCH (n)<-[:IN_NETWORK]-(:Lot)<-[:COVERS]-(a:Landlord)-[k:CONNECTED_BY_NAME|CONNECTED_BY_ADDRESS|CONNECTED_BY_IDENTITY]-(b:Landlord)-[:COVERS]->(:Lot)-[:IN_NETWORK]->(n)
    WHERE k.networkEdgeId IS NOT NULL
  }
  RETURN count(n) AS noInsideLink
}
RETURN badOrder + badValue + badIdentity + badBoundary + noInsideLink AS violationCount
