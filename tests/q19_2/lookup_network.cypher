// Q19.2: through which landlord records and links are two lots of one Operational Network joined? (representative path, fewest links)
// Only links the network used inside this network (networkGroupId equals the network). CONNECTED_BY_NAME and CONNECTED_BY_ADDRESS carry
// the network weight; CONNECTED_BY_IDENTITY (weight 100) carries the identity stage and evidence. Address links BOR masked at a hub
// address are not relationships (see NetworkMaskedAddress). A path is not a finding of common ownership. No row: no path in this network.
MATCH (:Lot {bbl: $a})<-[:COVERS]-(x:Landlord), (:Lot {bbl: $b})<-[:COVERS]-(y:Landlord)
MATCH p = SHORTEST 1 (x)-[k:CONNECTED_BY_NAME|CONNECTED_BY_ADDRESS|CONNECTED_BY_IDENTITY WHERE k.networkGroupId = $groupId]-+(y)
WITH p ORDER BY length(p) LIMIT 1
RETURN length(p) AS steps,
       [n IN nodes(p) | n.nodeId] AS nodeIds,
       [r IN relationships(p) | {type: type(r), stage: r.stage, evidenceType: r.evidenceType, evidenceId: r.evidenceId, weight: r.weight,
                                 nodeA: startNode(r).nodeId, nodeB: endNode(r).nodeId}] AS links;
