#!/usr/bin/env python3

import sys
sys.path.append('.')

from src.knowledge.external_ontologies import get_external_ontology_manager
from src.knowledge.concept_cache import get_concept_cache
from src.knowledge.ontology import Concept, ConceptType
from src.settings import Settings

def test_actual_enrichment():
    """Test if enrichment is actually working by checking concept properties."""
    print("=== TESTING ACTUAL ENRICHMENT ===\n")
    
    settings = Settings()
    cache = get_concept_cache(settings)
    manager = get_external_ontology_manager(settings, cache)
    
    # Test concepts that should definitely be enrichable
    test_concepts = [
        Concept(id="portfolio", name="Portfolio", concept_type=ConceptType.INVESTMENT_VEHICLE),
        Concept(id="capm", name="CAPM", concept_type=ConceptType.MODEL),
        Concept(id="beta", name="Beta", concept_type=ConceptType.RISK_MEASURE),
        Concept(id="alpha", name="Alpha", concept_type=ConceptType.PERFORMANCE_MEASURE),
        Concept(id="variance", name="Variance", concept_type=ConceptType.STATISTICAL_MEASURE)
    ]
    
    for concept in test_concepts:
        print(f"\n{'='*60}")
        print(f"TESTING: {concept.name}")
        print(f"{'='*60}")
        
        # Clear any existing enrichment
        original_properties = concept.properties.copy()
        concept.properties = {}
        
        try:
            enriched_concept = manager.enrich_concept(concept)
            
            # Check if enrichment was applied by looking at properties
            has_external_id = 'external_id' in enriched_concept.properties
            has_external_source = 'external_source' in enriched_concept.properties
            has_external_confidence = 'external_confidence' in enriched_concept.properties
            
            print(f"Has external_id: {has_external_id}")
            print(f"Has external_source: {has_external_source}")
            print(f"Has external_confidence: {has_external_confidence}")
            
            if has_external_id or has_external_source:
                print("✓ ENRICHMENT APPLIED")
                print(f"External ID: {enriched_concept.properties.get('external_id', 'N/A')}")
                print(f"External Source: {enriched_concept.properties.get('external_source', 'N/A')}")
                print(f"External Confidence: {enriched_concept.properties.get('external_confidence', 'N/A')}")
                print(f"Description: {enriched_concept.description[:100] if enriched_concept.description else 'N/A'}...")
                print(f"Aliases: {list(enriched_concept.aliases)[:5]}")  # First 5 aliases
                
                # Check for categories
                categories = enriched_concept.properties.get('categories', [])
                if categories:
                    print(f"Categories: {categories[:3]}")  # First 3 categories
                    
            else:
                print("✗ NO ENRICHMENT APPLIED")
                print("Checking why...")
                
                # Manually test connectors
                for connector_name, connector in manager.connectors.items():
                    print(f"\n  Testing {connector_name}:")
                    try:
                        results = connector.search_concept(concept.name, concept.concept_type)
                        if results:
                            best = connector._find_best_match(results, concept)
                            if best:
                                score = connector._calculate_match_score(best, concept)
                                print(f"    Best match: {best.label}")
                                print(f"    Raw confidence: {best.confidence:.3f}")
                                print(f"    Calculated score: {score:.3f}")
                                print(f"    Threshold: 0.12")
                                print(f"    Passes threshold: {score >= 0.12}")
                            else:
                                print(f"    No best match found")
                        else:
                            print(f"    No search results")
                    except Exception as e:
                        print(f"    Error: {e}")
            
        except Exception as e:
            print(f"✗ ERROR: {e}")
            import traceback
            traceback.print_exc()

def test_api_enrichment():
    """Test enrichment through the API to see what's returned to frontend."""
    print(f"\n{'='*80}")
    print("TESTING API ENRICHMENT")
    print(f"{'='*80}")
    
    import requests
    try:
        # Get concepts from API
        response = requests.get("http://localhost:8000/api/concepts")
        if response.status_code == 200:
            data = response.json()
            concepts = data.get('concepts', [])
            
            print(f"Found {len(concepts)} concepts from API")
            
            # Check first few for enrichment
            for i, concept in enumerate(concepts[:5]):
                name = concept.get('name', 'Unknown')
                external_links = concept.get('external_links', {})
                has_external = bool(external_links)
                
                print(f"{i+1}. {name}: External links = {has_external}")
                if has_external:
                    print(f"   External links: {external_links}")
        else:
            print(f"API request failed: {response.status_code}")
            
    except Exception as e:
        print(f"Error testing API: {e}")

if __name__ == '__main__':
    test_actual_enrichment()
    test_api_enrichment()