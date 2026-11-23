// Q6.3: did the Owner Portfolio method mask this address as address evidence, and with what degree?
// $address is the derived text: uppercase, no city or ZIP, floor and unit text kept (the HPD street line, a space, then the second line).
// The release records the mask on identities, not addresses; the text is each masked identity's own business address as filed. The answer
// also lists every ZIP of an HPD contact whose street line plus second line equals the text. An empty result means no identity at this
// text was masked, not that the address is safe.
MATCH (m:PortfolioMaskedAddress {address: $address})
OPTIONAL MATCH (c:Contact)
WHERE c.mailingAddress IS NOT NULL
  AND toUpper(CASE WHEN c.addressLine2 IS NULL THEN c.mailingAddress ELSE c.mailingAddress + ' ' + c.addressLine2 END) = m.address
RETURN m.address AS address, m.degree AS degree, m.maskedIdentities AS maskedIdentities,
       count(DISTINCT c) AS hpdContacts, collect(DISTINCT left(c.zip, 5)) AS hpdZips;
