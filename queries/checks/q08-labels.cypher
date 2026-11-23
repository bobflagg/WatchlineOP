// Q8 and Q9 rules for what a landlord record is called and which record anchors a group: businessAddresses, when present, is a non-empty
// list of non-blank strings, strictly increasing (so sorted and distinct); every OperationalNetwork and every OwnerPortfolio has exactly one ANCHORED_BY
// relationship, and it ends at a Landlord. Returns the violation count.
CALL () {
  MATCH (a:Landlord)
  WHERE a.businessAddresses IS NOT NULL
    AND (NOT a.businessAddresses IS :: LIST<STRING NOT NULL>
         OR size(a.businessAddresses) = 0
         OR any(x IN a.businessAddresses WHERE trim(x) = '')
         OR NOT all(i IN range(0, size(a.businessAddresses) - 2) WHERE a.businessAddresses[i] < a.businessAddresses[i + 1]))
  RETURN count(a) AS badAddresses
}
CALL () {
  MATCH (g)
  WHERE g:OperationalNetwork OR g:OwnerPortfolio
  WITH g, COUNT { (g)-[:ANCHORED_BY]->(:Landlord) } AS anchors, COUNT { (g)-[:ANCHORED_BY]->() } AS any
  WHERE anchors <> 1 OR any <> 1
  RETURN count(g) AS badAnchor
}
RETURN badAddresses + badAnchor AS violationCount
