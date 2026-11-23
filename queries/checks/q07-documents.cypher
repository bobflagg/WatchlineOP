// Q7 rules outside what shacl2cypher compiles. Returns the violation count:
//  - a party has hub counts exactly when it has a street line, except parties of documents loaded only by scope F (Q13), which carry none;
//  - every HAS_PARTY link carries partyType 1, 2 or 3;
//  - a document party belongs to exactly one document;
//  - a document party is not also a Contact, Grantee or Registration.
CALL () { MATCH (p:DocumentParty)
          WHERE (p.mailingAddress IS NULL AND (p.addressNames IS NOT NULL OR p.addressDocuments IS NOT NULL))
             OR (p.mailingAddress IS NOT NULL AND (p.addressNames IS NULL) <> (p.addressDocuments IS NULL))
             OR (p.mailingAddress IS NOT NULL AND p.addressNames IS NULL AND NOT EXISTS { MATCH (:Lot)-[:HAS_FINANCING_DOCUMENT]->(:Document)-[:HAS_PARTY]->(p) })
          RETURN count(p) AS a }
CALL () { MATCH (:Document)-[r:HAS_PARTY]->(:DocumentParty) WHERE r.partyType IS NULL OR NOT r.partyType IN [1, 2, 3] RETURN count(r) AS c }
CALL () { MATCH (p:DocumentParty) OPTIONAL MATCH (d:Document)-[:HAS_PARTY]->(p) WITH p, count(DISTINCT d) AS n WHERE n <> 1 RETURN count(p) AS d }
CALL () { MATCH (p:DocumentParty) WHERE p:Contact OR p:Grantee OR p:Registration RETURN count(p) AS e }
CALL () { MATCH (e:DosEntity) WHERE (e.processAddress IS NULL) <> (e.processAddressEntities IS NULL) RETURN count(e) AS f }
RETURN a + c + d + e + f AS violationCount;
