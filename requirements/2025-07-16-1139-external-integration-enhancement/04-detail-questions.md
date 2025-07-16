# Expert Requirements Questions

## Q6: Should we enhance the existing ExternalOntologyManager in src/knowledge/external_ontologies.py to automatically pull related concepts using SPARQL queries?
**Default if unknown:** Yes (leverages existing SPARQL infrastructure and the get_related_concepts() methods that are already implemented but underutilized)

## Q7: Do you want related external concepts to be added as secondary nodes that are visually distinct from primary document-derived concepts?
**Default if unknown:** Yes (prevents graph clutter while maintaining clear distinction between core document concepts and external knowledge expansion)

## Q8: Should we fix the cache serialization issue with ExternalConceptData objects to ensure external enrichment works reliably?
**Default if unknown:** Yes (critical for system stability - the current cache stores strings instead of proper objects, causing enrichment failures)

## Q9: Should we extend the sophisticated relationship_mapper.py scoring system to include external relationship confidence in the final relationship scores?
**Default if unknown:** Yes (the existing 5-component scoring system is well-designed and can incorporate external evidence as a 6th component)

## Q10: Do you want the enhanced tooltips to include DBpedia categories and properties that are already available from the API but not currently displayed?
**Default if unknown:** Yes (the API already provides this rich metadata, just needs frontend integration in the existing tooltip rendering logic at lines 313-452 in main.js)