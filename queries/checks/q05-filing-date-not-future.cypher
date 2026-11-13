// Q5 rule: initialFilingDate is not after the snapshot date (2026-07-06). Returns the violation count.
MATCH (e:DosEntity)
WHERE e.filingDate > date('2026-07-06')
RETURN count(e) AS violationCount
