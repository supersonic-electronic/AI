#!/usr/bin/env python3
"""
Test script to verify the DBpedia visualization is working correctly
"""

import requests
import json
from pathlib import Path

def test_server_health():
    """Test if the server is healthy and responding."""
    try:
        response = requests.get("http://localhost:8080/health")
        if response.status_code == 200:
            print("✅ Server is healthy and responding")
            return True
        else:
            print(f"❌ Server health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        return False

def test_visualization_data():
    """Test if the visualization data endpoint is working."""
    try:
        response = requests.get("http://localhost:8080/api/visualization-data")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Visualization data loaded successfully")
            print(f"  - Nodes: {len(data.get('nodes', []))}")
            print(f"  - Edges: {len(data.get('edges', []))}")
            print(f"  - Metadata: {data.get('metadata', {})}")
            return True
        else:
            print(f"❌ Visualization data endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error fetching visualization data: {e}")
        return False

def test_html_page():
    """Test if the HTML page is served correctly."""
    try:
        response = requests.get("http://localhost:8080/")
        if response.status_code == 200:
            html_content = response.text
            if "DBpedia Knowledge Graph" in html_content:
                print("✅ HTML page served correctly")
                if "console.log" in html_content:
                    print("✅ Debug logging is enabled")
                if "d3.v7.min.js" in html_content:
                    print("✅ D3.js library is included")
                return True
            else:
                print("❌ HTML page content is incorrect")
                return False
        else:
            print(f"❌ HTML page request failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error fetching HTML page: {e}")
        return False

def test_api_endpoints():
    """Test various API endpoints."""
    endpoints = [
        "/api/concepts",
        "/api/relationships", 
        "/api/statistics",
        "/api/search?q=portfolio"
    ]
    
    all_passed = True
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"http://localhost:8080{endpoint}")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ {endpoint} - OK")
            else:
                print(f"❌ {endpoint} - Failed ({response.status_code})")
                all_passed = False
        except Exception as e:
            print(f"❌ {endpoint} - Error: {e}")
            all_passed = False
    
    return all_passed

def verify_source_labeling():
    """Verify that source labeling is working correctly."""
    try:
        response = requests.get("http://localhost:8080/api/concepts")
        if response.status_code == 200:
            data = response.json()
            concepts = data.get('concepts', [])
            
            print(f"✅ Source labeling verification:")
            for concept in concepts:
                name = concept.get('name', 'Unknown')
                enriched = concept.get('enriched', False)
                source = concept.get('source', 'Unknown')
                external_source = concept.get('external_source', 'None')
                
                print(f"  - {name}:")
                print(f"    Source: {source}")
                print(f"    Enriched: {enriched}")
                print(f"    External Source: {external_source}")
                
                # Check tooltip data
                tooltip = concept.get('tooltip', {})
                if enriched and tooltip.get('dbpedia_uri'):
                    print(f"    DBpedia URI: {tooltip['dbpedia_uri']}")
                if tooltip.get('document'):
                    print(f"    Document: {tooltip['document']}")
                print()
            
            return True
        else:
            print(f"❌ Failed to verify source labeling: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error verifying source labeling: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Testing DBpedia Knowledge Graph Visualization")
    print("=" * 60)
    
    tests = [
        ("Server Health", test_server_health),
        ("Visualization Data", test_visualization_data),
        ("HTML Page", test_html_page),
        ("API Endpoints", test_api_endpoints),
        ("Source Labeling", verify_source_labeling)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Testing {test_name}...")
        print("-" * 40)
        
        if test_func():
            passed += 1
            print(f"✅ {test_name} - PASSED")
        else:
            print(f"❌ {test_name} - FAILED")
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The visualization should be working correctly.")
        print("🌐 Visit http://localhost:8080 to view the interactive knowledge graph")
        print("💡 Open browser developer tools to see debug logs")
    else:
        print(f"⚠️  {total - passed} tests failed. Please check the issues above.")
    
    return passed == total

if __name__ == "__main__":
    main()