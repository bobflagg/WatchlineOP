// Q21.3: for one lot, which Operational Network and Owner Portfolio is it in, and how do the two lists differ? $bbl is the lot.
// Returns the lot's two group ids, then (by group) member lots with their open counts, so the agent can show lots only in the network, only in the portfolio
// and in both, and the open-violation totals of each side. A lot in no group in a layer has a null group and its absence reason (Q19.1), not an empty list.
// Both layers are derived leads, not findings of common ownership. Group ids are run-local.
MATCH (x:Lot {bbl: $bbl})
OPTIONAL MATCH (x)-[:IN_NETWORK]->(n:OperationalNetwork)
OPTIONAL MATCH (x)-[:IN_PORTFOLIO]->(p:OwnerPortfolio)
CALL (n, p) {
  OPTIONAL MATCH (n)<-[:IN_NETWORK]-(a:Lot)
  WITH p, collect(DISTINCT a.bbl) AS netLots
  OPTIONAL MATCH (p)<-[:IN_PORTFOLIO]-(b:Lot)
  RETURN netLots, collect(DISTINCT b.bbl) AS portLots
}
RETURN x.bbl AS bbl, n.groupId AS networkGroupId, p.groupId AS portfolioGroupId, x.networkAbsenceDetail AS networkAbsenceDetail, x.portfolioAbsenceDetail AS portfolioAbsenceDetail,
       netLots, portLots,
       [b IN netLots WHERE NOT b IN portLots] AS onlyNetwork, [b IN portLots WHERE NOT b IN netLots] AS onlyPortfolio, [b IN netLots WHERE b IN portLots] AS both;
