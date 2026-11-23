// Q10.1: the lot's Operational Network and Owner Portfolio, and the lots in one layer and not the other.
// Counting unit: rental lots in the graph. Layers are never mixed. Ids are run-local (BOR run 2026-05-29-869bd299).
// A null id means the lot is in no group of that layer (Q8.4 and Q9.5 give the reasons). Both groupings are derived, not legal ownership.
MATCH (l:Lot {bbl: $bbl})
OPTIONAL MATCH (l)-[:IN_PORTFOLIO]->(p:OwnerPortfolio)
OPTIONAL MATCH (l)-[:IN_NETWORK]->(n:OperationalNetwork)
WITH l, p, n
CALL (p) { OPTIONAL MATCH (x:Lot)-[:IN_PORTFOLIO]->(p) RETURN collect(x.bbl) AS pLots }
CALL (n) { OPTIONAL MATCH (y:Lot)-[:IN_NETWORK]->(n) RETURN collect(y.bbl) AS nLots }
RETURN l.bbl AS bbl, n.groupId AS networkId, n.split AS networkSplit, p.groupId AS portfolioId, p.composition AS composition,
       size(nLots) AS networkLots, size(pLots) AS portfolioLots,
       [b IN nLots WHERE NOT b IN pLots] AS networkOnlyLots,
       [b IN pLots WHERE NOT b IN nLots] AS portfolioOnlyLots;
