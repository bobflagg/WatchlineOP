// Q20.1: the recorded trail of a lot is the union of the component lookups, run in this order and merged by no rule of their own:
//   1. tests/q1_2/lookup.cypher   buildings of the lot ($bbl)
//   2. tests/q2_2/lookup.cypher   registered owner contacts per building ($bin)
//   3. tests/q3_1/lookup.cypher   latest deeds of the lot ($bbl)
//   4. tests/q5_1 and q5_2        DOS candidates by name key and process address ($key, $dosId)
//   5. tests/q11_1/lookup.cypher  recorded mortgages naming the owner ($nameKey)
//   6. tests/q7_1/lookup.cypher   addresses shared with a named entity ($nameKeyA, $nameKeyB)
//   7. tests/q10_1/lookup.cypher  Operational Network and Owner Portfolio (apart, as leads)
// The dossier adds no fact and joins none: each section keeps its own source, date and caveats. Nothing is stored for Q20.
RETURN 'composed from the component lookups' AS note;
