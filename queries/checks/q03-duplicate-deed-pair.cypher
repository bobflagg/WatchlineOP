// Q3 rule: at most one HAS_DEED per lot and deed pair. Returns the violation count.
MATCH (l:Lot)-[h:HAS_DEED]->(d:Deed)
WITH l, d, count(h) AS n WHERE n > 1
RETURN count(*) AS violationCount
