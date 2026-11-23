// Q26.4: does the graph hold any HPD violation for this lot? $bbl is the lot. Violations are loaded only for HPD-registered lots (Q15), so
// loadedScope false means "not loaded", never "none": the source may hold violations for an unregistered lot. For a registered lot, violations 0
// means none in the snapshot (data through 2026-07-02), not that conditions are good. Counting unit: distinct violations of the lot's buildings.
MATCH (l:Lot {bbl: $bbl})
CALL (l) {
  OPTIONAL MATCH (l)-[:HAS_BUILDING]->(:Building)-[:HAS_VIOLATION]->(v:Violation)
  RETURN count(DISTINCT v) AS violations
}
RETURN l.bbl AS bbl, l.hpdRegistered AS loadedScope, violations;
