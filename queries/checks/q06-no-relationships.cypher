// Q6 rule: a masked address and a listed address have no relationship to anything. They are matched to HPD contact addresses by text at
// answer time; a stored link would hide the matching rule. Returns the violation count.
MATCH (a)
WHERE (a:NetworkMaskedAddress OR a:PortfolioMaskedAddress OR a:MailDropAddress) AND EXISTS { (a)--() }
RETURN count(a) AS violationCount
