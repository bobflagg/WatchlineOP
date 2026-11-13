// Q5.3: which registered agent does this DOS record list, and at what address? Absent means none listed (3.4 million of 4.2 million records list none).
// A commercial registered agent is a service company, not a person and not a lead.
MATCH (e:DosEntity {dosId: $dosId})
RETURN e.dosId AS dosId, e.agentName AS agentName, e.agentAddress AS agentAddress, e.agentAddressLine2 AS agentAddressLine2,
       e.agentCity AS agentCity, e.agentState AS agentState, e.agentZip AS agentZip;
