// Q19.3: were two lots connected before the Operational Network was subdivided, and are they in the same network?
// Louvain splits a connected component of more than 300 lots into communities. A link whose networkGroupId is absent crosses a cut, so a
// path over all network links shows connectivity in the original component. That is not membership: two lots with such a path can be
// in different networks. No row: no path over the links the network used (different components, or one lot has no network link).
MATCH (:Lot {bbl: $a})<-[:COVERS]-(x:Landlord), (:Lot {bbl: $b})<-[:COVERS]-(y:Landlord)
MATCH p = SHORTEST 1 (x)-[k:CONNECTED_BY_NAME|CONNECTED_BY_ADDRESS|CONNECTED_BY_IDENTITY WHERE k.networkEdgeId IS NOT NULL]-+(y)
WITH p ORDER BY length(p) LIMIT 1
RETURN length(p) AS steps,
       [r IN relationships(p) | {type: type(r), networkGroupId: r.networkGroupId, crossesCut: r.networkGroupId IS NULL}] AS links;
