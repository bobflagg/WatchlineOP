// Q2.1: which HPD registrations does this building have, and when was each last filed and when does it end?
MATCH (b:Building {bin: $bin})
OPTIONAL MATCH (b)-[h:HAS_REGISTRATION]->(r:Registration)
RETURN b.bin AS bin, b.address AS address,
       collect(r {.registrationId, lastRegistered: toString(h.lastRegistered), registrationEnd: toString(h.registrationEnd)}) AS registrations;
