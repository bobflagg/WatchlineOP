// Q9.3: through which links were the landlord records of this Owner Portfolio joined?
// Each row is one piece of evidence BOR used, so a pair of records can appear more than once. CONNECTED_BY_IDENTITY joins two records
// judged one party by a resolved identity cluster, a curated owner or a registered-LLC entity; CONNECTED_BY_DEED joins records whose
// buildings were conveyed by one joint deed. stage is BOR's stage code (identity.splink_base, identity.splink_feedback, identity.curated,
// identity.registered_llc, deed.held_since, deed.linked_successor) and evidenceId names the cluster, set or deed evidence item in the
// release (run-local). A landlord record is not a verified person or owner; the direction is only node_a to node_b.
// Landlords are found through the portfolio's rental lots, so a record that covers only co-op or condo lots outside the footprint
// appears only as the end of a link. Only edges in this portfolio are returned (portfolioGroupId equals the portfolio).
MATCH (p:OwnerPortfolio {groupId: $groupId})<-[:IN_PORTFOLIO]-(:Lot)<-[:COVERS]-(a:Landlord)
WITH collect(DISTINCT a) AS members
UNWIND members AS m
MATCH (m)-[k:CONNECTED_BY_IDENTITY|CONNECTED_BY_DEED]-(:Landlord)
WHERE k.portfolioGroupId = $groupId
WITH DISTINCT k
RETURN type(k) AS type, startNode(k).nodeId AS nodeA, endNode(k).nodeId AS nodeB, k.stage AS stage, k.evidenceId AS evidenceId
ORDER BY nodeA, nodeB, stage, evidenceId;
