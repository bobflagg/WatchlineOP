// Q5 rule: a DOS entity has no relationship to an owner contact, grantee, registration or anything else (a name match is a lead, computed at answer time).
MATCH (e:DosEntity)
WHERE EXISTS { (e)--() }
RETURN count(e) AS violationCount
