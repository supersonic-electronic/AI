#!/usr/bin/env python3
"""
Test script to verify DBpedia enrichment functionality.
"""

import sys
from pathlib import Path

# Add src to Python path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.settings import get_settings
from src.knowledge.concept_cache import ConceptCache
from src.knowledge.external_ontologies import ExternalOntologyManager
from src.knowledge.ontology import Concept, ConceptType

def test_dbpedia_enrichment():
    """Test DBpedia enrichment on a sample concept."""
    print("Testing DBpedia enrichment...")
    
    # Initialize components
    settings = get_settings()
    cache = ConceptCache(settings)
    manager = ExternalOntologyManager(settings, cache)
    
    print(f"DBpedia enabled: {getattr(settings, 'enable_dbpedia', True)}")
    print(f"Available connectors: {list(manager.connectors.keys())}")
    
    # Test concept
    test_concept = Concept(
        id="test_portfolio",
        name="Portfolio",
        concept_type=ConceptType.PORTFOLIO,
        description="A collection of financial investments",
        confidence=0.8
    )
    
    print(f"\nOriginal concept: {test_concept.name}")
    print(f"Description: {test_concept.description}")
    print(f"Aliases: {list(test_concept.aliases)}")
    print(f"Properties: {test_concept.properties}")
    
    # Enrich the concept
    try:
        enriched_concept = manager.enrich_concept(test_concept)
        
        print(f"\nEnriched concept: {enriched_concept.name}")
        print(f"Description: {enriched_concept.description}")
        print(f"Aliases: {list(enriched_concept.aliases)}")
        print(f"Properties: {enriched_concept.properties}")
        
        # Check if external enrichment worked
        external_source = enriched_concept.properties.get('external_source')
        external_id = enriched_concept.properties.get('external_id')
        external_confidence = enriched_concept.properties.get('external_confidence', 0)
        
        if external_source:
            print(f"\n✓ External enrichment successful!")
            print(f"  Source: {external_source}")
            print(f"  External ID: {external_id}")
            print(f"  Confidence: {external_confidence}")
            
            if external_source == 'dbpedia':
                print(f"  🎯 DBpedia enrichment working!")
                return True
            elif external_source == 'wikidata':
                print(f"  📚 Wikidata enrichment working!")
                return True
            else:
                print(f"  ℹ️  Other external source working: {external_source}")
                return True
        else:
            print(f"\n✗ External enrichment failed - no external source found")
            return False
            
    except Exception as e:
        print(f"\n✗ DBpedia enrichment error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_dbpedia_enrichment()