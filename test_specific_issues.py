#!/usr/bin/env python3

import sys
sys.path.append('.')
import requests
import json

def test_specific_enrichment_issues():
    """Test the specific enrichment issues reported by the user."""
    print("=== TESTING SPECIFIC ENRICHMENT ISSUES ===\n")
    
    # Test both APIs to compare
    apis_to_test = [
        ("Graph API", "http://localhost:8000/api/graph?enrich_dbpedia=true"),
        ("Concepts API", "http://localhost:8000/api/concepts")
    ]
    
    # Concepts that should have DBpedia enrichment
    expected_enriched_concepts = [
        "Rate of return",  # https://dbpedia.org/page/Rate_of_return
        "Efficient frontier",  # https://dbpedia.org/page/Efficient_frontier  
        "Sharpe ratio",  # https://dbpedia.org/page/Sharpe_ratio
        "CAPM",  # Should be displayed as CAPM not Capm
        "Correlation"  # Should not be Kendall's tau
    ]
    
    for api_name, url in apis_to_test:
        print(f"\n{'='*60}")
        print(f"TESTING {api_name}")
        print(f"{'='*60}")
        
        try:
            response = requests.get(url, timeout=30)
            if response.status_code != 200:
                print(f"❌ {api_name} failed: {response.status_code}")
                continue
                
            data = response.json()
            
            if api_name == "Graph API":
                # Graph API returns nodes
                items = data.get('nodes', [])
                concepts = {}
                for node in items:
                    node_data = node.get('data', {})
                    name = node_data.get('name', '')
                    concepts[name] = node_data
            else:
                # Concepts API returns concepts list
                items = data.get('concepts', [])
                concepts = {}
                for concept in items:
                    name = concept.get('name', '')
                    concepts[name] = concept
            
            print(f"Found {len(concepts)} concepts")
            
            # Test each expected concept
            for expected_name in expected_enriched_concepts:
                found_concept = None
                found_name = None
                
                # Look for exact match or similar match
                for name, concept_data in concepts.items():
                    if name.lower() == expected_name.lower():
                        found_concept = concept_data
                        found_name = name
                        break
                    elif expected_name.lower() in name.lower() or name.lower() in expected_name.lower():
                        found_concept = concept_data
                        found_name = name
                        break
                
                if found_concept:
                    print(f"\n📋 TESTING: {expected_name}")
                    print(f"   Found as: '{found_name}'")
                    
                    # Check enrichment status
                    has_dbpedia = found_concept.get('dbpedia_enriched', False)
                    has_wikidata = found_concept.get('wikidata_enriched', False)
                    external_id = found_concept.get('external_id', '')
                    dbpedia_uri = found_concept.get('dbpedia_uri', '')
                    description = found_concept.get('description', '')
                    
                    print(f"   DBpedia enriched: {has_dbpedia}")
                    print(f"   Wikidata enriched: {has_wikidata}")
                    print(f"   External ID: {external_id}")
                    print(f"   DBpedia URI: {dbpedia_uri}")
                    print(f"   Description: {description[:100]}...")
                    
                    # Specific issue checks
                    if expected_name == "CAPM":
                        if found_name != "CAPM":
                            print(f"   ❌ ISSUE: Displayed as '{found_name}' instead of 'CAPM'")
                        else:
                            print(f"   ✅ Correctly displayed as 'CAPM'")
                    
                    if expected_name == "Correlation":
                        if "kendall" in description.lower() and "tau" in description.lower():
                            print(f"   ❌ ISSUE: Description mentions Kendall's tau instead of correlation")
                        else:
                            print(f"   ✅ Description seems correct")
                    
                    # Check if concepts that should have DBpedia enrichment are missing it
                    if expected_name in ["Rate of return", "Efficient frontier", "Sharpe ratio"]:
                        if not has_dbpedia and not dbpedia_uri:
                            print(f"   ❌ ISSUE: Missing DBpedia enrichment (should have it)")
                        else:
                            print(f"   ✅ Has DBpedia enrichment")
                            
                else:
                    print(f"\n❌ CONCEPT NOT FOUND: {expected_name}")
        
        except Exception as e:
            print(f"❌ Error testing {api_name}: {e}")

def test_direct_enrichment_for_missing():
    """Test direct enrichment for concepts that should have DBpedia data."""
    print(f"\n{'='*80}")
    print("TESTING DIRECT ENRICHMENT FOR MISSING CONCEPTS")
    print(f"{'='*80}")
    
    from src.knowledge.external_ontologies import get_external_ontology_manager
    from src.knowledge.concept_cache import get_concept_cache
    from src.knowledge.ontology import Concept, ConceptType
    from src.settings import Settings
    
    settings = Settings()
    cache = get_concept_cache(settings)
    manager = get_external_ontology_manager(settings, cache)
    
    # Test the specific concepts that should have DBpedia data
    test_concepts = [
        Concept(id="ror", name="Rate of return", concept_type=ConceptType.PERFORMANCE_MEASURE),
        Concept(id="ef", name="Efficient frontier", concept_type=ConceptType.OPTIMIZATION), 
        Concept(id="sr", name="Sharpe ratio", concept_type=ConceptType.PERFORMANCE_MEASURE),
        Concept(id="capm2", name="CAPM", concept_type=ConceptType.MODEL),
        Concept(id="corr", name="Correlation", concept_type=ConceptType.STATISTICAL_MEASURE)
    ]
    
    for concept in test_concepts:
        print(f"\n🔍 DIRECT ENRICHMENT TEST: {concept.name}")
        try:
            enriched = manager.enrich_concept(concept)
            
            has_external = 'external_id' in enriched.properties
            external_id = enriched.properties.get('external_id', 'N/A')
            external_source = enriched.properties.get('external_source', 'N/A')
            description = enriched.description or 'N/A'
            
            print(f"   Enriched: {has_external}")
            print(f"   External ID: {external_id}")
            print(f"   Source: {external_source}")
            print(f"   Description: {description[:100]}...")
            
            if has_external:
                print("   ✅ Direct enrichment works")
                # Test if it matches expected DBpedia URL
                expected_urls = {
                    "Rate of return": "dbpedia.org/resource/Rate_of_return",
                    "Efficient frontier": "dbpedia.org/resource/Efficient_frontier", 
                    "Sharpe ratio": "dbpedia.org/resource/Sharpe_ratio"
                }
                if concept.name in expected_urls:
                    expected = expected_urls[concept.name]
                    if expected in external_id:
                        print(f"   ✅ Matches expected DBpedia URL")
                    else:
                        print(f"   ⚠️  Different DBpedia URL than expected")
            else:
                print("   ❌ Direct enrichment failed")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")

if __name__ == '__main__':
    test_specific_enrichment_issues()
    test_direct_enrichment_for_missing()