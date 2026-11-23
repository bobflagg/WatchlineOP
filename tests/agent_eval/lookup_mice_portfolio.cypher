// Mice complaints and mice violations of each building of an Owner Portfolio. $groupId is the portfolio (run-local to the pinned BOR release).
// Mice complaint: Problem with minorCategory PESTS and problemCode MICE (OTHER is never mice). Mice violation: Violation with orderNumber 569 or 869
// (566 and 866 are unspecified vermin, never mice). Counts are per building, never per unit; complaints are what tenants reported, violations what an
// inspector cited. A portfolio is a derived lead, not a finding of common ownership.
MATCH (op:OwnerPortfolio {groupId: $groupId})<-[:IN_PORTFOLIO]-(l:Lot)-[:HAS_BUILDING]->(b:Building)
CALL (b) {
  OPTIONAL MATCH (b)-[:HAS_PROBLEM]->(p:Problem {minorCategory: 'PESTS', problemCode: 'MICE'})
  RETURN count(p) AS miceComplaints, count(CASE WHEN p.status = 'OPEN' THEN 1 END) AS miceOpen, min(p.receivedDate) AS first, max(p.receivedDate) AS last
}
CALL (b) {
  OPTIONAL MATCH (b)-[:HAS_VIOLATION]->(v:Violation) WHERE v.orderNumber IN ['569', '869']
  RETURN count(v) AS miceViolations, count(CASE WHEN v.status = 'Open' THEN 1 END) AS miceViolationsOpen
}
RETURN l.bbl AS bbl, b.bin AS bin, l.unitsRes AS unitsRes, miceComplaints, miceOpen, toString(first) AS first, toString(last) AS last, miceViolations, miceViolationsOpen
ORDER BY miceComplaints DESC, bin;
