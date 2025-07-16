#!/usr/bin/env python3

import sys
import asyncio
sys.path.append('.')

from src.frontend.api.graph import load_knowledge_graph, enrich_concepts_with_dbpedia_old
from src.knowledge.external_ontologies import get_external_ontology_manager
from src.knowledge.concept_cache import get_concept_cache
from src.settings import Settings

async def debug_concepts_api():
    """Debug why Concepts API enrichment isn't working."""
    print("=== DEBUGGING CONCEPTS API ENRICHMENT ===\n")
    
    settings = Settings()
    cache = get_concept_cache(settings)
    manager = get_external_ontology_manager(settings, cache)
    
    # Load graph data (same as Concepts API)
    print("Loading knowledge graph...")
    graph_data = load_knowledge_graph()
    concepts = graph_data.get("concepts", {})
    
    print(f"Loaded {len(concepts)} concepts")
    
    # Check specific concept before enrichment
    capm_concept = None
    for concept_id, concept_data in concepts.items():
        if concept_data.get('name') == 'CAPM':
            capm_concept = concept_data.copy()
            capm_concept['id'] = concept_id
            print(f"\nCAPM BEFORE enrichment:")
            print(f"  Name: {capm_concept.get('name')}")
            print(f"  ID: {concept_id}")
            print(f"  Has external_id: {'external_id' in capm_concept}")
            print(f"  Has dbpedia_enriched: {'dbpedia_enriched' in capm_concept}")
            print(f"  Description: {capm_concept.get('description', 'N/A')[:100]}...")
            break
    
    # Apply enrichment (same as Concepts API)
    print(f"\nApplying enrichment to {len(concepts)} concepts...")
    try:
        enriched_concepts = await enrich_concepts_with_dbpedia_old(concepts, manager)
        print(f"Enrichment completed")
    except Exception as e:
        print(f"Enrichment failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Check CAPM after enrichment
    for concept_id, concept_data in enriched_concepts.items():
        if concept_data.get('name') == 'CAPM':
            print(f"\nCAPM AFTER enrichment:")
            print(f"  Name: {concept_data.get('name')}")
            print(f"  ID: {concept_id}")
            print(f"  Has external_id: {'external_id' in concept_data}")
            print(f"  External ID: {concept_data.get('external_id', 'N/A')}")
            print(f"  Has dbpedia_enriched: {'dbpedia_enriched' in concept_data}")
            print(f"  DBpedia enriched: {concept_data.get('dbpedia_enriched', False)}")
            print(f"  Description: {concept_data.get('description', 'N/A')[:100]}...")
            break
    
    # Count enriched vs total
    enriched_count = sum(1 for c in enriched_concepts.values() if c.get('dbpedia_enriched', False))
    total_count = len(enriched_concepts)
    
    print(f"\nENRICHMENT SUMMARY:")
    print(f"  Total concepts: {total_count}")
    print(f"  Enriched concepts: {enriched_count}")
    print(f"  Enrichment rate: {enriched_count/total_count*100:.1f}%")

if __name__ == '__main__':
    asyncio.run(debug_concepts_api())