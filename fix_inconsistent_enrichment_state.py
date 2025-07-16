#!/usr/bin/env python3

import sys
import json
sys.path.append('.')

from pathlib import Path
from src.frontend.api.graph import load_knowledge_graph
from src.knowledge.concept_cache import get_concept_cache
from src.knowledge.utils import generate_cache_key
from src.settings import Settings

def fix_inconsistent_enrichment_state():
    """Fix concepts that have dbpedia_enriched=True but missing external metadata."""
    print("=== FIXING INCONSISTENT ENRICHMENT STATE ===\n")
    
    settings = Settings()
    cache = get_concept_cache(settings)
    
    # Load knowledge graph
    graph_data = load_knowledge_graph()
    concepts = graph_data.get("concepts", {})
    
    # Find concepts with inconsistent state
    inconsistent_concepts = []
    for concept_id, concept_data in concepts.items():
        dbpedia_enriched = concept_data.get('dbpedia_enriched', False)
        external_id = concept_data.get('external_id')
        external_source = concept_data.get('external_source', 'local')
        
        # Check for inconsistent state: marked as enriched but missing external data
        if dbpedia_enriched and (not external_id or external_source == 'local'):
            inconsistent_concepts.append({
                'id': concept_id,
                'name': concept_data.get('name', 'Unknown'),
                'dbpedia_enriched': dbpedia_enriched,
                'external_id': external_id,
                'external_source': external_source
            })
    
    print(f"Found {len(inconsistent_concepts)} concepts with inconsistent enrichment state:")
    for concept in inconsistent_concepts:
        print(f"  - {concept['name']} (ID: {concept['id']})")
        print(f"    dbpedia_enriched: {concept['dbpedia_enriched']}")
        print(f"    external_id: {concept['external_id']}")
        print(f"    external_source: {concept['external_source']}")
        print()
    
    if not inconsistent_concepts:
        print("No inconsistent concepts found.")
        return
    
    # Clear cache for these concepts to force re-enrichment
    print("Clearing cache for inconsistent concepts...")
    for concept in inconsistent_concepts:
        concept_name = concept['name']
        for connector_name in ['dbpedia', 'wikidata']:
            cache_key = generate_cache_key(f"{connector_name}Connector", concept_name)
            if cache.get(cache_key):
                cache.delete(cache_key)
                print(f"  Cleared cache: {cache_key}")
    
    # Reset enrichment flags for inconsistent concepts
    print("\nResetting enrichment flags...")
    for concept in inconsistent_concepts:
        concept_id = concept['id']
        concept_data = concepts[concept_id]
        
        # Reset enrichment flags to force re-enrichment
        concept_data['dbpedia_enriched'] = False
        concept_data['wikidata_enriched'] = False
        concept_data['external_source'] = 'local'
        
        # Remove external metadata to clean state
        if 'external_id' in concept_data:
            del concept_data['external_id']
        if 'external_confidence' in concept_data:
            del concept_data['external_confidence']
        if 'dbpedia_uri' in concept_data:
            del concept_data['dbpedia_uri']
        
        print(f"  Reset: {concept['name']}")
    
    # Save the cleaned knowledge graph
    output_file = Path("./data/knowledge_graph.json")
    backup_file = Path("./data/knowledge_graph_backup_before_state_fix.json")
    
    # Create backup
    if output_file.exists():
        print(f"\nCreating backup: {backup_file}")
        with open(backup_file, 'w', encoding='utf-8') as f:
            with open(output_file, 'r', encoding='utf-8') as original:
                f.write(original.read())
    
    # Save cleaned version
    print(f"Saving cleaned knowledge graph: {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(graph_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Fixed inconsistent enrichment state for {len(inconsistent_concepts)} concepts")
    print("   These concepts will now be re-enriched on next API call")

if __name__ == '__main__':
    fix_inconsistent_enrichment_state()