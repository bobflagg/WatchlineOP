// Q6.4: is this address on the curated mail-drop and registered-agent list, and with what kind?
// $address is the list's own key spelling: uppercase, street types abbreviated (AVE, ST), ordinals as 116TH, hyphens as spaces,
// no unit or floor. That is not HPD's spelling ("575 FIFTH AVE" is listed, "575 FIFTH AVENUE" is not), so a miss means "not listed
// under this spelling". $zip5 is the first five digits of the ZIP. A list row with no ZIP matches any ZIP and is reported as such.
// The list is preliminary: every row is unreviewed, and the kind is a project classification, not a finding about the parties.
MATCH (a:MailDropAddress {address: $address})
WHERE a.zip5 IS NULL OR a.zip5 = $zip5
RETURN a.address AS address, a.zip5 AS listZip, a.kind AS kind, a.basis AS basis, a.reviewStatus AS reviewStatus
ORDER BY listZip;
