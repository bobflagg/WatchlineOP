// Q4 rule: corporationName appears only on agents and lessees. Returns the violation count.
MATCH (c:RoleContact)
WHERE c.corporationName IS NOT NULL AND NOT c.contactType IN ['Agent', 'Lessee']
RETURN count(c) AS violationCount
