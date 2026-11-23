-- Q5.3 expected registered agent, from dos_active_corporations (data through 2026-07-06). verified against the frozen baseline recorded in data/README.md (2026-11-16).
-- Blank text is absent. 3,378,013 of 4,242,054 records list no agent. Agent address without a name: 0 in the scoped profile; a name without
-- an address: 71 (kept, address absent). A commercial agent is kept as recorded and is not a lead.
-- Expected 151265 (MADISON 79 ASSOCIATES, INC.): REGISTERED AGENT SOLUTIONS, INC., 99 WASHINGTON AVENUE, suite 700, ALBANY, 12260.
-- Expected 5857246 (anchor A): no agent.
SELECT dosid, nullif(btrim(registeredagentname),'') AS agent, nullif(btrim(registeredagentaddress1),'') AS line1, nullif(btrim(registeredagentaddress2),'') AS line2,
       nullif(btrim(registeredagentcity),'') AS city, nullif(btrim(registeredagentstate),'') AS state, nullif(btrim(registeredagentzip),'') AS zip
FROM dos_active_corporations WHERE dosid IN (151265, 128518, 5857246);
