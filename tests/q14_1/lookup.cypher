// Q14.1: which deeds support the title holder of this lot on a date? $bbl is the lot, $date the date ('YYYY-MM-DD'; the caller chooses which
// violation date counts: inspection, notice issued or another), $basis is 'document' (document date, else recorded date: as now known) or
// 'recorded' (recorded date: what public record showed on the date). The supporting deeds are those with the latest date on or before $date; deeds
// that tie are all returned, none is chosen. A grantee is a title lead, not proof of title or of responsibility. An empty result means no deed in the
// snapshot on or before the date, never that the lot had no owner. recordedAfterDate: the deed was not yet recorded on the date (it is
// supported by its document date only). confirmatory: CORRD or CONDEED re-records an earlier transfer. otherLots: a multi-lot deed is one deed.
MATCH (l:Lot {bbl: $bbl})-[:HAS_DEED]->(d:Deed)
WITH l, d, CASE WHEN $basis = 'recorded' THEN d.recordedDate ELSE coalesce(d.docDate, d.recordedDate) END AS effDate
WHERE effDate <= date($date)
WITH l, max(effDate) AS latest, collect({deed: d, eff: effDate}) AS xs
UNWIND [x IN xs WHERE x.eff = latest] AS x
WITH l, x.deed AS d, x.eff AS effDate
CALL (d) {
  OPTIONAL MATCH (d)-[:HAS_GRANTEE]->(g:Grantee)
  RETURN collect(CASE WHEN g IS NULL THEN null ELSE g {.name, .nameKey} END) AS grantees
}
CALL (d) { MATCH (d)<-[:HAS_DEED]-(o:Lot) RETURN count(o) - 1 AS otherLots }
RETURN d.documentId AS documentId, d.docType AS docType, d.docDate AS docDate, d.recordedDate AS recordedDate, d.amount AS amount,
       effDate, d.docDate IS NULL AS docDateAbsent, d.recordedDate > date($date) AS recordedAfterDate,
       d.docType IN ['CORRD', 'CONDEED'] AS confirmatory, otherLots, grantees
ORDER BY documentId;
