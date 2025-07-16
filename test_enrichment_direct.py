#!/usr/bin/env python3

import sys
sys.path.append('.')
import requests
import json

def test_direct_enrichment():
    """Test enrichment by calling a simple test endpoint."""
    print("Testing direct enrichment through API...")
    
    # Test the graph API which we know works
    print("\n1. Testing Graph API (known to work):")
    response = requests.get("http://localhost:8000/api/graph?enrich_dbpedia=true")
    if response.status_code == 200:
        data = response.json()
        nodes = data.get('nodes', [])
        enriched = sum(1 for node in nodes if node.get('data', {}).get('dbpedia_enriched', False))
        print(f"   Graph API: {enriched}/{len(nodes)} nodes enriched")
        
        # Show a sample enriched node
        for node in nodes:
            if node.get('data', {}).get('dbpedia_enriched', False):
                name = node.get('data', {}).get('name', 'Unknown')
                external_id = node.get('data', {}).get('external_id', 'N/A')
                print(f"   Sample: {name} -> {external_id}")
                break
    else:
        print(f"   Graph API failed: {response.status_code}")
    
    print("\n2. Testing Concepts API (should now work):")
    # Clear cache first by adding a unique parameter
    import time
    timestamp = int(time.time())
    response = requests.get(f"http://localhost:8000/api/concepts?page=1&per_page=5&_t={timestamp}")
    if response.status_code == 200:
        data = response.json()
        concepts = data.get('concepts', [])
        enriched = sum(1 for concept in concepts if concept.get('dbpedia_enriched', False))
        print(f"   Concepts API: {enriched}/{len(concepts)} concepts enriched")
        
        # Show details of first few concepts
        for concept in concepts[:3]:
            name = concept.get('name', 'Unknown')
            dbpedia = concept.get('dbpedia_enriched', False)
            external_id = concept.get('external_id', 'N/A')
            print(f"   {name}: DBpedia={dbpedia}, External={external_id}")
    else:
        print(f"   Concepts API failed: {response.status_code}")
        print(f"   Response: {response.text[:200]}")

if __name__ == '__main__':
    test_direct_enrichment()