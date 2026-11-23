// Q8.3: which landlords (HPD contact records) make up this Operational Network, what is each called, where does it file from, and which lots and
// HPD registrations does it cover? The name and addresses are as the release spells them: a label on a record, not a finding of who owns.
MATCH (n:OperationalNetwork {groupId: $groupId})<-[:IN_NETWORK]-(l:Lot)<-[c:COVERS]-(a:Landlord)
WITH a, collect({bbl: l.bbl, registrationId: c.registrationId}) AS lots
CALL (a) {
  OPTIONAL MATCH (a)-[:BASED_ON_CONTACT]->(k:Contact)<-[:HAS_CONTACT]-(r:Registration)
  RETURN collect(DISTINCT {registrationId: r.registrationId, contactType: k.contactType}) AS selectedContacts
}
RETURN a.nodeId AS nodeId, a.name AS name, a.businessAddresses AS businessAddresses, selectedContacts, lots
ORDER BY nodeId;
