// Q19.4: which stages joined these landlord records, so the answer can name each stage's benchmark precision as a method property?
// The graph stores the stage code on the link and nothing about precision: precision belongs to the release's method evidence
// (method_metrics) and is stated per stage, never per link. Where the release says "not evaluated", the answer says so.
MATCH ()-[k:CONNECTED_BY_IDENTITY|CONNECTED_BY_DEED]->()
WHERE k.portfolioGroupId = $groupId
RETURN DISTINCT k.stage AS stage ORDER BY stage;
