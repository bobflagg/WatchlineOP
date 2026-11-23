// Q19.2: through which landlord records and links are two lots of one Owner Portfolio joined? (representative path, fewest links)
// Each link is one piece of BOR evidence: CONNECTED_BY_IDENTITY (a resolved identity cluster, curated owner or registered-LLC entity) or
// CONNECTED_BY_DEED (one joint deed), with BOR's stage code and the run-local evidence id. A path is not a direct record between the
// two lots, and a stage's benchmark precision is not the probability that this link is right. Other equally short paths may exist.
// A landlord record is not a verified person or owner. No row: no path inside this portfolio.
MATCH (:Lot {bbl: $a})<-[:COVERS]-(x:Landlord), (:Lot {bbl: $b})<-[:COVERS]-(y:Landlord)
MATCH p = SHORTEST 1 (x)-[k:CONNECTED_BY_IDENTITY|CONNECTED_BY_DEED WHERE k.portfolioGroupId = $groupId]-+(y)
WITH p ORDER BY length(p) LIMIT 1
RETURN length(p) AS steps,
       [n IN nodes(p) | n.nodeId] AS nodeIds,
       [n IN nodes(p) | [(n)-[:COVERS]->(l:Lot) | l.bbl]] AS lotsOfEachRecord,
       [r IN relationships(p) | {type: type(r), stage: r.stage, evidenceType: r.evidenceType, evidenceId: r.evidenceId,
                                 nodeA: startNode(r).nodeId, nodeB: endNode(r).nodeId}] AS links;
