// Q8 rules: networkAbsence and networkAbsenceDetail are both present or both absent; absent on every lot in a network;
// each detail code belongs to its stated top-level reason (BOR DATA.md levels). Returns the violation count.
MATCH (l:Lot)
WITH l, CASE l.networkAbsenceDetail
  WHEN 'no_linkage' THEN 'no_qualifying_linkage'
  WHEN 'no_registration' THEN 'outside_source_coverage'
  WHEN 'no_owner_contact' THEN 'outside_method_input'
  WHEN 'aggregator_address_masked' THEN 'excluded_by_policy'
  WHEN 'address_evidence_masked' THEN 'excluded_by_policy'
  WHEN 'first_name_veto' THEN 'below_eligibility_rule'
  WHEN 'common_name_veto' THEN 'below_eligibility_rule'
  WHEN 'shared_company_degree_unknown' THEN 'below_eligibility_rule'
  WHEN 'shared_company_name_not_rare' THEN 'below_eligibility_rule'
  WHEN 'shared_company_first_name_conflict' THEN 'below_eligibility_rule'
  WHEN 'shared_company_degree_cap' THEN 'below_eligibility_rule'
END AS expected
WHERE (l.networkAbsence IS NULL) <> (l.networkAbsenceDetail IS NULL)
   OR (EXISTS { (l)-[:IN_NETWORK]->() } AND l.networkAbsence IS NOT NULL)
   OR (l.networkAbsenceDetail IS NOT NULL AND (expected IS NULL OR expected <> l.networkAbsence))
RETURN count(l) AS violationCount
