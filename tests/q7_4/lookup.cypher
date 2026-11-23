// Q7.4: is a shared address set aside as non-evidence, and why? $street is the HPD street line (uppercase, trimmed), $line2 the HPD second line
// (null when none), $zip5 the first five ZIP characters, $listAddress the mail-drop list's own key spelling of the address (uppercase, street types
// abbreviated; null when the caller has none: then the list is not consulted and the answer says so). Three separate classifications, each reported
// with its own reason:
//   network mask  - Operational Network address mask (text = street, a space, line 2; the release has no ZIP), as Q6.2;
//   portfolio mask - Owner Portfolio address-evidence mask (derived text), as Q6.3;
//   mail drop      - the curated, preliminary, unreviewed list (a miss is not a clearance), as Q6.4.
// setAside is true when any classification marks the address. A shared address that none marks is used, with its hub count from Q7.1 to Q7.3.
// A mask is a method's decision and the list is a project classification; neither says who is behind the address.
WITH $street AS street, $line2 AS line2, $zip5 AS zip5, $listAddress AS listAddress,
     toUpper(CASE WHEN $line2 IS NULL THEN $street ELSE $street + ' ' + $line2 END) AS text
CALL (text) {
  OPTIONAL MATCH (m:NetworkMaskedAddress {address: text})
  RETURN m {.addressId, .address, .degree, .maskedEdges} AS networkMask
}
CALL (text) {
  OPTIONAL MATCH (m:PortfolioMaskedAddress {address: text})
  RETURN m {.address, .degree, .maskedIdentities} AS portfolioMask
}
CALL (listAddress, zip5) {
  OPTIONAL MATCH (a:MailDropAddress {address: listAddress}) WHERE listAddress IS NOT NULL AND (a.zip5 IS NULL OR a.zip5 = zip5)
  RETURN [x IN collect(a) WHERE x IS NOT NULL | x {listZip: x.zip5, .kind, .basis, .reviewStatus}] AS mailDrop
}
RETURN street, line2, zip5, listAddress, text, networkMask, portfolioMask, mailDrop,
       networkMask IS NOT NULL OR portfolioMask IS NOT NULL OR size(mailDrop) > 0 AS setAside,
       listAddress IS NULL AS listNotConsulted;
