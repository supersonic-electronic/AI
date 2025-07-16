#!/usr/bin/env python3

import sys
sys.path.append('.')

from src.knowledge.external_ontologies import get_external_ontology_manager
from src.knowledge.concept_cache import get_concept_cache
from src.knowledge.ontology import Concept, ConceptType
from src.knowledge.utils import generate_cache_key
from src.settings import Settings

def fix_problematic_concepts():
    """Fix the specific problematic concepts by clearing their cache and re-enriching."""
    print("=== FIXING PROBLEMATIC CONCEPTS ===\n")
    
    settings = Settings()
    cache = get_concept_cache(settings)
    manager = get_external_ontology_manager(settings, cache)
    
    # Problematic concepts that need fixing
    problematic_concepts = [
        ("CAPM", ConceptType.MODEL, "Should get standard CAPM, not consumption-based"),
        ("Correlation", ConceptType.STATISTICAL_MEASURE, "Should get general correlation, not Kendall's tau"),
        ("Efficient frontier", ConceptType.OPTIMIZATION, "Should get standard efficient frontier"),
        ("Return", ConceptType.PERFORMANCE_MEASURE, "Should get rate of return"),
        ("Sharpe Ratio", ConceptType.PERFORMANCE_MEASURE, "Should get Sharpe ratio")
    ]
    
    for concept_name, concept_type, expected in problematic_concepts:
        print(f"\n{'='*60}")
        print(f"FIXING: {concept_name}")
        print(f"Expected: {expected}")
        print(f"{'='*60}")
        
        # Clear cache entries for this concept from all connectors
        for connector_name in ['dbpedia', 'wikidata']:
            cache_key = generate_cache_key(f"{connector_name}Connector", concept_name)
            if cache.get(cache_key):
                cache.delete(cache_key)
                print(f"Cleared cache: {cache_key}")
        
        # Create concept and enrich
        concept = Concept(
            id=f"fix_{concept_name.lower().replace(' ', '_')}", 
            name=concept_name, 
            concept_type=concept_type
        )
        
        print(f"Re-enriching '{concept_name}' with fresh data...")
        enriched = manager.enrich_concept(concept)
        
        # Check results
        has_external = 'external_id' in enriched.properties
        if has_external:
            external_id = enriched.properties['external_id']
            external_source = enriched.properties['external_source']
            description = enriched.description or 'N/A'
            
            print(f"✅ Enriched successfully")
            print(f"   Display name: '{enriched.name}'")
            print(f"   External ID: {external_id}")
            print(f"   Source: {external_source}")
            print(f"   Description: {description[:150]}...")
            
            # Validate the fix
            concept_lower = concept_name.lower()
            if concept_lower == 'capm':
                if 'Consumption-based' not in external_id:
                    print("   ✅ FIXED: Got standard CAPM")
                else:
                    print("   ❌ STILL BROKEN: Got consumption-based CAPM")
                    
            elif concept_lower == 'correlation':
                if 'Kendall' not in external_id and 'kendall' not in description.lower():
                    print("   ✅ FIXED: Got general correlation")
                else:
                    print("   ❌ STILL BROKEN: Got Kendall's tau")
                    
            elif 'efficient frontier' in concept_lower:
                if 'Resampled' not in external_id:
                    print("   ✅ FIXED: Got standard efficient frontier")
                else:
                    print("   ❌ STILL BROKEN: Got resampled efficient frontier")
                    
            elif concept_lower == 'return':
                if 'rate_of_return' in external_id.lower() or 'return' in external_id.lower():
                    print("   ✅ FIXED: Got rate of return")
                else:
                    print("   ❌ May not be correct return concept")
                    
        else:
            print("❌ No enrichment applied")

def test_api_after_fix():
    """Test API endpoints after fixing problematic concepts."""
    print(f"\n{'='*80}")
    print("TESTING API AFTER FIXES")
    print(f"{'='*80}")
    
    import requests
    
    try:
        # Test graph API
        response = requests.get("http://localhost:8000/api/graph?enrich_dbpedia=true", timeout=30)
        if response.status_code == 200:
            data = response.json()
            nodes = data.get('nodes', [])
            
            # Find specific concepts
            for node in nodes:
                node_data = node.get('data', {})
                name = node_data.get('name', '')
                
                if name.lower() in ['capm', 'correlation']:
                    description = node_data.get('description', '')
                    external_id = node_data.get('external_id', '')
                    
                    print(f"\n📋 {name}:")
                    print(f"   External ID: {external_id}")
                    print(f"   Description: {description[:100]}...")
                    
                    if name.lower() == 'capm' and 'Consumption-based' not in external_id:
                        print("   ✅ CAPM is fixed in API")
                    elif name.lower() == 'correlation' and 'Kendall' not in external_id:
                        print("   ✅ Correlation is fixed in API")
        else:
            print(f"API request failed: {response.status_code}")
            
    except Exception as e:
        print(f"Error testing API: {e}")

if __name__ == '__main__':
    fix_problematic_concepts()
    test_api_after_fix()