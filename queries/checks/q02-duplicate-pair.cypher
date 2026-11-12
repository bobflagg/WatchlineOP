// Q2 rule: at most one HAS_REGISTRATION (so one pair of dates) per building and registration. Returns the violation count.
MATCH (b:Building)-[h:HAS_REGISTRATION]->(r:Registration)
WITH b, r, count(h) AS c WHERE c > 1
RETURN count(*) AS violationCount
