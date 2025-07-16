#!/usr/bin/env python3
"""
Simple test of DBpedia Lookup API to debug response format.
"""

import requests
import json

def test_dbpedia_lookup():
    """Test DBpedia Lookup API directly."""
    url = "https://lookup.dbpedia.org/api/search"
    params = {
        'label': 'Portfolio',
        'format': 'json',
        'maxResults': 3
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        data = response.json()
        print(f"Response data type: {type(data)}")
        print(f"Response data: {json.dumps(data, indent=2)}")
        
        return data
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    test_dbpedia_lookup()