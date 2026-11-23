// Q4 rule: a site manager has no mailingAddress, addressLine2 or zip. Returns the violation count.
MATCH (c:Contact {contactType: 'SiteManager'})
WHERE c.mailingAddress IS NOT NULL OR c.addressLine2 IS NOT NULL OR c.zip IS NOT NULL
RETURN count(c) AS violationCount
