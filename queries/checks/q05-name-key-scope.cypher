// Q5 rules: (a) nameKey is rule N3 of name; (b) every DosEntity's key equals the N3 key of a CorporateOwner owner name or a grantee name (scope).
// N3 = trim and collapse whitespace after: uppercase, drop periods, commas to spaces, drop apostrophes (src/watchline/compare.py).
// Returns the violation count (a + b).
CALL () {
  MATCH (e:DosEntity)
  WITH e, trim(reduce(s = '', w IN split(replace(replace(replace(replace(replace(replace(toUpper(e.name), '.', ''), ',', ' '), "'", ''), '\t', ' '), '\n', ' '), '\r', ' '), ' ') |
       CASE WHEN w = '' THEN s WHEN s = '' THEN w ELSE s + ' ' + w END)) AS k
  WHERE e.nameKey <> k
  RETURN count(e) AS badKey
}
CALL () {
  MATCH (e:DosEntity) RETURN count(e) AS total
}
CALL () {
  CALL () { MATCH (c:Contact {contactType: 'CorporateOwner'}) WHERE c.corporationName IS NOT NULL RETURN collect(DISTINCT c.corporationName) AS ownerNames }
  CALL () { MATCH (g:Grantee) WHERE g.name IS NOT NULL RETURN collect(DISTINCT g.name) AS granteeNames }
  UNWIND (ownerNames + granteeNames) AS nm
  WITH DISTINCT trim(reduce(s = '', w IN split(replace(replace(replace(replace(replace(replace(toUpper(toString(nm)), '.', ''), ',', ' '), "'", ''), '\t', ' '), '\n', ' '), '\r', ' '), ' ') |
       CASE WHEN w = '' THEN s WHEN s = '' THEN w ELSE s + ' ' + w END)) AS key
  MATCH (e:DosEntity {nameKey: key})
  RETURN count(DISTINCT e) AS inScope
}
RETURN badKey + (total - inScope) AS violationCount
