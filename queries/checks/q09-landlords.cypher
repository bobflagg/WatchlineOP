// Q9 rules: a landlord covers a lot or is the end of a link that BOR used in an Owner Portfolio; each lot in a portfolio is covered by at least one landlord;
// in a portfolio with more than one covering landlord, each of them has a link in that portfolio. Returns the violation count.
CALL () {
  MATCH (a:Landlord)
  WHERE NOT EXISTS { (a)-[:COVERS]->(:Lot) } AND NOT EXISTS { (a)-[k:CONNECTED_BY_IDENTITY|CONNECTED_BY_DEED]-(:Landlord) WHERE k.portfolioEdgeId IS NOT NULL }
  RETURN count(a) AS isolated
}
CALL () {
  MATCH (l:Lot)-[:IN_PORTFOLIO]->(:OwnerPortfolio)
  WHERE NOT EXISTS { (:Landlord)-[:COVERS]->(l) }
  RETURN count(l) AS uncovered
}
CALL () {
  MATCH (p:OwnerPortfolio)<-[:IN_PORTFOLIO]-(:Lot)<-[:COVERS]-(a:Landlord)
  WITH p, collect(DISTINCT a) AS members
  WHERE size(members) > 1
  UNWIND members AS a
  WITH DISTINCT a, p
  WHERE NOT EXISTS { (a)-[k:CONNECTED_BY_IDENTITY|CONNECTED_BY_DEED]-(:Landlord) WHERE k.portfolioGroupId = p.groupId }
  RETURN count(a) AS unlinked
}
RETURN isolated + uncovered + unlinked AS violationCount
