// Q6.2: did the Operational Network method mask this address as an aggregator address, and with what degree?
// $address is the release's own text: uppercase, no city or ZIP, floor and unit text kept (the HPD street line, a space, then the
// second line). The release has no ZIP, so the answer also lists every ZIP of an HPD contact whose street line plus second line
// equals the text. Method, threshold, unit, normalizer version and run are one value each, recorded in data/sources.yaml.
// An empty result means the method did not mask this text, not that the address is safe.
MATCH (m:NetworkMaskedAddress {address: $address})
OPTIONAL MATCH (c:Contact)
WHERE c.mailingAddress IS NOT NULL
  AND toUpper(CASE WHEN c.addressLine2 IS NULL THEN c.mailingAddress ELSE c.mailingAddress + ' ' + c.addressLine2 END) = m.address
RETURN m.addressId AS addressId, m.address AS address, m.degree AS degree, m.maskedEdges AS maskedEdges,
       count(DISTINCT c) AS hpdContacts, collect(DISTINCT left(c.zip, 5)) AS hpdZips;
