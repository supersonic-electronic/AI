#!/usr/bin/env python3

import sys
sys.path.append('.')

from src.knowledge.external_ontologies import get_external_ontology_manager
from src.knowledge.concept_cache import get_concept_cache
from src.knowledge.ontology import Concept, ConceptType
from src.settings import Settings

def test_improved_enrichment():
    """Test enrichment with improvements for specific problematic concepts."""
    print("=== TESTING IMPROVED ENRICHMENT ===\n")
    
    settings = Settings()
    cache = get_concept_cache(settings)
    
    # Clear cache for fresh results
    print("Clearing cache to test improvements...")
    cache.clear('dbpedia')
    cache.clear('wikidata')
    
    manager = get_external_ontology_manager(settings, cache)
    
    # Test the problematic concepts
    test_concepts = [
        Concept(id="capm", name="capm", concept_type=ConceptType.MODEL),  # Test lowercase -> CAPM
        Concept(id="corr", name="Correlation", concept_type=ConceptType.STATISTICAL_MEASURE),
        Concept(id="ef", name="Efficient frontier", concept_type=ConceptType.OPTIMIZATION),
        Concept(id="ror", name="Return", concept_type=ConceptType.PERFORMANCE_MEASURE),  # Should match Rate of return
        Concept(id="sr", name="Sharpe Ratio", concept_type=ConceptType.PERFORMANCE_MEASURE)
    ]
    
    for concept in test_concepts:
        print(f"\n{'='*60}")
        print(f"TESTING: {concept.name} (original)")
        print(f"{'='*60}")
        
        try:
            enriched = manager.enrich_concept(concept)
            
            # Check results
            has_external = 'external_id' in enriched.properties
            external_id = enriched.properties.get('external_id', 'N/A')
            external_source = enriched.properties.get('external_source', 'N/A')
            description = enriched.description or 'N/A'
            
            print(f"Display name: '{enriched.name}' (fixed from '{concept.name}')")
            print(f"Enriched: {has_external}")
            print(f"External ID: {external_id}")
            print(f"Source: {external_source}")
            print(f"Description: {description[:150]}...")
            
            # Specific checks
            if concept.name.lower() == 'capm':
                if enriched.name == 'CAPM':
                    print("✅ CAPM casing fixed correctly")
                else:
                    print(f"❌ CAPM casing not fixed: '{enriched.name}'")
                    
                if 'consumption-based' not in description.lower():
                    print("✅ Avoided consumption-based CAPM")
                else:
                    print("❌ Still getting consumption-based CAPM")
                    
            elif concept.name.lower() == 'correlation':
                if 'kendall' not in description.lower() or 'tau' not in description.lower():
                    print("✅ Avoided Kendall's tau")
                else:
                    print("❌ Still getting Kendall's tau")
                    
            elif 'efficient frontier' in concept.name.lower():
                if 'resampled' not in description.lower():
                    print("✅ Avoided resampled efficient frontier")
                else:
                    print("❌ Still getting resampled efficient frontier")
                    
            elif concept.name.lower() == 'return':
                if 'rate of return' in description.lower() or 'investment' in description.lower():
                    print("✅ Got investment return concept")
                else:
                    print("❌ May not be investment-related return")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

def test_search_improvements():
    """Test search improvements for specific concepts."""
    print(f"\n{'='*80}")
    print("TESTING SEARCH IMPROVEMENTS")  
    print(f"{'='*80}")
    
    from src.knowledge.external_ontologies import get_external_ontology_manager
    from src.knowledge.concept_cache import get_concept_cache
    from src.settings import Settings
    
    settings = Settings()
    cache = get_concept_cache(settings)
    manager = get_external_ontology_manager(settings, cache)
    
    dbpedia_connector = manager.connectors['dbpedia']
    
    # Test search for CAPM to see if we get better results
    print("\n🔍 Testing CAPM search results:")
    capm_results = dbpedia_connector.search_concept('CAPM', ConceptType.MODEL)
    
    if capm_results:
        print(f"Found {len(capm_results)} results:")
        for i, result in enumerate(capm_results[:5]):
            print(f"  {i+1}. {result.label} (confidence: {result.confidence:.3f})")
            print(f"     ID: {result.external_id}")
            print(f"     Description: {result.description[:100]}...")
    else:
        print("No results found")

if __name__ == '__main__':
    test_improved_enrichment()
    test_search_improvements()