// Q9.4: how does this lot's Owner Portfolio footprint differ from its Operational Network?
// Counting unit: rental lots in the graph. The layers are never mixed: portfolioLots and networkLots are separate counts.
// portfolioOnlyLots and networkOnlyLots list the lots one layer has and the other lacks. A null id means the lot is in
// no group of that layer (Q8.4 and Q9.5 give the reasons). Both groupings are leads, not legal ownership, and their ids
// are run-local (BOR run 2026-05-29-869bd299).
MATCH (l:Lot {bbl: $bbl})
OPTIONAL MATCH (l)-[:IN_PORTFOLIO]->(p:OwnerPortfolio)
OPTIONAL MATCH (l)-[:IN_NETWORK]->(n:OperationalNetwork)
WITH l, p, n
CALL (p) { OPTIONAL MATCH (x:Lot)-[:IN_PORTFOLIO]->(p) RETURN collect(x.bbl) AS pLots }
CALL (n) { OPTIONAL MATCH (y:Lot)-[:IN_NETWORK]->(n) RETURN collect(y.bbl) AS nLots }
RETURN l.bbl AS bbl, p.groupId AS portfolioId, n.groupId AS networkId,
       size(pLots) AS portfolioLots, size(nLots) AS networkLots,
       size([b IN pLots WHERE b IN nLots]) AS inBoth,
       [b IN pLots WHERE NOT b IN nLots] AS portfolioOnlyLots,
       [b IN nLots WHERE NOT b IN pLots] AS networkOnlyLots;
