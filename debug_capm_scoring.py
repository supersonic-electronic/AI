#!/usr/bin/env python3

import sys
sys.path.append('.')

from src.knowledge.external_ontologies import get_external_ontology_manager
from src.knowledge.concept_cache import get_concept_cache
from src.knowledge.ontology import Concept, ConceptType
from src.settings import Settings

def debug_capm_scoring():
    """Debug CAPM scoring to see why consumption-based is being selected."""
    print("=== DEBUGGING CAPM SCORING ===\n")
    
    settings = Settings()
    cache = get_concept_cache(settings)
    manager = get_external_ontology_manager(settings, cache)
    
    dbpedia_connector = manager.connectors['dbpedia']
    
    # Create CAPM concept
    capm_concept = Concept(id="capm", name="CAPM", concept_type=ConceptType.MODEL)
    
    # Get search results
    print("1. Getting search results...")
    results = dbpedia_connector.search_concept('CAPM', ConceptType.MODEL)
    
    print(f"Found {len(results)} results\n")
    
    # Score each result and show the scoring breakdown
    print("2. Scoring each result:")
    scored_results = []
    
    for i, result in enumerate(results):
        print(f"\n--- Result {i+1}: {result.label} ---")
        print(f"Original confidence: {result.confidence:.3f}")
        print(f"External ID: {result.external_id}")
        print(f"Description: {result.description[:100]}...")
        
        # Calculate score
        score = dbpedia_connector._calculate_match_score(result, capm_concept)
        scored_results.append((score, result))
        
        print(f"Calculated score: {score:.3f}")
        
        # Check specific scoring factors
        label_text = (result.label or '').lower()
        description_text = (result.description or '').lower()
        
        print("Scoring factors:")
        if 'consumption-based' in label_text or 'consumption-based' in description_text:
            print("  - Has 'consumption-based' (should get -1.0 penalty)")
        if result.label.lower() == 'capital asset pricing model':
            print("  - Exact match 'capital asset pricing model' (should get +2.0 boost)")
        if '(finance)' in label_text:
            print("  - Has '(finance)' disambiguation (should get +2.5 boost)")
        
    # Sort results by score
    scored_results.sort(key=lambda x: x[0], reverse=True)
    
    print(f"\n3. Final ranking:")
    for i, (score, result) in enumerate(scored_results):
        print(f"  {i+1}. {result.label} - Score: {score:.3f}")
        
    best_match = scored_results[0][1] if scored_results else None
    if best_match:
        print(f"\n✅ Best match: {best_match.label}")
        print(f"   External ID: {best_match.external_id}")
        
        # Check if this is the standard CAPM
        if 'consumption-based' not in best_match.label.lower():
            print("   ✅ Standard CAPM selected")
        else:
            print("   ❌ Consumption-based CAPM selected (this is the problem)")
    else:
        print("\n❌ No best match found")

if __name__ == '__main__':
    debug_capm_scoring()