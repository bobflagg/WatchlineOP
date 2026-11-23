// Q7.5 entry: the lots of an entity found by name. $nameKey is the given name after rule N3. An entity's lots are those of the buildings
// whose HPD registrations carry a Contact with that name key (any contact type): a lead found by name, never a stored link.
OPTIONAL MATCH (:Contact {nameKey: $nameKey})<-[:HAS_CONTACT]-(:Registration)<-[:HAS_REGISTRATION]-(:Building)<-[:HAS_BUILDING]-(l:Lot)
RETURN collect(DISTINCT l.bbl) AS bbls;
