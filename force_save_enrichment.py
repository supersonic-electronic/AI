#!/usr/bin/env python3

import sys
import json
import asyncio
from pathlib import Path
sys.path.append('.')

from src.frontend.api.graph import load_knowledge_graph, enrich_concepts_with_dbpedia_old  
from src.knowledge.external_ontologies import get_external_ontology_manager
from src.knowledge.concept_cache import get_concept_cache
from src.knowledge.utils import generate_cache_key
from src.settings import Settings

async def force_save_enrichment():
    """Force save enrichment data to knowledge graph with validation."""
    print("=== FORCE SAVING ENRICHMENT WITH VALIDATION ===\n")
    
    settings = Settings()
    cache = get_concept_cache(settings)
    manager = get_external_ontology_manager(settings, cache)
    
    # Clear cache for problematic concepts
    problematic_concepts = ['Efficient Frontier', 'Sharpe Ratio', 'Risk', 'Mean Variance', 'Asset Allocation', 'Variance']
    
    print("Clearing cache for problematic concepts...")
    for concept_name in problematic_concepts:
        for connector_name in ['dbpedia', 'wikidata']:
            cache_key = generate_cache_key(f"{connector_name}Connector", concept_name)
            if cache.get(cache_key):
                cache.delete(cache_key)
                print(f"  Cleared: {cache_key}")
    
    # Load and reset graph data
    graph_data = load_knowledge_graph()
    concepts = graph_data.get("concepts", {})
    
    # Reset enrichment flags for problematic concepts
    print(f"\nResetting enrichment flags for problematic concepts...")
    for concept_id, concept_data in concepts.items():
        name = concept_data.get('name', '')
        if name in problematic_concepts:
            concept_data['dbpedia_enriched'] = False
            concept_data['wikidata_enriched'] = False
            concept_data['external_source'] = 'local'
            if 'external_id' in concept_data:
                del concept_data['external_id']
            print(f"  Reset: {name}")
    
    # Apply enrichment 
    print(f"\nApplying enrichment to {len(concepts)} concepts...")
    enriched_concepts = await enrich_concepts_with_dbpedia_old(concepts, manager)
    
    # Validate specific concepts before saving
    print(f"\nValidating enrichment before saving...")
    validation_results = {}
    critical_concepts = ['Efficient Frontier', 'Expected Return', 'CAPM', 'Correlation', 'Return']
    
    for concept_id, concept_data in enriched_concepts.items():
        name = concept_data.get('name', '')
        if name in critical_concepts:
            external_id = concept_data.get('external_id', '')
            dbpedia_enriched = concept_data.get('dbpedia_enriched', False)
            
            validation_results[name] = {
                'external_id': external_id,
                'dbpedia_enriched': dbpedia_enriched,
                'has_enrichment': bool(external_id and dbpedia_enriched)
            }
            
            status = "✅" if validation_results[name]['has_enrichment'] else "❌"
            print(f"  {status} {name}: external_id='{external_id}', enriched={dbpedia_enriched}")
    
    # Only save if critical concepts are properly enriched
    critical_enriched = sum(1 for r in validation_results.values() if r['has_enrichment'])
    total_critical = len(validation_results)
    
    print(f"\nCritical concepts enriched: {critical_enriched}/{total_critical}")
    
    if critical_enriched >= 4:  # Require at least 4/5 critical concepts to be enriched
        # Save the knowledge graph
        output_file = Path("./data/knowledge_graph.json")
        backup_file = Path("./data/knowledge_graph_backup_force_save.json")
        
        # Create backup
        if output_file.exists():
            print(f"\nCreating backup: {backup_file}")
            with open(backup_file, 'w', encoding='utf-8') as f:
                with open(output_file, 'r', encoding='utf-8') as original:
                    f.write(original.read())
        
        # Update and save
        graph_data["concepts"] = enriched_concepts
        print(f"Saving knowledge graph: {output_file}")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(graph_data, f, indent=2, ensure_ascii=False)
        
        # Post-save validation
        print(f"\nPost-save validation...")
        with open(output_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        
        for name in critical_concepts:
            for concept_id, concept_data in saved_data['concepts'].items():
                if concept_data.get('name') == name:
                    saved_external_id = concept_data.get('external_id', '')
                    saved_enriched = concept_data.get('dbpedia_enriched', False)
                    status = "✅" if saved_external_id and saved_enriched else "❌"
                    print(f"  {status} {name}: Saved correctly")
                    break
        
        print(f"\n✅ Force save completed successfully!")
        return True
    else:
        print(f"\n❌ Not saving - insufficient critical concepts enriched ({critical_enriched}/{total_critical})")
        return False

if __name__ == '__main__':
    success = asyncio.run(force_save_enrichment())
    if success:
        print("✅ All critical concepts should now have proper enrichment in the saved file")
    else:
        print("❌ Save aborted due to enrichment failures")