// Q27.3: which pest complaint problems are recorded against this building in a period, by pest and status?
// $bin is the building; $start and $end are dates (inclusive). Loaded problems start 2021-01-01: a period starting earlier is partly "not loaded".
// A pest complaint is a Problem whose minorCategory is 'PESTS'; the pest is its problemCode (MICE, ROACHES, OTHER, BED BUGS, FLIES, TERMITES, FLEAS).
// OTHER is not a pest name and never means mice. Counting unit: problem records (flagged duplicates included and counted apart); complaints are distinct
// complaint ids. Open means open at the snapshot (data through 2026-07-07). A complaint is what a tenant reported, not what was found; the count is per
// building, never per unit. An empty result means no pest complaint in the period (or the BIN is outside the registered scope).
MATCH (b:Building {bin: $bin})
OPTIONAL MATCH (b)-[:HAS_PROBLEM]->(p:Problem) WHERE p.minorCategory = 'PESTS' AND p.receivedDate >= date($start) AND p.receivedDate <= date($end)
RETURN p.problemCode AS problemCode, p.status AS status, count(p) AS problems,
       count(CASE WHEN p.duplicate THEN 1 END) AS duplicates, count(DISTINCT p.complaintId) AS complaints,
       min(p.receivedDate) AS firstReceived, max(p.receivedDate) AS lastReceived
ORDER BY problemCode, status;
