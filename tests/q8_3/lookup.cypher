// Q8.3: which links connect the members of this Operational Network, and how strong are they?
// A Landlord is a Who Owns What landlord record: a distinct contact kind, name and business address as filed with HPD, covering
// one or more lots through the HPD registration BOR used. It is not a verified person or owner.
// Links join landlords. CONNECTED_BY_NAME and CONNECTED_BY_ADDRESS carry the network's weight (1.5 times the name match, 1.0 times
// the address match); CONNECTED_BY_IDENTITY (a resolved identity, a curated owner or a registered-LLC entity) carries 100 and the
// stage and evidence that produced it. Only relationships the Operational Network used are returned (networkEdgeId is set).
// A link whose networkGroupId is absent joins a landlord of this network to one of another network: it shows where a connected
// component was cut, not membership. Address links BOR masked at a hub address are not relationships; see NetworkMaskedAddress.maskedEdges.
MATCH (n:OperationalNetwork {groupId: $groupId})<-[:IN_NETWORK]-(:Lot)<-[:COVERS]-(a:Landlord)
WITH collect(DISTINCT a) AS members
UNWIND members AS m
MATCH (m)-[k:CONNECTED_BY_NAME|CONNECTED_BY_ADDRESS|CONNECTED_BY_IDENTITY]-(:Landlord)
WHERE k.networkEdgeId IS NOT NULL
WITH DISTINCT k
RETURN type(k) AS type, startNode(k).nodeId AS nodeA, endNode(k).nodeId AS nodeB, k.weight AS weight, k.stage AS stage,
       k.evidenceId AS evidenceId, k.networkGroupId AS networkGroupId
ORDER BY nodeA, nodeB, type, evidenceId;
