#!/usr/bin/env python3
"""
Test the API endpoint to see if DBpedia enrichment shows up in graph data.
"""

import requests
import json

def test_graph_api():
    """Test the /api/graph endpoint for DBpedia data."""
    print("Testing /api/graph endpoint...")
    
    try:
        # Test the graph API endpoint
        response = requests.get('http://localhost:8000/api/graph?enrich_dbpedia=true')
        response.raise_for_status()
        
        data = response.json()
        
        print(f"Response status: {response.status_code}")
        print(f"Total nodes: {len(data.get('nodes', []))}")
        print(f"Total edges: {len(data.get('edges', []))}")
        print(f"Stats: {data.get('stats', {})}")
        
        # Check for DBpedia enriched nodes
        dbpedia_nodes = []
        enriched_nodes = []
        
        for node in data.get('nodes', []):
            node_data = node.get('data', {})
            if node_data.get('external_source') == 'dbpedia':
                dbpedia_nodes.append(node_data)
            elif node_data.get('dbpedia_enriched') == True:
                enriched_nodes.append(node_data)
        
        print(f"\nDBpedia nodes found: {len(dbpedia_nodes)}")
        print(f"DBpedia enriched nodes found: {len(enriched_nodes)}")
        
        if dbpedia_nodes:
            print("\n🎯 DBpedia nodes:")
            for node in dbpedia_nodes[:3]:  # Show first 3
                print(f"  - {node.get('name')}: {node.get('external_source')} ({node.get('dbpedia_uri', 'no URI')})")
        
        if enriched_nodes:
            print("\n📚 DBpedia enriched nodes:")
            for node in enriched_nodes[:3]:  # Show first 3
                print(f"  - {node.get('name')}: enriched={node.get('dbpedia_enriched')} (URI: {node.get('dbpedia_uri', 'none')})")
        
        return len(dbpedia_nodes) > 0 or len(enriched_nodes) > 0
        
    except requests.exceptions.ConnectionError:
        print("❌ Server not running. Start with: poetry run python main.py server")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_graph_api()