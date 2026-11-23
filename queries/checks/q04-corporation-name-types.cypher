// Q4 rule: corporationName appears only on corporate owners, agents and lessees. Returns the violation count.
MATCH (c:Contact)
WHERE c.corporationName IS NOT NULL AND NOT c.contactType IN ['CorporateOwner', 'Agent', 'Lessee']
RETURN count(c) AS violationCount
