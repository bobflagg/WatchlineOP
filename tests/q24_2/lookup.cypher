// Q24.2: which records carry this person's name, in what roles, and how many? Every row is a lead (a name alone), never a match: common
// personal names return unrelated people. $person is the name as given, upper case with single spaces, in HPD's order (first, middle initial, last).
// $reversed is the same name with the first and last words swapped (ACRIS often records "LAST FIRST"), or null for a one-word name; deed parties
// are searched under both orders and each row says which. Counts are distinct registrations, buildings, lots and deeds; samples are the first ten ids.
CALL () {
  MATCH (c:Contact) WHERE toUpper(c.personName) = $person
  OPTIONAL MATCH (r:Registration)-[:HAS_CONTACT]->(c)
  OPTIONAL MATCH (b:Building)-[:HAS_REGISTRATION]->(r)
  OPTIONAL MATCH (l:Lot)-[:HAS_BUILDING]->(b)
  WITH c.contactType AS role, collect(DISTINCT c) AS cs, collect(DISTINCT r) AS rs, collect(DISTINCT b) AS bs, collect(DISTINCT l) AS ls
  RETURN 'hpd_contacts' AS source, role, 'as given' AS order, size(rs) AS records, size(bs) AS buildings, size(ls) AS lots,
         [x IN rs | x.registrationId][..10] AS sample
  UNION
  UNWIND [['as given', $person], ['reversed', $reversed]] AS o
  WITH o WHERE o[1] IS NOT NULL
  MATCH (l:Lot)-[:HAS_DEED]->(d:Deed)-[rel:HAS_GRANTEE|HAS_GRANTOR]->(p {nameKey: o[1]})
  WITH o[0] AS order, CASE type(rel) WHEN 'HAS_GRANTEE' THEN 'grantee' ELSE 'grantor' END AS role, collect(DISTINCT d.documentId) AS ds, collect(DISTINCT l.bbl) AS ls
  RETURN 'acris_parties' AS source, role, order, size(ds) AS records, null AS buildings, size(ls) AS lots, ds[..10] AS sample
}
RETURN source, role, order, records, buildings, lots, sample ORDER BY source, role, order;
