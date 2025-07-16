# Expert Requirements Answers

## Q6: Should we enhance the existing ExternalOntologyManager in src/knowledge/external_ontologies.py to automatically pull related concepts using SPARQL queries?
**Answer:** Yes

## Q7: Do you want related external concepts to be added as secondary nodes that are visually distinct from primary document-derived concepts?
**Answer:** No - integrate both sources into 1 note, give preference to local source and fill in as needed.

## Q8: Should we fix the cache serialization issue with ExternalConceptData objects to ensure external enrichment works reliably?
**Answer:** Yes

## Q9: Should we extend the sophisticated relationship_mapper.py scoring system to include external relationship confidence in the final relationship scores?
**Answer:** Yes

## Q10: Do you want the enhanced tooltips to include DBpedia categories and properties that are already available from the API but not currently displayed?
**Answer:** Yes

## Key Requirements Clarification

**Critical Insight from Q7:** The user wants **unified concept integration** rather than separate nodes. This means:
- Local concepts should be enriched with external data in-place
- External metadata should fill gaps in local concept data
- Local source data takes precedence when conflicts exist
- No separate "secondary" external nodes - everything merges into enhanced local concepts