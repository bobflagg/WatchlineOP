// Q5.2: where does the state forward legal papers for this DOS record? Process name and address as recorded. Absent means none recorded.
// The process name is where service goes, not who runs the entity; 'THE COMPANY' and 'THE LIMITED LIABILITY COMPANY' are the statutory default.
MATCH (e:DosEntity {dosId: $dosId})
RETURN e.dosId AS dosId, e.processName AS processName, e.processAddress AS processAddress, e.processAddressLine2 AS processAddressLine2,
       e.processCity AS processCity, e.processState AS processState, e.processZip AS processZip;
