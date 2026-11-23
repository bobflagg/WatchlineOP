// Q23.3: at which business addresses does this managing agent disclose itself, and did the Operational Network or Owner Portfolio method mask any of them?
// $nameKey is the agent's corporation name under rule N3. An address is the HPD street line, a space, then the second line, uppercased (as Q6.2 and Q6.3).
// A mask is a method's setting aside of an address as evidence (Q6); an empty mask list means no method masked that text, not that the address is safe.
// The preliminary mail-drop list is not used (undefined, unreviewed). Contacts with no recorded address are counted apart. Counting unit: distinct contacts.
MATCH (c:Contact {nameKey: $nameKey, contactType: 'Agent'})
WITH c, CASE WHEN c.mailingAddress IS NULL THEN null
             WHEN c.addressLine2 IS NULL THEN toUpper(c.mailingAddress) ELSE toUpper(c.mailingAddress + ' ' + c.addressLine2) END AS address
OPTIONAL MATCH (n:NetworkMaskedAddress {address: address})
OPTIONAL MATCH (p:PortfolioMaskedAddress {address: address})
RETURN address, count(DISTINCT c) AS contacts, n.degree AS networkDegree, p.degree AS portfolioDegree
ORDER BY contacts DESC, address;
