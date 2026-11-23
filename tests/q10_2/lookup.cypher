// Q10.2: link kinds that explain each lot in one layer and not the other, for this lot's network and portfolio.
// A kind is relationship type:stage. network_only lots: links carrying the network id and no portfolio id, at landlords covering the lot.
// portfolio_only lots: links carrying the portfolio id and no network id. links counts distinct links. Run 2026-05-29-869bd299.
MATCH (l:Lot {bbl: $bbl})
OPTIONAL MATCH (l)-[:IN_PORTFOLIO]->(p:OwnerPortfolio)
OPTIONAL MATCH (l)-[:IN_NETWORK]->(n:OperationalNetwork)
WITH l, p, n
CALL (p, n) {
  OPTIONAL MATCH (x:Lot)-[:IN_NETWORK]->(n) WHERE NOT EXISTS { (x)-[:IN_PORTFOLIO]->(p) }
  OPTIONAL MATCH (x)<-[:COVERS]-(:Landlord)-[k]-(:Landlord)
    WHERE type(k) STARTS WITH 'CONNECTED_BY' AND k.networkGroupId = n.groupId AND k.portfolioGroupId IS NULL
  WITH x, collect(DISTINCT type(k) + ':' + coalesce(k.stage, '')) AS kinds, count(DISTINCT k) AS links
  WHERE x IS NOT NULL
  RETURN collect({bbl: x.bbl, side: 'network_only', kinds: kinds, links: links}) AS netDiffs
}
CALL (p, n) {
  OPTIONAL MATCH (x:Lot)-[:IN_PORTFOLIO]->(p) WHERE NOT EXISTS { (x)-[:IN_NETWORK]->(n) }
  OPTIONAL MATCH (x)<-[:COVERS]-(:Landlord)-[k]-(:Landlord)
    WHERE type(k) STARTS WITH 'CONNECTED_BY' AND k.portfolioGroupId = p.groupId AND k.networkGroupId IS NULL
  WITH x, collect(DISTINCT type(k) + ':' + coalesce(k.stage, '')) AS kinds, count(DISTINCT k) AS links
  WHERE x IS NOT NULL
  RETURN collect({bbl: x.bbl, side: 'portfolio_only', kinds: kinds, links: links}) AS portDiffs
}
RETURN l.bbl AS bbl, n.groupId AS networkId, p.groupId AS portfolioId, netDiffs + portDiffs AS differences;
