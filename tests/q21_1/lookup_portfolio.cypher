// Q21.1: open violations by class and rate per residential unit for each member lot of an Owner Portfolio (rental member lots). $groupId is the portfolio (run-local).
// Counting unit: distinct violations of the lot's buildings, open at the snapshot (data through 2026-07-02). Classes are reported apart, never summed into severity.
// Rate = open / lot PLUTO units (lot-wide); null means "rate unavailable" (units 0 or absent), ranked last. A violation is what an inspector cited.
MATCH (n:OwnerPortfolio {groupId: $groupId})<-[:IN_PORTFOLIO]-(l:Lot)
CALL (l) {
  OPTIONAL MATCH (l)-[:HAS_BUILDING]->(:Building)-[:HAS_VIOLATION]->(v:Violation {status: 'Open'})
  WITH DISTINCT v
  RETURN count(v) AS open, count(CASE WHEN v.violationClass = 'A' THEN v END) AS classA, count(CASE WHEN v.violationClass = 'B' THEN v END) AS classB,
         count(CASE WHEN v.violationClass = 'C' THEN v END) AS classC, count(CASE WHEN v.violationClass = 'I' THEN v END) AS classI
}
WITH l, open, classA, classB, classC, classI,
     CASE WHEN l.unitsRes IS NULL OR l.unitsRes = 0 THEN null ELSE toFloat(open) / l.unitsRes END AS rate
RETURN l.bbl AS bbl, l.unitsRes AS unitsRes, open, classA, classB, classC, classI, rate
ORDER BY coalesce(rate, -1.0) DESC, open DESC, bbl;
