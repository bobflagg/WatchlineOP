// Q9.1: which Owner Portfolio does this lot belong to, and what is its composition?
// groupId is run-local (BOR run 2026-05-29-869bd299). composition: identity (a resolved shared identity), deed_only
// (a qualifying shared deed) or deed_bridged (identity groups joined by a deed). A portfolio is an apparent-owner
// attribution from ownership signals, not a legal finding of ownership.
// No portfolio (null groupId) means the lot is in none; Q9.5 gives the reason. A co-op or condo lot left out of a
// portfolio's rental footprint has no portfolio here either.
MATCH (l:Lot {bbl: $bbl})
OPTIONAL MATCH (l)-[:IN_PORTFOLIO]->(p:OwnerPortfolio)
RETURN l.bbl AS bbl, p.groupId AS groupId, p.composition AS composition;
