// Q9 rules for the links of Owner Portfolios (CONNECTED_BY_IDENTITY and CONNECTED_BY_DEED): a link joins two different landlords, lower
// nodeId first, and has a portfolioEdgeId string, an evidenceId string and a stage among the codes of its type (identity.splink_base,
// identity.splink_feedback, identity.curated, identity.registered_llc for identity; deed.held_since, deed.linked_successor for deed) with the
// matching evidenceType; a landlord's lots in portfolios are all in one portfolio; when portfolioGroupId is set, each end that covers a
// portfolio lot is in that portfolio. Returns the violation count.
CALL () {
  MATCH (a:Landlord)-[k:CONNECTED_BY_IDENTITY|CONNECTED_BY_DEED]->(b:Landlord)
  WHERE a.nodeId >= b.nodeId
     OR k.portfolioEdgeId IS NULL OR NOT k.portfolioEdgeId IS :: STRING
     OR k.evidenceId IS NULL OR NOT k.evidenceId IS :: STRING
     OR k.stage IS NULL OR NOT k.stage IS :: STRING
     OR (k.portfolioGroupId IS NOT NULL AND NOT k.portfolioGroupId IS :: STRING)
  RETURN count(k) AS badLink
}
CALL () {
  MATCH (:Landlord)-[k:CONNECTED_BY_IDENTITY]->(:Landlord)
  WHERE NOT k.stage IN ['identity.splink_base', 'identity.splink_feedback', 'identity.curated', 'identity.registered_llc']
     OR NOT k.evidenceType IN ['identity_cluster', 'link_set']
  RETURN count(k) AS badIdentityStage
}
CALL () {
  MATCH (:Landlord)-[k:CONNECTED_BY_DEED]->(:Landlord)
  WHERE NOT k.stage IN ['deed.held_since', 'deed.linked_successor'] OR k.evidenceType <> 'evidence_item'
     OR k.networkEdgeId IS NOT NULL OR k.weight IS NOT NULL
  RETURN count(k) AS badDeedStage
}
CALL () {
  MATCH (a:Landlord)-[:COVERS]->(:Lot)-[:IN_PORTFOLIO]->(p:OwnerPortfolio)
  WITH a, count(DISTINCT p) AS portfolios
  WHERE portfolios > 1
  RETURN count(a) AS badLandlord
}
CALL () {
  MATCH (a:Landlord)-[k:CONNECTED_BY_IDENTITY|CONNECTED_BY_DEED]-(:Landlord)
  WHERE k.portfolioGroupId IS NOT NULL
  CALL (a, k) { MATCH (a)-[:COVERS]->(:Lot)-[:IN_PORTFOLIO]->(p:OwnerPortfolio) WHERE p.groupId <> k.portfolioGroupId RETURN count(p) AS elsewhere }
  WITH k, elsewhere
  WHERE elsewhere > 0
  RETURN count(DISTINCT k) AS badEnds
}
RETURN badLink + badIdentityStage + badDeedStage + badLandlord + badEnds AS violationCount
