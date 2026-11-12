// Q2 rule: registrationEnd is never before lastRegistered (when both are present). Returns the violation count.
MATCH (:Building)-[h:HAS_REGISTRATION]->(:Registration)
WHERE h.lastRegistered IS NOT NULL AND h.registrationEnd IS NOT NULL AND h.registrationEnd < h.lastRegistered
RETURN count(h) AS violationCount
