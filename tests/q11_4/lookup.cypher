// Q11.4: which derived group leads involve this entity's lots? $nameKey is the given name after rule N3. An entity's lots are those of the
// buildings whose HPD registrations carry a Contact with that name key (a lead found by name, never a stored link). For each lot the answer
// gives its Operational Network and Owner Portfolio (ids are run-local, BOR run 2026-05-29-869bd299) with member lot counts, or the BOR absence
// reason. Both are derived (Type II) and hypothesized: a lead to verify, never a finding of common ownership or control. An Owner Portfolio is an
// apparent-owner attribution; an Operational Network is infrastructure connection, "other" and not ownership. Evidence per link: Q7.5 and Q8.3.
OPTIONAL MATCH (:Contact {nameKey: $nameKey})<-[:HAS_CONTACT]-(:Registration)<-[:HAS_REGISTRATION]-(:Building)<-[:HAS_BUILDING]-(l:Lot)
WITH collect(DISTINCT l) AS lots
UNWIND CASE WHEN size(lots) = 0 THEN [null] ELSE lots END AS l
OPTIONAL MATCH (l)-[:IN_NETWORK]->(n:OperationalNetwork)
OPTIONAL MATCH (l)-[:IN_PORTFOLIO]->(p:OwnerPortfolio)
CALL (n) { OPTIONAL MATCH (n)<-[:IN_NETWORK]-(m:Lot) RETURN count(m) AS networkLots }
CALL (p) { OPTIONAL MATCH (p)<-[:IN_PORTFOLIO]-(m:Lot) RETURN count(m) AS portfolioLots }
RETURN l.bbl AS bbl, n.groupId AS networkGroupId, n.split AS networkSplit, networkLots, l.networkAbsence AS networkAbsence,
       p.groupId AS portfolioGroupId, p.composition AS portfolioComposition, portfolioLots, l.portfolioAbsence AS portfolioAbsence
ORDER BY bbl;
