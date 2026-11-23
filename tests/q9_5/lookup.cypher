// Q9.5: why is this lot in no Owner Portfolio?
// portfolioAbsence is BOR's top-level reason (no_qualifying_linkage, excluded_by_policy, below_eligibility_rule,
// outside_source_coverage, outside_method_input); portfolioAbsenceDetail is its code. Absence is not a finding that the lot
// has no common owner. A lot with no BOR status row (an HPD lot missing from PLUTO) has neither. A co-op or condo lot left out
// of a portfolio's footprint has coop_condo_excluded. A null groupId with no reason means a lot in no group and no row.
MATCH (l:Lot {bbl: $bbl})
OPTIONAL MATCH (l)-[:IN_PORTFOLIO]->(p:OwnerPortfolio)
RETURN l.bbl AS bbl, p.groupId AS groupId, l.portfolioAbsence AS portfolioAbsence, l.portfolioAbsenceDetail AS portfolioAbsenceDetail;
