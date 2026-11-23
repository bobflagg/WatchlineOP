// Q8.1: who anchors this Operational Network, the landlord record the network is shown under? A display rule: the member with the most lots, ties to the smallest
// node id; not the owner. groupId is run-local.
MATCH (:OperationalNetwork {groupId: $groupId})-[:ANCHORED_BY]->(a:Landlord)
RETURN a.nodeId AS nodeId, a.name AS name;
