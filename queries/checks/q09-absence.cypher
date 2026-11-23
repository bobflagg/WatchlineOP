// Q9 rules: portfolioAbsence and portfolioAbsenceDetail are both present or both absent; absent on every lot in a portfolio;
// each detail code belongs to its stated top-level reason (BOR DATA.md levels). Returns the violation count.
MATCH (l:Lot)
WITH l, CASE l.portfolioAbsenceDetail
  WHEN 'no_linkage' THEN 'no_qualifying_linkage'
  WHEN 'no_registration' THEN 'outside_source_coverage'
  WHEN 'no_owner_contact' THEN 'outside_method_input'
  WHEN 'unmatched_node' THEN 'outside_method_input'
  WHEN 'address_evidence_masked' THEN 'excluded_by_policy'
  WHEN 'coop_condo_excluded' THEN 'excluded_by_policy'
  WHEN 'coop_condo_dominated' THEN 'excluded_by_policy'
  WHEN 'institutional_screen' THEN 'excluded_by_policy'
  WHEN 'first_name_veto' THEN 'below_eligibility_rule'
  WHEN 'common_name_veto' THEN 'below_eligibility_rule'
  WHEN 'shared_company_degree_unknown' THEN 'below_eligibility_rule'
  WHEN 'shared_company_name_not_rare' THEN 'below_eligibility_rule'
  WHEN 'shared_company_first_name_conflict' THEN 'below_eligibility_rule'
  WHEN 'shared_company_degree_cap' THEN 'below_eligibility_rule'
  WHEN 'deed_not_latest' THEN 'below_eligibility_rule'
  WHEN 'deed_parcels_out_of_range' THEN 'below_eligibility_rule'
  WHEN 'successor_not_shell' THEN 'below_eligibility_rule'
  WHEN 'successor_transfer_not_nominal' THEN 'below_eligibility_rule'
END AS expected
WHERE (l.portfolioAbsence IS NULL) <> (l.portfolioAbsenceDetail IS NULL)
   OR (EXISTS { (l)-[:IN_PORTFOLIO]->() } AND l.portfolioAbsence IS NOT NULL)
   OR (l.portfolioAbsenceDetail IS NOT NULL AND (expected IS NULL OR expected <> l.portfolioAbsence))
RETURN count(l) AS violationCount
