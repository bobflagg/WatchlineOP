// Q17.3: is this lot's latest registration older than its latest deed? $bbl is the lot. latestRegistered is the latest lastRegistered over the lot's
// registrations (undated ones ignored). The latest deed is the one recorded last; deeds recorded that day are all returned, none is chosen.
// olderThanDeed: holds when latestRegistered is before the deed's recorded date, does-not-hold when it is the same day or later, cannot-tell with
// no deed, no dated registration or no registration. notASale: amount 0, or CORRD or CONDEED (Q12); a correction is not read as a transfer.
MATCH (l:Lot {bbl: $bbl})
CALL (l) {
  OPTIONAL MATCH (l)-[:HAS_BUILDING]->(:Building)-[h:HAS_REGISTRATION]->(:Registration)
  RETURN max(h.lastRegistered) AS latestRegistered
}
CALL (l) {
  OPTIONAL MATCH (l)-[:HAS_DEED]->(d:Deed)
  WITH max(d.recordedDate) AS latestRecorded
  OPTIONAL MATCH (l)-[:HAS_DEED]->(d:Deed) WHERE d.recordedDate = latestRecorded
  RETURN latestRecorded, collect(CASE WHEN d IS NULL THEN null ELSE d {.documentId, .docType, .docDate, .recordedDate, .amount,
         notASale: d.amount = 0 OR d.docType IN ['CORRD', 'CONDEED']} END) AS deeds
}
RETURN l.bbl AS bbl, latestRegistered, latestRecorded AS latestDeedRecorded, [x IN deeds WHERE x IS NOT NULL] AS latestDeeds,
       CASE WHEN latestRegistered IS NULL OR latestRecorded IS NULL THEN 'cannot-tell'
            WHEN latestRegistered < latestRecorded THEN 'holds' ELSE 'does-not-hold' END AS olderThanDeed;
