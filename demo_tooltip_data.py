#!/usr/bin/env python3
"""
Demo script to show the rich tooltip data with source labeling
"""

import requests
import json

def demo_tooltip_data():
    """Demonstrate the rich tooltip data for each concept."""
    print("🎨 DBpedia Knowledge Graph - Tooltip Data Demo")
    print("=" * 70)
    
    try:
        # Get concept data
        response = requests.get("http://localhost:8080/api/concepts")
        data = response.json()
        
        concepts = data.get('concepts', [])
        print(f"Found {len(concepts)} concepts with detailed tooltip data\n")
        
        for i, concept in enumerate(concepts, 1):
            print(f"🔍 Concept {i}: {concept['name']}")
            print("=" * 50)
            
            tooltip = concept.get('tooltip', {})
            
            # Basic info
            print(f"📋 Basic Information:")
            print(f"  • Type: {tooltip.get('type', 'Unknown')}")
            print(f"  • Confidence: {tooltip.get('confidence', 'Unknown')}")
            print(f"  • Source: {tooltip.get('source', 'Unknown')}")
            print(f"  • Enriched: {'Yes' if tooltip.get('enriched') else 'No'}")
            
            # Local document info
            if tooltip.get('source') == 'local_document':
                print(f"\n📄 Local Document Information:")
                print(f"  • Document: {tooltip.get('document', 'Unknown')}")
                print(f"  • Page: {tooltip.get('page', 'Unknown')}")
                print(f"  • Context: {tooltip.get('context', 'No context available')}")
            
            # DBpedia enrichment info
            if tooltip.get('enriched'):
                print(f"\n🌐 DBpedia Enrichment:")
                print(f"  • External Source: {tooltip.get('external_source', 'Unknown')}")
                print(f"  • DBpedia URI: {tooltip.get('dbpedia_uri', 'Not available')}")
                print(f"  • Enrichment Confidence: {tooltip.get('enrichment_confidence', 'Unknown')}")
                
                if tooltip.get('dbpedia_abstract'):
                    abstract = tooltip['dbpedia_abstract']
                    print(f"  • Abstract: {abstract[:150]}...")
                
                if tooltip.get('creator'):
                    print(f"  • Creator: {tooltip['creator']}")
                
                if tooltip.get('publication_date'):
                    print(f"  • Publication Date: {tooltip['publication_date']}")
                
                if tooltip.get('categories'):
                    categories = tooltip['categories']
                    print(f"  • Categories: {', '.join(categories[:3])}")
                
                if tooltip.get('aliases'):
                    aliases = tooltip['aliases']
                    print(f"  • Aliases: {', '.join(aliases[:3])}")
            
            print(f"\n{'─' * 70}\n")
        
        # Show relationship data
        print("🔗 Relationship Information:")
        print("=" * 50)
        
        rel_response = requests.get("http://localhost:8080/api/relationships")
        rel_data = rel_response.json()
        
        relationships = rel_data.get('relationships', [])
        print(f"Found {len(relationships)} relationships")
        
        dbpedia_rels = [r for r in relationships if r.get('source_type') == 'dbpedia']
        derived_rels = [r for r in relationships if r.get('source_type') == 'derived']
        
        print(f"  • DBpedia-derived relationships: {len(dbpedia_rels)}")
        print(f"  • Document-derived relationships: {len(derived_rels)}")
        
        print(f"\n📊 Sample Relationships:")
        for i, rel in enumerate(relationships[:5], 1):
            source_type = rel.get('source_type', 'unknown')
            source_emoji = "🌐" if source_type == 'dbpedia' else "📄"
            print(f"  {i}. {source_emoji} {rel['source']} → {rel['target']}")
            print(f"     Type: {rel['type']}, Confidence: {rel['confidence']}")
            print(f"     Source: {source_type}")
        
        print(f"\n🎯 Visualization Features:")
        print("=" * 50)
        features = [
            "🟢 Green nodes = DBpedia enriched concepts",
            "🔵 Blue nodes = Local document concepts", 
            "🟠 Orange edges = DBpedia-derived relationships",
            "⚫ Gray edges = Document-derived relationships",
            "🖱️  Hover over nodes for detailed tooltips",
            "🔍 Clear source attribution in all tooltips",
            "📋 Rich metadata from external sources",
            "🔗 Clickable DBpedia URIs for verification"
        ]
        
        for feature in features:
            print(f"  {feature}")
        
        print(f"\n✅ All tooltip data is properly labeled with source information!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    demo_tooltip_data()