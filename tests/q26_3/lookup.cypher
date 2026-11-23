// Q26.3: for each layer, is this lot in a group, and if not, why? $bbl is the lot. Group ids are valid only within run 2026-05-29-869bd299
// (release v0.3.0). absence is BOR's top-level reason (the five), detail its code. A lot in no group is not a finding of different owners:
// recall is unmeasured. No row means the lot is outside the rental graph.
MATCH (l:Lot {bbl: $bbl})
OPTIONAL MATCH (l)-[:IN_NETWORK]->(n:OperationalNetwork)
OPTIONAL MATCH (l)-[:IN_PORTFOLIO]->(p:OwnerPortfolio)
RETURN l.bbl AS bbl, n.groupId AS networkGroupId, l.networkAbsence AS networkAbsence, l.networkAbsenceDetail AS networkAbsenceDetail,
       p.groupId AS portfolioGroupId, l.portfolioAbsence AS portfolioAbsence, l.portfolioAbsenceDetail AS portfolioAbsenceDetail;
