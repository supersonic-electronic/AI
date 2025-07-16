#!/usr/bin/env python3

import sys
sys.path.append('.')
import json
from pathlib import Path

from src.frontend.api.graph import load_knowledge_graph, enrich_concepts_with_dbpedia_old
from src.knowledge.external_ontologies import get_external_ontology_manager
from src.knowledge.concept_cache import get_concept_cache
from src.settings import Settings
from src.knowledge.utils import generate_cache_key

async def regenerate_knowledge_graph():
    """Regenerate the knowledge graph with corrected enrichments."""
    print("=== REGENERATING KNOWLEDGE GRAPH WITH FIXES ===\n")
    
    settings = Settings()
    cache = get_concept_cache(settings)
    
    # Clear cache for problematic concepts to force re-enrichment
    problematic_concepts = ['CAPM', 'Correlation', 'Efficient frontier', 'Return', 'Sharpe Ratio', 'Expected Return', 'capm', 'correlation']
    
    print("Clearing cache for problematic concepts...")
    for concept_name in problematic_concepts:
        for connector_name in ['dbpedia', 'wikidata']:
            cache_key = generate_cache_key(f"{connector_name}Connector", concept_name)
            if cache.get(cache_key):
                cache.delete(cache_key)
                print(f"Cleared: {cache_key}")
    
    # Load original graph data
    print("\nLoading original knowledge graph...")
    graph_data = load_knowledge_graph()
    concepts = graph_data.get("concepts", {})
    
    print(f"Found {len(concepts)} concepts to re-enrich")
    
    # Apply enrichment with fixes
    print("\nApplying enrichment with improvements...")
    manager = get_external_ontology_manager(settings, cache)
    enriched_concepts = await enrich_concepts_with_dbpedia_old(concepts, manager)
    
    # Update graph data
    graph_data["concepts"] = enriched_concepts
    
    # Count improvements
    enriched_count = sum(1 for c in enriched_concepts.values() if c.get('dbpedia_enriched', False))
    print(f"Enriched {enriched_count}/{len(enriched_concepts)} concepts")
    
    # Check specific fixes
    print("\nValidating specific fixes:")
    fixed_concepts = {}
    
    for concept_id, concept_data in enriched_concepts.items():
        name = concept_data.get('name', '').lower()
        if name in ['capm', 'correlation', 'efficient frontier', 'return', 'expected return']:
            external_id = concept_data.get('external_id', '')
            description = concept_data.get('description', '')
            
            fixed_concepts[name] = {
                'name': concept_data.get('name'),
                'external_id': external_id,
                'description': description[:100]
            }
            
            print(f"✓ {concept_data.get('name')}: {external_id}")
    
    # Save updated knowledge graph
    output_file = Path("./data/knowledge_graph.json")
    backup_file = Path("./data/knowledge_graph_backup.json")
    
    # Create backup
    if output_file.exists():
        print(f"\nCreating backup: {backup_file}")
        with open(backup_file, 'w', encoding='utf-8') as f:
            with open(output_file, 'r', encoding='utf-8') as original:
                f.write(original.read())
    
    # Save new version
    print(f"Saving updated knowledge graph: {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(graph_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Knowledge graph regenerated successfully!")
    print(f"   File: {output_file}")
    print(f"   Total concepts: {len(enriched_concepts)}")
    print(f"   Enriched concepts: {enriched_count}")
    
    return fixed_concepts

def test_regenerated_api():
    """Test the API after regenerating the knowledge graph."""
    print(f"\n{'='*80}")
    print("TESTING REGENERATED API")
    print(f"{'='*80}")
    
    import requests
    
    try:
        # Test both APIs
        apis = [
            ("Graph API", "http://localhost:8000/api/graph?enrich_dbpedia=true"),
            ("Concepts API", "http://localhost:8000/api/concepts")
        ]
        
        for api_name, url in apis:
            print(f"\n--- {api_name} ---")
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                if api_name == "Graph API":
                    items = data.get('nodes', [])
                    concepts = {node.get('data', {}).get('name', ''): node.get('data', {}) for node in items}
                else:
                    items = data.get('concepts', [])
                    concepts = {concept.get('name', ''): concept for concept in items}
                
                # Check specific concepts
                for check_name in ['CAPM', 'Capm', 'Correlation']:
                    if check_name in concepts:
                        concept_data = concepts[check_name]
                        external_id = concept_data.get('external_id', '')
                        
                        print(f"  {check_name}: {external_id}")
                        
                        if check_name.lower() == 'capm' or check_name.lower() == 'capm':
                            if 'Capital_asset_pricing_model' in external_id and 'Consumption-based' not in external_id:
                                print(f"    ✅ CAPM fixed in {api_name}")
                            else:
                                print(f"    ❌ CAPM still wrong in {api_name}")
                                
                        elif check_name.lower() == 'correlation':
                            if 'Pearson' in external_id or ('correlation' in external_id.lower() and 'Kendall' not in external_id):
                                print(f"    ✅ Correlation fixed in {api_name}")
                            else:
                                print(f"    ❌ Correlation still wrong in {api_name}")
            else:
                print(f"  Error: {response.status_code}")
                
    except Exception as e:
        print(f"Error testing APIs: {e}")

if __name__ == '__main__':
    import asyncio
    
    async def main():
        fixed_concepts = await regenerate_knowledge_graph()
        test_regenerated_api()
    
    asyncio.run(main())