#!/usr/bin/env python3

import sys
import traceback
sys.path.append('.')

from src.knowledge.external_ontologies import get_external_ontology_manager
from src.knowledge.concept_cache import get_concept_cache
from src.knowledge.ontology import Concept, ConceptType
from src.settings import Settings

def debug_sharpe_ratio_error():
    """Find the exact line causing AttributeError for Sharpe Ratio."""
    print("=== DEBUGGING SHARPE RATIO ATTRIBUTEERROR ===\n")
    
    settings = Settings()
    cache = get_concept_cache(settings)
    
    # Clear cache for fresh attempt
    from src.knowledge.utils import generate_cache_key
    for connector_name in ['dbpedia', 'wikidata']:
        cache_key = generate_cache_key(f"{connector_name}Connector", "Sharpe Ratio")
        if cache.get(cache_key):
            cache.delete(cache_key)
            print(f"Cleared cache: {cache_key}")
    
    manager = get_external_ontology_manager(settings, cache)
    
    concept = Concept(
        id='test_sharpe_debug',
        name='Sharpe Ratio',
        concept_type=ConceptType.PERFORMANCE_MEASURE
    )
    
    print("Testing each connector individually...\n")
    
    # Test DBpedia connector
    print("--- Testing DBpedia Connector ---")
    try:
        dbpedia_connector = manager.get_connector('dbpedia')
        if dbpedia_connector:
            dbpedia_results = dbpedia_connector.search_concept('Sharpe Ratio')
            print(f"DBpedia search successful: {len(dbpedia_results)} results")
            if dbpedia_results:
                # Try to get best match
                best_match = dbpedia_connector._get_best_match('Sharpe Ratio', dbpedia_results, concept.concept_type)
                print(f"Best match found: {best_match is not None}")
                if best_match:
                    print(f"Best match details: {best_match.label} -> {best_match.resource_uri}")
        else:
            print("No DBpedia connector found")
    except Exception as e:
        print(f"DBpedia error: {type(e).__name__}: {e}")
        traceback.print_exc()
    
    print()
    
    # Test Wikidata connector  
    print("--- Testing Wikidata Connector ---")
    try:
        wikidata_connector = manager.get_connector('wikidata')
        if wikidata_connector:
            wikidata_results = wikidata_connector.search_concept('Sharpe Ratio')
            print(f"Wikidata search successful: {len(wikidata_results)} results")
            if wikidata_results:
                # Try to get best match
                best_match = wikidata_connector._get_best_match('Sharpe Ratio', wikidata_results, concept.concept_type)
                print(f"Best match found: {best_match is not None}")
                if best_match:
                    print(f"Best match details: {best_match.label} -> {best_match.external_id}")
        else:
            print("No Wikidata connector found")
    except Exception as e:
        print(f"Wikidata error: {type(e).__name__}: {e}")
        traceback.print_exc()
    
    print()
    
    # Test full enrichment
    print("--- Testing Full Enrichment ---")
    try:
        enriched = manager.enrich_concept(concept)
        print(f"Full enrichment successful")
        print(f"Has external_id: {'external_id' in enriched.properties}")
        if 'external_id' in enriched.properties:
            print(f"External ID: {enriched.properties['external_id']}")
        print(f"Properties: {list(enriched.properties.keys())}")
    except Exception as e:
        print(f"Full enrichment error: {type(e).__name__}: {e}")
        traceback.print_exc()

if __name__ == '__main__':
    debug_sharpe_ratio_error()