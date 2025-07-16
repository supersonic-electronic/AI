# Discovery Answers - Phase 2

## Q1: Are you observing missing enrichment badges (DBpedia/Wikidata) on nodes that should have external data?
**Answer:** Yes

## Q2: Do some concepts with similar names get enriched while others do not?
**Answer:** Yes

## Q3: Are you seeing enrichment inconsistencies after clearing cache or restarting the system?
**Answer:** Yes

## Q4: Do financial acronyms (like CAPM, VAR, ETF) show inconsistent enrichment compared to full terms?
**Answer:** No, but they are not spelled as acronyms (Capm vs CAPM)

## Q5: Are you expecting all nodes in the knowledge graph to have some form of external enrichment?
**Answer:** No

## Key Insights from Answers:
- The problem persists even after cache clearing/system restart (Q3=Yes), indicating it's not just a caching issue
- Similar concept names have inconsistent enrichment (Q2=Yes), suggesting matching algorithm issues
- Acronym casing inconsistency noted (Capm vs CAPM) - could be a normalization problem
- Not all nodes need enrichment (Q5=No), so we need to focus on concepts that should legitimately have enrichment