// Q26.1: does the HPD registration data hold a record for this lot? $bbl is the lot. No row means the lot is not in the graph (outside the rental
// scope: unregistered with under 3 units); the answer says so. hpdRegistered false: the dataset holds no registration row, reason outside source
// coverage (no registration). The data does not say whether the lot is exempt or unregistered. Snapshot date: 2026-05-29.
MATCH (l:Lot {bbl: $bbl})
RETURN l.bbl AS bbl, l.hpdRegistered AS hpdRegistered, l.unitsRes AS unitsRes, l.yearBuilt AS yearBuilt;
