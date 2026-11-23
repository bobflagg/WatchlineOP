// Q6 rules: masked address texts are unique within each method; no node carries two of the labels NetworkMaskedAddress, PortfolioMaskedAddress and
// MailDropAddress; the list key is address|zip5 (zip5 empty when absent); the identity counts of portfolio masked addresses sum to 5298 (the
// release's masked identities). Returns the violation count.
CALL () {
  MATCH (a:NetworkMaskedAddress)
  WITH a.address AS text, count(*) AS n
  WHERE n > 1
  RETURN count(text) AS duplicateText
}
CALL () {
  MATCH (a:PortfolioMaskedAddress)
  WITH a.address AS text, count(*) AS n
  WHERE n > 1
  RETURN count(text) AS duplicatePortfolioText
}
CALL () {
  MATCH (a)
  WHERE size([l IN labels(a) WHERE l IN ['NetworkMaskedAddress', 'PortfolioMaskedAddress', 'MailDropAddress']]) > 1
  RETURN count(a) AS bothLabels
}
CALL () {
  MATCH (a:PortfolioMaskedAddress)
  RETURN CASE WHEN count(a) = 0 THEN 0 WHEN sum(a.maskedIdentities) = 5298 THEN 0 ELSE 1 END AS badIdentityTotal
}
CALL () {
  MATCH (a:MailDropAddress)
  WHERE a.listKey <> a.address + '|' + coalesce(a.zip5, '')
  RETURN count(a) AS badListKey
}
RETURN duplicateText + duplicatePortfolioText + bothLabels + badListKey + badIdentityTotal AS violationCount
