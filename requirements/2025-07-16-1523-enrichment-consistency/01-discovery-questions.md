# Discovery Questions - Phase 2

## Q1: Are you observing missing enrichment badges (DBpedia/Wikidata) on nodes that should have external data?
**Default if unknown:** Yes (this is the most common manifestation of enrichment inconsistency)

## Q2: Do some concepts with similar names get enriched while others do not?
**Default if unknown:** Yes (suggests matching algorithm inconsistencies)

## Q3: Are you seeing enrichment inconsistencies after clearing cache or restarting the system?
**Default if unknown:** No (cache clearing typically resolves most temporary inconsistencies)

## Q4: Do financial acronyms (like CAPM, VAR, ETF) show inconsistent enrichment compared to full terms?
**Default if unknown:** Yes (acronym handling is complex and prone to inconsistencies)

## Q5: Are you expecting all nodes in the knowledge graph to have some form of external enrichment?
**Default if unknown:** No (some concepts may legitimately not have external matches)