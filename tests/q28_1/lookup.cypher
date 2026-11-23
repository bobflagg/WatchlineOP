// Q28.1: which Housing Court cases did HPD record against this building? $bin is the building.
// Counting unit: cases. A case is an action brought, not a finding of fault; a harassment finding exists only when harassmentFinding is
// 'After Inquest' or 'After Trial' ('No Harassment' is a recorded outcome, not a finding). Values are as recorded; absent means HPD records none.
// A caseOpenDate before 1990 or after the snapshot (data through 2026-07-09) is a source error: report it, never correct it.
// An empty result means no case in the snapshot for this building (or the BIN is outside the registered scope), not that none was ever brought.
MATCH (b:Building {bin: $bin})-[:HAS_LITIGATION]->(c:Litigation)
RETURN c.litigationId AS litigationId, c.caseType AS caseType, c.caseOpenDate AS caseOpenDate, c.caseStatus AS caseStatus,
       c.openJudgement AS openJudgement, c.harassmentFinding AS harassmentFinding, c.findingDate AS findingDate, c.penalty AS penalty,
       c.respondent AS respondent, c.respondentKeys AS respondentKeys
ORDER BY caseOpenDate, litigationId;
