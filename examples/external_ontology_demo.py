#!/usr/bin/env python3
"""
External Ontology Integration Demo

This script demonstrates how to use the external knowledge base integration
features of the AI Portfolio Optimizer system.
"""

import os
import sys
import logging
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from settings import get_settings
from knowledge.ontology import FinancialMathOntology, Concept, ConceptType
from knowledge.concept_extractor import get_concept_extractor


def setup_logging():
    """Set up logging for the demo."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def demonstrate_basic_enrichment():
    """Demonstrate basic concept enrichment with external ontologies."""
    print("=" * 80)
    print("BASIC CONCEPT ENRICHMENT DEMO")
    print("=" * 80)
    
    # Load settings
    settings = get_settings("config-with-external-ontologies.yaml")
    
    # Create ontology with external integration
    ontology = FinancialMathOntology(settings)
    
    # Create some test concepts
    test_concepts = [
        Concept(
            id="sharpe_ratio",
            name="Sharpe Ratio",
            concept_type=ConceptType.METRIC,
            description="A measure of risk-adjusted return"
        ),
        Concept(
            id="portfolio_theory",
            name="Portfolio Theory",
            concept_type=ConceptType.METHODOLOGY,
            description="Mathematical framework for portfolio optimization"
        ),
        Concept(
            id="efficient_frontier",
            name="Efficient Frontier",
            concept_type=ConceptType.METHODOLOGY,
            description="Set of optimal portfolios"
        )
    ]
    
    # Enrich concepts with external ontologies
    for concept in test_concepts:
        print(f"\nOriginal concept: {concept.name}")
        print(f"  Description: {concept.description}")
        print(f"  Aliases: {concept.aliases}")
        
        # Enrich with external ontologies
        enriched = ontology.enrich_concept_with_external_ontologies(concept)
        
        print(f"\nEnriched concept: {enriched.name}")
        print(f"  Description: {enriched.description}")
        print(f"  Aliases: {enriched.aliases}")
        print(f"  Confidence: {enriched.confidence}")
        
        # Show external properties
        if 'external_source' in enriched.properties:
            print(f"  External Source: {enriched.properties['external_source']}")
            print(f"  External ID: {enriched.properties['external_id']}")
        
        print("-" * 60)


def demonstrate_concept_extraction():
    """Demonstrate concept extraction with external enrichment."""
    print("\n" + "=" * 80)
    print("CONCEPT EXTRACTION WITH ENRICHMENT DEMO")
    print("=" * 80)
    
    # Load settings
    settings = get_settings("config-with-external-ontologies.yaml")
    
    # Create concept extractor
    extractor = get_concept_extractor(settings)
    
    # Sample text about portfolio theory
    sample_text = """
    Modern portfolio theory (MPT) is a mathematical framework for assembling 
    a portfolio of assets such that the expected return is maximized for a given 
    level of risk. The theory was introduced by Harry Markowitz in 1952.
    
    The Sharpe ratio is used to measure the performance of an investment by 
    adjusting for its risk. A higher Sharpe ratio indicates better risk-adjusted 
    performance. The efficient frontier represents the set of optimal portfolios 
    that offer the highest expected return for each level of risk.
    
    Portfolio optimization involves solving the equation:
    max μ'w - (λ/2)w'Σw
    subject to: w'1 = 1
    
    where μ is the expected return vector, w is the portfolio weights, 
    λ is the risk aversion parameter, and Σ is the covariance matrix.
    """
    
    print("Sample text:")
    print(sample_text[:200] + "...")
    
    # Extract concepts from text
    concepts, relationships = extractor.extract_concepts_from_text(
        sample_text, 
        document_name="demo.pdf", 
        page_number=1
    )
    
    print(f"\nExtracted {len(concepts)} concepts and {len(relationships)} relationships")
    
    # Show extracted concepts
    print("\nExtracted Concepts:")
    for i, concept in enumerate(concepts[:5]):  # Show first 5
        print(f"{i+1}. {concept.name} ({concept.concept_type.value})")
        print(f"   Description: {concept.description}")
        print(f"   Confidence: {concept.confidence}")
        print(f"   Extraction Method: {concept.extraction_method.value}")
        print()


def demonstrate_external_search():
    """Demonstrate direct external ontology search."""
    print("\n" + "=" * 80)
    print("EXTERNAL ONTOLOGY SEARCH DEMO")
    print("=" * 80)
    
    # Load settings
    settings = get_settings("config-with-external-ontologies.yaml")
    
    # Create ontology
    ontology = FinancialMathOntology(settings)
    
    # Search terms
    search_terms = ["portfolio optimization", "risk management", "asset allocation"]
    
    for term in search_terms:
        print(f"\nSearching for: '{term}'")
        results = ontology.search_external_ontologies(term)
        
        for source, concepts in results.items():
            print(f"\n  Results from {source}:")
            for concept in concepts[:3]:  # Show first 3 results
                print(f"    - {concept.label}")
                print(f"      {concept.description[:100]}...")
                print(f"      Confidence: {concept.confidence}")
        
        print("-" * 60)


def demonstrate_cache_statistics():
    """Demonstrate cache statistics and management."""
    print("\n" + "=" * 80)
    print("CACHE STATISTICS DEMO")
    print("=" * 80)
    
    # Load settings
    settings = get_settings("config-with-external-ontologies.yaml")
    
    # Create ontology
    ontology = FinancialMathOntology(settings)
    
    # Get cache statistics
    stats = ontology.get_external_ontology_stats()
    
    print("Cache Statistics:")
    print(f"  Total entries: {stats.get('total_entries', 'N/A')}")
    print(f"  Total size: {stats.get('total_size_bytes', 'N/A')} bytes")
    print(f"  Hit rate: {stats.get('hit_rate', 0):.2%}")
    print(f"  Total requests: {stats.get('total_requests', 'N/A')}")
    print(f"  Cache hits: {stats.get('hits', 'N/A')}")
    print(f"  Cache misses: {stats.get('misses', 'N/A')}")
    print(f"  Evictions: {stats.get('evictions', 'N/A')}")
    
    # Show source distribution
    source_dist = stats.get('source_distribution', {})
    if source_dist:
        print(f"\nSource Distribution:")
        for source, count in source_dist.items():
            print(f"  {source}: {count} entries")


def demonstrate_concept_extractor_features():
    """Demonstrate advanced concept extractor features."""
    print("\n" + "=" * 80)
    print("ADVANCED CONCEPT EXTRACTOR FEATURES DEMO")
    print("=" * 80)
    
    # Load settings
    settings = get_settings("config-with-external-ontologies.yaml")
    
    # Create concept extractor
    extractor = get_concept_extractor(settings)
    
    # Process a complete document
    document_text = """
    This paper explores modern portfolio theory and its applications in 
    quantitative finance. We examine the efficient frontier, Sharpe ratio 
    optimization, and risk-return trade-offs in portfolio construction.
    
    The fundamental equation of portfolio optimization is:
    maximize: μ'w - (λ/2)w'Σw
    subject to: w'1 = 1, w ≥ 0
    
    where μ represents expected returns, w is the weight vector, 
    λ is the risk aversion parameter, and Σ is the covariance matrix.
    """
    
    print("Processing document with external enrichment enabled...")
    
    # Process document with enrichment
    concepts, relationships = extractor.process_document(
        document_text,
        "sample_paper.pdf",
        enable_external_enrichment=True
    )
    
    print(f"\nDocument processing results:")
    print(f"  Concepts extracted: {len(concepts)}")
    print(f"  Relationships found: {len(relationships)}")
    
    # Show some enriched concepts
    print("\nTop concepts with external enrichment:")
    for concept in concepts[:3]:
        print(f"  - {concept.name} ({concept.concept_type.value})")
        print(f"    Description: {concept.description}")
        if hasattr(concept, 'properties') and 'external_source' in concept.properties:
            print(f"    External Source: {concept.properties['external_source']}")
        print()
    
    # Show extractor statistics
    stats = extractor.get_external_ontology_stats()
    print(f"Extractor cache statistics:")
    print(f"  Hit rate: {stats.get('hit_rate', 0):.2%}")
    print(f"  Total requests: {stats.get('total_requests', 0)}")


def main():
    """Main demonstration function."""
    setup_logging()
    
    print("AI Portfolio Optimizer - External Ontology Integration Demo")
    print("=" * 80)
    
    try:
        # Check if external ontologies are enabled
        settings = get_settings("config-with-external-ontologies.yaml")
        if not getattr(settings, 'enable_external_ontologies', False):
            print("⚠️  External ontologies are disabled in configuration.")
            print("   Set enable_external_ontologies: true in config to enable.")
            return
        
        print("✓ External ontologies are enabled")
        print("✓ Configuration loaded successfully")
        
        # Run demonstrations
        demonstrate_basic_enrichment()
        demonstrate_concept_extraction()
        demonstrate_external_search()
        demonstrate_cache_statistics()
        demonstrate_concept_extractor_features()
        
        print("\n" + "=" * 80)
        print("DEMO COMPLETED SUCCESSFULLY")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ Error during demonstration: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()