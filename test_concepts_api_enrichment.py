#!/usr/bin/env python3

import sys
import json
import asyncio
sys.path.append('.')

from src.frontend.api.graph import load_knowledge_graph, enrich_concepts_with_dbpedia_old
from src.knowledge.external_ontologies import get_external_ontology_manager
from src.knowledge.concept_cache import get_concept_cache
from src.settings import Settings

async def test_concepts_api_enrichment():
    """Test enrichment exactly as the Concepts API does it."""
    print("=== TESTING CONCEPTS API ENRICHMENT ===\n")
    
    settings = Settings()
    cache = get_concept_cache(settings)
    manager = get_external_ontology_manager(settings, cache)
    
    # Load graph data exactly like Concepts API
    graph_data = load_knowledge_graph()
    concepts = graph_data.get("concepts", {})
    
    print(f"Loaded {len(concepts)} concepts")
    
    # Test a few specific concepts
    test_concepts = {}
    for concept_id, concept_data in concepts.items():
        name = concept_data.get('name', '')
        if name in ['CAPM', 'Correlation', 'Return']:
            test_concepts[concept_id] = concept_data
            print(f"\nBEFORE enrichment - {name}:")
            print(f"  dbpedia_enriched: {concept_data.get('dbpedia_enriched', 'missing')}")
            print(f"  external_id: {concept_data.get('external_id', 'missing')}")
            print(f"  external_source: {concept_data.get('external_source', 'missing')}")
    
    # Apply enrichment exactly like Concepts API
    auto_enrich = getattr(settings, 'dbpedia_auto_enrich', True)
    enable_dbpedia = getattr(settings, 'enable_dbpedia', True)
    
    print(f"\nEnrichment settings: auto_enrich={auto_enrich}, enable_dbpedia={enable_dbpedia}")
    
    if auto_enrich and enable_dbpedia:
        try:
            print(f"Starting enrichment for {len(test_concepts)} test concepts...")
            enriched_concepts = await enrich_concepts_with_dbpedia_old(test_concepts, manager)
            print(f"Enrichment completed")
            
            # Check results
            for concept_id, concept_data in enriched_concepts.items():
                name = concept_data.get('name', '')
                print(f"\nAFTER enrichment - {name}:")
                print(f"  dbpedia_enriched: {concept_data.get('dbpedia_enriched', 'missing')}")
                print(f"  external_id: {concept_data.get('external_id', 'missing')}")
                print(f"  external_source: {concept_data.get('external_source', 'missing')}")
                print(f"  dbpedia_uri: {concept_data.get('dbpedia_uri', 'missing')}")
                
        except Exception as e:
            print(f"Enrichment failed: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("Enrichment disabled")

if __name__ == '__main__':
    asyncio.run(test_concepts_api_enrichment())