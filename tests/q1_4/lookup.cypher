// Q1.4: what are the year built, building class, residential units and assessed value of this tax lot?
// Properties are PLUTO 26v1. Absent (null) means PLUTO has no value or the lot is not in PLUTO.
// unitsRes and assessedTotal of 0 are PLUTO values, not "no housing". unitsRes is lot-wide: never sum it across BINs.
MATCH (l:Lot {bbl: $bbl})
RETURN l.bbl AS bbl, l.yearBuilt AS yearBuilt, l.buildingClass AS buildingClass,
       l.unitsRes AS unitsRes, l.assessedTotal AS assessedTotal;
