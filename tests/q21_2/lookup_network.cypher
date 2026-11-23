// Q21.2: how concentrated are the open violations of an Operational Network? $groupId is the network (run-local); $top is how many top lots to sum (3).
// Counting unit: distinct open violations of each lot's buildings (as Q21.1). Share = top lots' open count / sum of lot open counts. A BIN on several lots counts
// toward each, so distinctOpen (distinct violations over the whole group) is returned to show any overlap. null share when the group has no open violation.
MATCH (n:OperationalNetwork {groupId: $groupId})<-[:IN_NETWORK]-(l:Lot)
CALL (l) {
  OPTIONAL MATCH (l)-[:HAS_BUILDING]->(:Building)-[:HAS_VIOLATION]->(v:Violation {status: 'Open'})
  RETURN count(DISTINCT v) AS open
}
WITH l, open ORDER BY open DESC, l.bbl
WITH collect({bbl: l.bbl, open: open}) AS lots
CALL (lots) {
  MATCH (n:OperationalNetwork {groupId: $groupId})<-[:IN_NETWORK]-(:Lot)-[:HAS_BUILDING]->(:Building)-[:HAS_VIOLATION]->(v:Violation {status: 'Open'})
  RETURN count(DISTINCT v) AS distinctOpen
}
WITH lots, distinctOpen, reduce(t = 0, x IN lots | t + x.open) AS sumOpen, reduce(t = 0, x IN lots[0..$top] | t + x.open) AS topOpen
RETURN size(lots) AS memberLots, size([x IN lots WHERE x.open > 0]) AS lotsWithOpen, sumOpen, topOpen, distinctOpen,
       CASE WHEN sumOpen = 0 THEN null ELSE toFloat(topOpen) / sumOpen END AS topShare;
