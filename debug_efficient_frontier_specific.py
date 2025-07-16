#!/usr/bin/env python3

import sys
import asyncio
sys.path.append('.')

from src.frontend.api.graph import load_knowledge_graph, enrich_concepts_with_dbpedia_old
from src.knowledge.external_ontologies import get_external_ontology_manager
from src.knowledge.concept_cache import get_concept_cache
from src.knowledge.ontology import Concept, ConceptType
from src.settings import Settings

async def debug_efficient_frontier_specific():
    """Debug exactly what happens to Efficient Frontier during enrichment."""
    print("=== DEBUGGING EFFICIENT FRONTIER SPECIFIC ISSUE ===\n")
    
    settings = Settings()
    cache = get_concept_cache(settings)
    manager = get_external_ontology_manager(settings, cache)
    
    # Load graph data and find Efficient Frontier
    graph_data = load_knowledge_graph()
    concepts = graph_data.get("concepts", {})
    
    efficient_frontier_data = None
    efficient_frontier_id = None
    
    for concept_id, concept_data in concepts.items():
        if concept_data.get('name') == 'Efficient Frontier':
            efficient_frontier_id = concept_id
            efficient_frontier_data = concept_data.copy()
            break
    
    if not efficient_frontier_data:
        print("❌ Efficient Frontier not found")
        return
    
    print(f"Found Efficient Frontier: {efficient_frontier_id}")
    print(f"Original data: {efficient_frontier_data}")
    
    # Test enrichment step by step
    print(f"\n--- STEP 1: Create Concept Object ---")
    try:
        concept_type = ConceptType(efficient_frontier_data.get("type", "methodology"))
    except ValueError:
        concept_type = ConceptType.METHODOLOGY
    
    concept = Concept(
        id=efficient_frontier_id,
        name=efficient_frontier_data.get("name", "Unknown"),
        concept_type=concept_type,
        confidence=efficient_frontier_data.get("confidence", 1.0),
        description=efficient_frontier_data.get("description", "")
    )
    
    print(f"Created concept: {concept.name} (type: {concept.concept_type})")
    
    # Add existing properties
    print(f"\n--- STEP 2: Add Existing Properties ---")
    for key, value in efficient_frontier_data.items():
        if key not in ["name", "type", "confidence", "description"]:
            concept.properties[key] = value
    print(f"Added properties: {list(concept.properties.keys())}")
    
    # Test enrichment
    print(f"\n--- STEP 3: Apply Enrichment ---")
    enriched_concept = manager.enrich_concept(concept)
    
    print(f"Enrichment result:")
    print(f"  Name: {enriched_concept.name}")
    print(f"  Description: {(enriched_concept.description or 'None')[:100]}...")
    print(f"  Properties: {list(enriched_concept.properties.keys())}")
    print(f"  Has external_id: {'external_id' in enriched_concept.properties}")
    if 'external_id' in enriched_concept.properties:
        print(f"  External ID: {enriched_concept.properties['external_id']}")
        print(f"  External source: {enriched_concept.properties.get('external_source')}")
    
    # Test conversion back to dictionary (like the batch function does)
    print(f"\n--- STEP 4: Convert Back to Dictionary ---")
    enriched_data = efficient_frontier_data.copy()
    enriched_data.update({
        "name": enriched_concept.name,
        "description": enriched_concept.description or enriched_data.get("description", ""),
        "confidence": enriched_concept.confidence,
        "aliases": list(enriched_concept.aliases) if enriched_concept.aliases else enriched_data.get("aliases", []),
        "properties": {**enriched_data.get("properties", {}), **enriched_concept.properties}
    })
    
    print(f"Updated data keys: {list(enriched_data.keys())}")
    print(f"Has external_id: {'external_id' in enriched_data}")
    print(f"Properties: {enriched_data.get('properties', {})}")
    
    # Check external ontology metadata logic
    print(f"\n--- STEP 5: External Ontology Metadata Logic ---")
    external_source = enriched_concept.properties.get('external_source')
    has_dbpedia = external_source == 'dbpedia' or enriched_concept.properties.get('dbpedia_id')
    has_wikidata = external_source == 'wikidata' or enriched_concept.properties.get('wikidata_id')
    
    print(f"External source: {external_source}")
    print(f"Has DBpedia: {has_dbpedia}")
    print(f"Has Wikidata: {has_wikidata}")
    
    if external_source in ['dbpedia', 'wikidata'] or has_dbpedia or has_wikidata:
        print("✅ Should get external metadata")
        
        if has_dbpedia:
            dbpedia_uri = enriched_concept.properties.get('dbpedia_id') or (enriched_concept.properties.get('external_id') if external_source == 'dbpedia' else '')
            print(f"DBpedia URI: {dbpedia_uri}")
        
        # This is what should be added to enriched_data
        metadata_to_add = {
            "dbpedia_enriched": has_dbpedia,
            "wikidata_enriched": has_wikidata,
            "external_id": enriched_concept.properties.get('external_id', '') if external_source == 'dbpedia' else enriched_concept.properties.get('dbpedia_id', ''),
        }
        print(f"Metadata to add: {metadata_to_add}")
        
    else:
        print("❌ Would not get external metadata")
    
    # Test the actual batch function with just this concept
    print(f"\n--- STEP 6: Test Actual Batch Function ---")
    single_concept_dict = {efficient_frontier_id: efficient_frontier_data}
    batch_result = await enrich_concepts_with_dbpedia_old(single_concept_dict, manager)
    
    batch_concept_data = batch_result.get(efficient_frontier_id, {})
    batch_external_id = batch_concept_data.get('external_id', 'None')
    batch_enriched = batch_concept_data.get('dbpedia_enriched', 'None')
    
    print(f"Batch result external_id: {batch_external_id}")
    print(f"Batch result dbpedia_enriched: {batch_enriched}")
    
    if not batch_external_id or batch_external_id == 'None':
        print("❌ PROBLEM: Batch function is not preserving external_id")
    else:
        print("✅ Batch function works correctly")

if __name__ == '__main__':
    asyncio.run(debug_efficient_frontier_specific())