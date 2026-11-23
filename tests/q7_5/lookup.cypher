// Q7.5: did the Operational Network or Owner Portfolio layer group the two, in which group in the pinned run, and which links connect their
// landlord records? $bblsA and $bblsB are the lots of each side (a building's lot, or lookup_lots.cypher for an entity). Group ids are run-local
// (BOR run 2026-05-29-869bd299). Each link is one piece of evidence BOR used: identity (stage, cluster or set id), deed (stage, evidence item),
// name or address (weight only). A link at an address masked as an aggregator is not loaded and is only counted by Q6.2. A landlord record
// is a name on a filing, not a verified owner; no group and no link do not show the two are unrelated.
CALL () {
  UNWIND $bblsA AS b MATCH (l:Lot {bbl: b})
  OPTIONAL MATCH (l)-[:IN_NETWORK]->(n:OperationalNetwork)
  OPTIONAL MATCH (l)-[:IN_PORTFOLIO]->(p:OwnerPortfolio)
  RETURN collect({bbl: l.bbl, networkGroupId: n.groupId, networkSplit: n.split, networkAbsence: l.networkAbsence, networkAbsenceDetail: l.networkAbsenceDetail,
                  portfolioGroupId: p.groupId, portfolioComposition: p.composition, portfolioAbsence: l.portfolioAbsence,
                  portfolioAbsenceDetail: l.portfolioAbsenceDetail}) AS lotsA
}
CALL () {
  UNWIND $bblsB AS b MATCH (l:Lot {bbl: b})
  OPTIONAL MATCH (l)-[:IN_NETWORK]->(n:OperationalNetwork)
  OPTIONAL MATCH (l)-[:IN_PORTFOLIO]->(p:OwnerPortfolio)
  RETURN collect({bbl: l.bbl, networkGroupId: n.groupId, networkSplit: n.split, networkAbsence: l.networkAbsence, networkAbsenceDetail: l.networkAbsenceDetail,
                  portfolioGroupId: p.groupId, portfolioComposition: p.composition, portfolioAbsence: l.portfolioAbsence,
                  portfolioAbsenceDetail: l.portfolioAbsenceDetail}) AS lotsB
}
CALL () {
  UNWIND $bblsA AS b OPTIONAL MATCH (:Lot {bbl: b})<-[:COVERS]-(a:Landlord) RETURN collect(DISTINCT a.nodeId) AS landlordsA
}
CALL () {
  UNWIND $bblsB AS b OPTIONAL MATCH (:Lot {bbl: b})<-[:COVERS]-(a:Landlord) RETURN collect(DISTINCT a.nodeId) AS landlordsB
}
CALL (landlordsA, landlordsB) {
  MATCH (x:Landlord)-[k:CONNECTED_BY_IDENTITY|CONNECTED_BY_DEED|CONNECTED_BY_NAME|CONNECTED_BY_ADDRESS]-(y:Landlord)
  WHERE x.nodeId IN landlordsA AND y.nodeId IN landlordsB
  WITH DISTINCT k
  RETURN collect({type: type(k), nodeA: startNode(k).nodeId, nodeB: endNode(k).nodeId, weight: k.weight, stage: k.stage,
                  evidenceType: k.evidenceType, evidenceId: k.evidenceId, networkGroupId: k.networkGroupId,
                  portfolioGroupId: k.portfolioGroupId}) AS links
}
RETURN lotsA, lotsB, landlordsA, landlordsB, links;
