// Q9.1: who anchors this Owner Portfolio, the landlord record the portfolio is shown under? A display rule: the member with the most lots, ties to the smallest
// node id; not the owner. groupId is run-local.
MATCH (:OwnerPortfolio {groupId: $groupId})-[:ANCHORED_BY]->(a:Landlord)
RETURN a.nodeId AS nodeId, a.name AS name;
