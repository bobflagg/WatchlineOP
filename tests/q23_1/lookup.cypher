// Q23.1: which registrations and buildings disclose this managing agent, in what spellings and contact types?
// $nameKey is the corporation name under rule N3 (case-insensitive, no periods or apostrophes, single spaces); look it up through nameKey, never raw strings.
// Rows are per contact type: the managing agent is the contact type Agent; the same name may also be recorded in another role (for example CorporateOwner), reported apart and never added in. Variants that differ only by case, spacing or punctuation are combined; a legal suffix
// ("LLC") or a different word is a different key and is not combined. Counting units: distinct registrations, buildings (BIN) and lots (BBL).
// A shared agent is a management relationship, not ownership; a large footprint suggests a commercial service and does not prove one.
MATCH (c:Contact {nameKey: $nameKey})<-[:HAS_CONTACT]-(r:Registration)
OPTIONAL MATCH (b:Building)-[:HAS_REGISTRATION]->(r)
OPTIONAL MATCH (l:Lot)-[:HAS_BUILDING]->(b)
WITH c, r, b, l
RETURN c.contactType AS contactType, c.corporationName AS spelling,
       count(DISTINCT r) AS registrations, count(DISTINCT b) AS buildings, count(DISTINCT l) AS lots
ORDER BY contactType, registrations DESC, spelling;
