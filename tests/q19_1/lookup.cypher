// Q19.1: for each of two lots, which Operational Network and Owner Portfolio is it in, or why is it in none?
// The answer compares the two rows per layer: same group, different groups, or one or both ungrouped (with BOR's reason code).
// groupId is run-local (BOR run 2026-05-29-869bd299). networkSplit is wcc (a whole connected component) or louvain (a community cut
// from a larger component). A lot in no group has a reason: absence is not evidence of different owners. A lot with no Lot node is
// outside the rental graph and has no row.
UNWIND [$a, $b] AS bbl
MATCH (l:Lot {bbl: bbl})
OPTIONAL MATCH (l)-[:IN_NETWORK]->(n:OperationalNetwork)
OPTIONAL MATCH (l)-[:IN_PORTFOLIO]->(p:OwnerPortfolio)
RETURN l.bbl AS bbl, n.groupId AS networkGroupId, n.split AS networkSplit, l.networkAbsence AS networkAbsence, l.networkAbsenceDetail AS networkAbsenceDetail,
       p.groupId AS portfolioGroupId, p.composition AS portfolioComposition, l.portfolioAbsence AS portfolioAbsence, l.portfolioAbsenceDetail AS portfolioAbsenceDetail;
