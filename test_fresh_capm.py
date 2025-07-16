#!/usr/bin/env python3

import sys
sys.path.append('.')

from src.knowledge.external_ontologies import get_external_ontology_manager
from src.knowledge.concept_cache import get_concept_cache
from src.knowledge.ontology import Concept, ConceptType
from src.settings import Settings

def test_fresh_capm():
    """Test CAPM with completely fresh cache."""
    print("=== TESTING FRESH CAPM ENRICHMENT ===\n")
    
    settings = Settings()
    cache = get_concept_cache(settings)
    
    # Completely clear cache
    print("Clearing all cache entries...")
    cache.clear('dbpedia')
    cache.clear('wikidata')
    
    manager = get_external_ontology_manager(settings, cache)
    
    # Test CAPM enrichment
    capm_concept = Concept(id="capm_test", name="CAPM", concept_type=ConceptType.MODEL)
    
    print("Testing CAPM enrichment with fresh cache...")
    enriched = manager.enrich_concept(capm_concept)
    
    print(f"Display name: '{enriched.name}'")
    print(f"Enriched: {'external_id' in enriched.properties}")
    
    if 'external_id' in enriched.properties:
        external_id = enriched.properties['external_id']
        description = enriched.description or 'N/A'
        
        print(f"External ID: {external_id}")
        print(f"Description: {description[:200]}...")
        
        # Check if it's the correct CAPM
        if 'Capital_asset_pricing_model' in external_id and 'Consumption-based' not in external_id:
            print("✅ SUCCESS: Got standard CAPM")
        elif 'Consumption-based' in external_id:
            print("❌ STILL WRONG: Got consumption-based CAPM")
            print("   This suggests a caching or selection issue")
        else:
            print("⚠️  Got different CAPM variant")
    else:
        print("❌ No enrichment applied")

def test_correlation_fresh():
    """Test correlation with fresh cache."""
    print("\n" + "="*60)
    print("TESTING FRESH CORRELATION ENRICHMENT")
    print("="*60)
    
    settings = Settings()
    cache = get_concept_cache(settings)
    manager = get_external_ontology_manager(settings, cache)
    
    correlation_concept = Concept(id="corr_test", name="Correlation", concept_type=ConceptType.STATISTICAL_MEASURE)
    
    print("Testing Correlation enrichment...")
    enriched = manager.enrich_concept(correlation_concept)
    
    print(f"Display name: '{enriched.name}'")
    print(f"Enriched: {'external_id' in enriched.properties}")
    
    if 'external_id' in enriched.properties:
        external_id = enriched.properties['external_id']
        description = enriched.description or 'N/A'
        
        print(f"External ID: {external_id}")
        print(f"Description: {description[:200]}...")
        
        # Check if it's the wrong correlation (Kendall's tau)
        if 'kendall' in description.lower() or 'tau' in description.lower():
            print("❌ STILL WRONG: Got Kendall's tau instead of general correlation")
        else:
            print("✅ SUCCESS: Got general correlation")
    else:
        print("❌ No enrichment applied")

if __name__ == '__main__':
    test_fresh_capm()
    test_correlation_fresh()