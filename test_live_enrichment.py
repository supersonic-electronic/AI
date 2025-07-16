#!/usr/bin/env python3

import sys
sys.path.append('.')

from src.knowledge.external_ontologies import get_external_ontology_manager
from src.knowledge.concept_cache import get_concept_cache
from src.knowledge.ontology import Concept, ConceptType
from src.settings import Settings

def test_live_enrichment():
    """Test enrichment with the actual system."""
    print("Testing live enrichment with consistency fixes...")
    
    settings = Settings()
    cache = get_concept_cache(settings)
    manager = get_external_ontology_manager(settings, cache)
    
    # Test concepts that should now be consistent
    test_concepts = [
        Concept(id="capm1", name="CAPM", concept_type=ConceptType.MODEL),
        Concept(id="capm2", name="capm", concept_type=ConceptType.MODEL),
        Concept(id="capm3", name="Capm", concept_type=ConceptType.MODEL),
        Concept(id="bs1", name="Black-Scholes", concept_type=ConceptType.MODEL),
        Concept(id="bs2", name="black-scholes", concept_type=ConceptType.MODEL),
    ]
    
    print("\nTesting enrichment consistency:")
    enrichment_results = {}
    
    for concept in test_concepts:
        print(f"\nEnriching concept: '{concept.name}' (ID: {concept.id})")
        try:
            enriched = manager.enrich_concept(concept)
            
            # Check if enrichment was applied
            has_enrichment = hasattr(enriched, 'external_data') and enriched.external_data
            enrichment_results[concept.name] = has_enrichment
            
            if has_enrichment:
                print(f"  ✓ Successfully enriched with: {enriched.external_data.get('source', 'unknown')}")
                print(f"    Label: {enriched.external_data.get('label', 'N/A')}")
                print(f"    Confidence: {enriched.external_data.get('confidence', 'N/A')}")
            else:
                print(f"  ○ No enrichment applied (may be legitimate)")
                
        except Exception as e:
            print(f"  ✗ Error enriching '{concept.name}': {e}")
            enrichment_results[concept.name] = False
    
    # Check consistency for concept variants
    print("\n" + "="*50)
    print("CONSISTENCY ANALYSIS:")
    
    capm_variants = ["CAPM", "capm", "Capm"]
    capm_results = [enrichment_results.get(variant, False) for variant in capm_variants]
    
    if all(result == capm_results[0] for result in capm_results):
        print(f"✓ CAPM variants consistent: all {'enriched' if capm_results[0] else 'unenriched'}")
    else:
        print(f"✗ CAPM variants inconsistent: {dict(zip(capm_variants, capm_results))}")
    
    bs_variants = ["Black-Scholes", "black-scholes"]
    bs_results = [enrichment_results.get(variant, False) for variant in bs_variants]
    
    if all(result == bs_results[0] for result in bs_results):
        print(f"✓ Black-Scholes variants consistent: all {'enriched' if bs_results[0] else 'unenriched'}")
    else:
        print(f"✗ Black-Scholes variants inconsistent: {dict(zip(bs_variants, bs_results))}")
    
    print("\n🎯 Enrichment consistency test complete!")

if __name__ == '__main__':
    test_live_enrichment()