// Q8.4: if this lot is in no Operational Network, why not?
// networkAbsence is one of five top-level reasons and networkAbsenceDetail is BOR's own code for it.
// Both are absent when the lot is in a network, and also when BOR's lot universe (PLUTO lots) does not
// include the lot (an HPD-registered lot missing from PLUTO): then there is no reason to report.
// An absence is not evidence about ownership; "no qualifying linkage" does not mean different owners.
MATCH (l:Lot {bbl: $bbl})
OPTIONAL MATCH (l)-[:IN_NETWORK]->(n:OperationalNetwork)
RETURN l.bbl AS bbl, n.groupId AS groupId, l.networkAbsence AS networkAbsence, l.networkAbsenceDetail AS networkAbsenceDetail;
