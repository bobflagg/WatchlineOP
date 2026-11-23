// Q8.1: which Operational Network does this lot belong to, and is it a whole component or a Louvain community?
// groupId is run-local (BOR run 2026-05-29-869bd299): it means something only inside that run.
// split: wcc is the whole connected component; louvain is a community cut from a component of more than 300 lots.
// No row for the network (null groupId) means the lot is in no network; Q8.4 gives the reason.
MATCH (l:Lot {bbl: $bbl})
OPTIONAL MATCH (l)-[:IN_NETWORK]->(n:OperationalNetwork)
RETURN l.bbl AS bbl, n.groupId AS groupId, n.split AS split;
