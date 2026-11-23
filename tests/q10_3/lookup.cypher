// Q10.3: release-wide disagreement, from the graph. Counting unit: rental lots. Run 2026-05-29-869bd299.
// networksWithManyPortfolios: networks whose rental lots fall in more than one portfolio.
// portfoliosWithManyNetworks: portfolios whose rental lots fall in more than one network. Lots in no portfolio are not counted as a portfolio.
CALL () { MATCH (n:OperationalNetwork)<-[:IN_NETWORK]-(:Lot)-[:IN_PORTFOLIO]->(p:OwnerPortfolio)
          WITH n, count(DISTINCT p) AS c WHERE c > 1 RETURN count(n) AS networksWithManyPortfolios }
CALL () { MATCH (p:OwnerPortfolio)<-[:IN_PORTFOLIO]-(:Lot)-[:IN_NETWORK]->(n:OperationalNetwork)
          WITH p, count(DISTINCT n) AS c WHERE c > 1 RETURN count(p) AS portfoliosWithManyNetworks, collect(p.groupId) AS spanningPortfolios }
RETURN networksWithManyPortfolios, portfoliosWithManyNetworks, spanningPortfolios;
