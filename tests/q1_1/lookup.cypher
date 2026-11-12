// Q1.1: which tax lot does this address resolve to? The agent gets a BBL from Geosupport, then:
MATCH (l:Lot {bbl: $bbl})
RETURN l.bbl AS bbl, l.address AS address, l.hpdRegistered AS hpdRegistered;
