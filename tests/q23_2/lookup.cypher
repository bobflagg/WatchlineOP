// Q23.2: of the lots whose buildings disclose this managing agent, how many are in the reference building's Operational Network and Owner Portfolio, and how many are not?
// $bin is the reference building (resolved as in Q1); $nameKey is the agent's corporation name under rule N3 (Q23.1). Counting unit: distinct lots (BBL);
// a building count is Q23.1. A lot not in any network or portfolio is reported as "none", not as "other": the release may not group it (Owner Portfolio: rental lots only).
// Both groupings are leads to verify, valid only within release v0.3.0. A shared agent shows a management relationship, not common ownership.
MATCH (:Building {bin: $bin})<-[:HAS_BUILDING]-(rl:Lot)
OPTIONAL MATCH (rl)-[:IN_NETWORK]->(rn:OperationalNetwork)
OPTIONAL MATCH (rl)-[:IN_PORTFOLIO]->(rp:OwnerPortfolio)
WITH rl, rn.groupId AS network, rp.groupId AS portfolio
CALL (network, portfolio) {
  MATCH (:Contact {nameKey: $nameKey, contactType: 'Agent'})<-[:HAS_CONTACT]-(:Registration)<-[:HAS_REGISTRATION]-(:Building)<-[:HAS_BUILDING]-(fl:Lot)
  WITH DISTINCT fl
  OPTIONAL MATCH (fl)-[:IN_NETWORK]->(fn:OperationalNetwork)
  OPTIONAL MATCH (fl)-[:IN_PORTFOLIO]->(fp:OwnerPortfolio)
  RETURN count(fl) AS lots,
         count(CASE WHEN fn.groupId = network THEN 1 END) AS networkSame,
         count(CASE WHEN fn IS NOT NULL AND (network IS NULL OR fn.groupId <> network) THEN 1 END) AS networkOther,
         count(CASE WHEN fn IS NULL THEN 1 END) AS networkNone,
         count(CASE WHEN fp.groupId = portfolio THEN 1 END) AS portfolioSame,
         count(CASE WHEN fp IS NOT NULL AND (portfolio IS NULL OR fp.groupId <> portfolio) THEN 1 END) AS portfolioOther,
         count(CASE WHEN fp IS NULL THEN 1 END) AS portfolioNone
}
RETURN rl.bbl AS referenceLot, network, portfolio, lots, networkSame, networkOther, networkNone, portfolioSame, portfolioOther, portfolioNone
ORDER BY referenceLot;
