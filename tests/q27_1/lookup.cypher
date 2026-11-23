// Q27.1: which complaint problems are recorded against this building in a period, by type, major category and status?
// $bin is the building; $start and $end are dates (inclusive). Loaded problems start 2021-01-01: a period starting earlier is partly "not loaded".
// Counting unit: problem records (flagged duplicates included and counted apart); complaints are distinct complaint ids. Open means open at the
// snapshot (data through 2026-07-07). A problem is what was reported, not what was found. An empty result means no problem in the period (or the BIN is outside the registered scope).
MATCH (b:Building {bin: $bin})
OPTIONAL MATCH (b)-[:HAS_PROBLEM]->(p:Problem) WHERE p.receivedDate >= date($start) AND p.receivedDate <= date($end)
RETURN p.problemType AS problemType, p.majorCategory AS majorCategory, p.status AS status, count(p) AS problems,
       count(CASE WHEN p.duplicate THEN 1 END) AS duplicates, count(DISTINCT p.complaintId) AS complaints,
       min(p.receivedDate) AS firstReceived, max(p.receivedDate) AS lastReceived
ORDER BY problemType, majorCategory, status;
