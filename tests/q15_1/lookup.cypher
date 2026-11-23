// Q15.1: which violations are recorded against this building, by class and status? $bin is the building.
// Counting unit: violations. Open means open at the snapshot (data through 2026-07-02). A violation is what an inspector cited, not a measure of
// conditions. An empty result means no violation in the snapshot for this building (or the BIN is outside the registered scope).
MATCH (b:Building {bin: $bin})
OPTIONAL MATCH (b)-[:HAS_VIOLATION]->(v:Violation)
RETURN v.violationClass AS violationClass, v.status AS status, count(v) AS violations, min(v.inspectionDate) AS oldestInspection
ORDER BY violationClass, status;
