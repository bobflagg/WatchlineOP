// Q17.4: does this lot meet the registration dataset's unit threshold? $bbl is the lot, $threshold the dataset's minimum (3). unitsRes is PLUTO's
// lot-wide count, never summed across buildings. 0 means PLUTO records none, so the outcome is units-not-recorded, not below-threshold.
// yearBuilt is returned so a newly built lot can be reported with its year; the data does not say why it is unregistered. The answer does not
// rule on legal applicability beyond the threshold.
MATCH (l:Lot {bbl: $bbl})
RETURN l.bbl AS bbl, l.unitsRes AS unitsRes, $threshold AS threshold, l.yearBuilt AS yearBuilt,
       CASE WHEN l.unitsRes IS NULL OR l.unitsRes = 0 THEN 'units-not-recorded'
            WHEN l.unitsRes >= $threshold THEN 'meets-threshold' ELSE 'below-threshold' END AS thresholdOutcome;
