#!/usr/bin/env python3

import sys
sys.path.append('.')
import logging

# Set up detailed logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s:%(name)s:%(message)s')

from src.knowledge.external_ontologies import get_external_ontology_manager
from src.knowledge.concept_cache import get_concept_cache
from src.knowledge.ontology import Concept, ConceptType
from src.settings import Settings

def debug_enrichment():
    """Debug why concepts are not getting enriched."""
    print("=== DEBUGGING ENRICHMENT ISSUE ===\n")
    
    settings = Settings()
    print(f"DBpedia enabled: {settings.enable_dbpedia}")
    print(f"DBpedia auto enrich: {settings.dbpedia_auto_enrich}")
    print(f"DBpedia confidence threshold: {settings.dbpedia_confidence_threshold}")
    
    cache = get_concept_cache(settings)
    manager = get_external_ontology_manager(settings, cache)
    
    print(f"\nAvailable connectors: {list(manager.connectors.keys())}")
    
    # Test concepts that should definitely be enrichable
    test_concepts = [
        Concept(id="portfolio", name="Portfolio", concept_type=ConceptType.INVESTMENT_VEHICLE),
        Concept(id="capm", name="CAPM", concept_type=ConceptType.MODEL),
        Concept(id="beta", name="Beta", concept_type=ConceptType.RISK_MEASURE),
        Concept(id="alpha", name="Alpha", concept_type=ConceptType.PERFORMANCE_MEASURE),
        Concept(id="variance", name="Variance", concept_type=ConceptType.STATISTICAL_MEASURE)
    ]
    
    for concept in test_concepts:
        print(f"\n{'='*60}")
        print(f"TESTING CONCEPT: {concept.name} (type: {concept.concept_type})")
        print(f"{'='*60}")
        
        try:
            # Test enrichment
            enriched_concept = manager.enrich_concept(concept)
            
            # Check if enrichment was applied
            has_external = hasattr(enriched_concept, 'external_data') and enriched_concept.external_data
            print(f"Enriched: {has_external}")
            
            if has_external:
                print(f"External data: {enriched_concept.external_data}")
            else:
                print("No external data found")
                
                # Test individual connectors
                for connector_name, connector in manager.connectors.items():
                    print(f"\n--- Testing {connector_name} connector ---")
                    try:
                        results = connector.search_concept(concept.name, concept.concept_type)
                        print(f"Search results: {len(results) if results else 0}")
                        
                        if results:
                            for i, result in enumerate(results[:3]):
                                print(f"  {i+1}. {result.label} (confidence: {result.confidence:.3f})")
                                
                                # Test match scoring
                                match_score = connector._calculate_match_score(result, concept)
                                print(f"     Match score: {match_score:.3f}")
                                
                        else:
                            print("  No search results found")
                            
                    except Exception as e:
                        print(f"  Error testing {connector_name}: {e}")
                        import traceback
                        traceback.print_exc()
            
        except Exception as e:
            print(f"Error enriching {concept.name}: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    debug_enrichment()