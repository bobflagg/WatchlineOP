// Q15.3: which pest violations does this building have, by order code and status? $bin is the building, $codes the pest order codes from
// data/hpd_pest_orders.yaml. The agent maps each code to its kind (mice, roaches, rodents, vermin-unspecified) from that list; the graph stores only
// the code. Counting unit: violations. Open means open at the snapshot (data through 2026-07-02). A violation is what an inspector cited, and no
// species is recorded for the 'vermin-unspecified' codes. An empty result means no pest violation in the snapshot (or the BIN is outside the scope).
MATCH (b:Building {bin: $bin})
OPTIONAL MATCH (b)-[:HAS_VIOLATION]->(v:Violation) WHERE v.orderNumber IN $codes
RETURN v.orderNumber AS orderNumber, v.status AS status, count(v) AS violations, min(v.inspectionDate) AS oldestInspection
ORDER BY orderNumber, status;
