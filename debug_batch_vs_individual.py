#!/usr/bin/env python3

import sys
import asyncio
sys.path.append('.')

from src.frontend.api.graph import load_knowledge_graph, enrich_concepts_with_dbpedia_old
from src.knowledge.external_ontologies import get_external_ontology_manager
from src.knowledge.concept_cache import get_concept_cache
from src.knowledge.ontology import Concept, ConceptType
from src.settings import Settings

async def debug_batch_vs_individual():
    """Debug why Efficient Frontier works individually but fails in batch."""
    print("=== DEBUGGING BATCH VS INDIVIDUAL ENRICHMENT ===\n")
    
    settings = Settings()
    cache = get_concept_cache(settings)
    manager = get_external_ontology_manager(settings, cache)
    
    # Load graph data
    graph_data = load_knowledge_graph()
    concepts = graph_data.get("concepts", {})
    
    # Find Efficient Frontier
    efficient_frontier_id = None
    efficient_frontier_data = None
    for concept_id, concept_data in concepts.items():
        if concept_data.get('name') == 'Efficient Frontier':
            efficient_frontier_id = concept_id
            efficient_frontier_data = concept_data.copy()
            break
    
    if not efficient_frontier_data:
        print("❌ Efficient Frontier not found in knowledge graph")
        return
    
    print(f"Found Efficient Frontier: {efficient_frontier_id}")
    print(f"Current state: dbpedia_enriched={efficient_frontier_data.get('dbpedia_enriched')}")
    print(f"Current external_id: {efficient_frontier_data.get('external_id')}")
    
    # Test 1: Individual enrichment
    print(f"\n--- TEST 1: Individual Enrichment ---")
    concept = Concept(
        id=efficient_frontier_id,
        name='Efficient Frontier',
        concept_type=ConceptType.OPTIMIZATION
    )
    
    individual_enriched = manager.enrich_concept(concept)
    individual_has_external = 'external_id' in individual_enriched.properties
    individual_external_id = individual_enriched.properties.get('external_id', 'None')
    
    print(f"Individual result: {individual_has_external}")
    print(f"Individual external_id: {individual_external_id}")
    
    # Test 2: Batch enrichment with just Efficient Frontier
    print(f"\n--- TEST 2: Batch Enrichment (Single Concept) ---")
    single_concept_dict = {efficient_frontier_id: efficient_frontier_data}
    batch_single_result = await enrich_concepts_with_dbpedia_old(single_concept_dict, manager)
    
    batch_single_data = batch_single_result.get(efficient_frontier_id, {})
    batch_single_has_external = 'external_id' in batch_single_data
    batch_single_external_id = batch_single_data.get('external_id', 'None')
    
    print(f"Batch single result: {batch_single_has_external}")
    print(f"Batch single external_id: {batch_single_external_id}")
    
    # Test 3: Full batch enrichment 
    print(f"\n--- TEST 3: Full Batch Enrichment ---")
    batch_full_result = await enrich_concepts_with_dbpedia_old(concepts, manager)
    
    batch_full_data = batch_full_result.get(efficient_frontier_id, {})
    batch_full_has_external = 'external_id' in batch_full_data
    batch_full_external_id = batch_full_data.get('external_id', 'None')
    
    print(f"Full batch result: {batch_full_has_external}")
    print(f"Full batch external_id: {batch_full_external_id}")
    
    # Analysis
    print(f"\n--- ANALYSIS ---")
    if individual_has_external and not batch_full_has_external:
        print("❌ ISSUE: Individual enrichment works but batch enrichment fails")
        print("   This suggests a problem in the enrich_concepts_with_dbpedia_old function")
        
        # Check if the issue is with the concept creation in batch mode
        print("\nInvestigating concept creation in batch mode...")
        print(f"Original concept data keys: {list(efficient_frontier_data.keys())}")
        print(f"Original dbpedia_enriched: {efficient_frontier_data.get('dbpedia_enriched')}")
        
    elif individual_has_external and batch_single_has_external and not batch_full_has_external:
        print("❌ ISSUE: Works individually and in small batch, but fails in full batch")
        print("   This suggests interference from other concepts or resource limits")
        
    else:
        print("✅ No clear pattern found - need deeper investigation")

if __name__ == '__main__':
    asyncio.run(debug_batch_vs_individual())