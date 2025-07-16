#!/usr/bin/env python3

import sys
import json
import asyncio
from pathlib import Path
sys.path.append('.')

from src.frontend.api.graph import load_knowledge_graph, enrich_concepts_with_dbpedia_old
from src.knowledge.external_ontologies import get_external_ontology_manager
from src.knowledge.concept_cache import get_concept_cache
from src.knowledge.ontology import Concept, ConceptType
from src.settings import Settings

class RobustEnrichmentSystem:
    """Systematic approach to ensure consistent DBpedia enrichment."""
    
    def __init__(self):
        self.settings = Settings()
        self.cache = get_concept_cache(self.settings)
        self.manager = get_external_ontology_manager(self.settings, self.cache)
        
        # Comprehensive mapping of concepts that SHOULD have DBpedia enrichment
        self.known_dbpedia_concepts = {
            'CAPM': 'http://dbpedia.org/resource/Capital_asset_pricing_model',
            'Correlation': 'http://dbpedia.org/resource/Pearson_correlation_coefficient', 
            'Efficient Frontier': 'http://dbpedia.org/resource/Efficient_frontier',
            'Return': 'http://dbpedia.org/resource/Rate_of_return',
            'Sharpe Ratio': 'http://dbpedia.org/resource/Sharpe_ratio',
            'Expected Return': 'http://dbpedia.org/resource/Expected_return',
            'Markowitz': 'http://dbpedia.org/resource/Harry_Markowitz',
            'Black-Scholes': 'http://dbpedia.org/resource/Black%E2%80%93Scholes_model',
            'Portfolio': 'http://dbpedia.org/resource/Portfolio_(finance)',
            'Alpha': 'http://dbpedia.org/resource/Alpha_(finance)',
            'Beta': 'http://dbpedia.org/resource/Beta_(finance)',
            'Risk': 'http://dbpedia.org/resource/Financial_risk',
            'Volatility': 'http://dbpedia.org/resource/Volatility_(finance)',
            'Diversification': 'http://dbpedia.org/resource/Diversification_(finance)',
            'Asset Allocation': 'http://dbpedia.org/resource/Asset_allocation',
            'Standard Deviation': 'http://dbpedia.org/resource/Standard_deviation',
            'Variance': 'http://dbpedia.org/resource/Variance',
            'Covariance': 'http://dbpedia.org/resource/Covariance_matrix',
            'Mean Variance': 'http://dbpedia.org/resource/Modern_portfolio_theory',
            'Optimization': 'http://dbpedia.org/resource/Mathematical_optimization'
        }
    
    def validate_current_enrichment(self):
        """Check which concepts are missing expected DBpedia enrichment."""
        print("=== VALIDATING CURRENT ENRICHMENT STATE ===\n")
        
        graph_data = load_knowledge_graph()
        concepts = graph_data.get("concepts", {})
        
        missing_enrichment = []
        incorrect_enrichment = []
        correct_enrichment = []
        
        for concept_id, concept_data in concepts.items():
            name = concept_data.get('name', '')
            if name in self.known_dbpedia_concepts:
                expected_url = self.known_dbpedia_concepts[name]
                actual_url = concept_data.get('external_id', '')
                is_enriched = concept_data.get('dbpedia_enriched', False)
                
                print(f"📋 {name}:")
                print(f"   Expected: {expected_url}")
                print(f"   Actual: {actual_url}")
                print(f"   Enriched: {is_enriched}")
                
                if not is_enriched or not actual_url:
                    missing_enrichment.append(name)
                    print("   ❌ MISSING enrichment")
                elif expected_url.split('/')[-1].lower() != actual_url.split('/')[-1].lower():
                    incorrect_enrichment.append(name) 
                    print("   ⚠️  INCORRECT enrichment")
                else:
                    correct_enrichment.append(name)
                    print("   ✅ CORRECT enrichment")
                print()
        
        print(f"SUMMARY:")
        print(f"  ✅ Correct: {len(correct_enrichment)}")
        print(f"  ⚠️  Incorrect: {len(incorrect_enrichment)}")
        print(f"  ❌ Missing: {len(missing_enrichment)}")
        
        return missing_enrichment, incorrect_enrichment, correct_enrichment
    
    async def fix_all_enrichments(self):
        """Systematically fix all enrichment issues."""
        print("\n=== FIXING ALL ENRICHMENTS SYSTEMATICALLY ===\n")
        
        # Load current data
        graph_data = load_knowledge_graph()
        concepts = graph_data.get("concepts", {})
        
        # Find concepts that need fixing
        concepts_to_fix = {}
        for concept_id, concept_data in concepts.items():
            name = concept_data.get('name', '')
            if name in self.known_dbpedia_concepts:
                concepts_to_fix[concept_id] = concept_data
        
        print(f"Found {len(concepts_to_fix)} concepts that should have DBpedia enrichment")
        
        # Clear cache for all these concepts to force fresh enrichment
        print("Clearing cache for all problematic concepts...")
        for concept_data in concepts_to_fix.values():
            name = concept_data.get('name', '')
            for connector_name in ['dbpedia', 'wikidata']:
                from src.knowledge.utils import generate_cache_key
                cache_key = generate_cache_key(f"{connector_name}Connector", name)
                if self.cache.get(cache_key):
                    self.cache.delete(cache_key)
                    print(f"  Cleared: {cache_key}")
        
        # Reset enrichment flags to force re-enrichment
        print("Resetting enrichment flags...")
        for concept_id, concept_data in concepts_to_fix.items():
            concept_data['dbpedia_enriched'] = False
            concept_data['wikidata_enriched'] = False
            concept_data['external_source'] = 'local'
            if 'external_id' in concept_data:
                del concept_data['external_id']
            print(f"  Reset: {concept_data.get('name')}")
        
        # Apply enrichment to all concepts
        print(f"\nApplying enrichment to all {len(concepts)} concepts...")
        enriched_concepts = await enrich_concepts_with_dbpedia_old(concepts, self.manager)
        
        # Validate that expected concepts got enriched correctly
        print("\nValidating enrichment results...")
        validation_results = {}
        for concept_id, concept_data in enriched_concepts.items():
            name = concept_data.get('name', '')
            if name in self.known_dbpedia_concepts:
                expected_url = self.known_dbpedia_concepts[name]
                actual_url = concept_data.get('external_id', '')
                is_enriched = concept_data.get('dbpedia_enriched', False)
                
                validation_results[name] = {
                    'expected': expected_url,
                    'actual': actual_url,
                    'enriched': is_enriched,
                    'correct': bool(actual_url and expected_url.split('/')[-1].lower() in actual_url.lower())
                }
                
                status = "✅" if validation_results[name]['correct'] else "❌"
                print(f"  {status} {name}: {actual_url}")
        
        # Save the corrected knowledge graph
        output_file = Path("./data/knowledge_graph.json")
        backup_file = Path("./data/knowledge_graph_backup_robust_fix.json")
        
        # Create backup
        if output_file.exists():
            print(f"\nCreating backup: {backup_file}")
            with open(backup_file, 'w', encoding='utf-8') as f:
                with open(output_file, 'r', encoding='utf-8') as original:
                    f.write(original.read())
        
        # Save new version
        graph_data["concepts"] = enriched_concepts
        print(f"Saving corrected knowledge graph: {output_file}")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(graph_data, f, indent=2, ensure_ascii=False)
        
        return validation_results
    
    def create_comprehensive_expansions(self):
        """Add all known concepts to financial term expansions."""
        print("=== CREATING COMPREHENSIVE FINANCIAL TERM EXPANSIONS ===\n")
        
        # This would add comprehensive search terms for all concepts
        additional_expansions = {
            'efficient frontier': ['Efficient frontier', 'Portfolio frontier', 'Markowitz frontier'],
            'markowitz': ['Harry Markowitz', 'Markowitz model', 'Portfolio theory'],
            'black-scholes': ['Black Scholes model', 'Black Scholes Merton', 'Option pricing model'],
            'alpha': ['Alpha finance', 'Jensen alpha', 'Portfolio alpha'],
            'beta': ['Beta finance', 'Beta coefficient', 'Market beta'],
            'asset allocation': ['Asset allocation', 'Portfolio allocation', 'Strategic asset allocation'],
            'optimization': ['Portfolio optimization', 'Mathematical optimization', 'Investment optimization']
        }
        
        print("Additional expansions that should be added:")
        for concept, expansions in additional_expansions.items():
            print(f"  {concept}: {expansions}")
        
        return additional_expansions

async def main():
    system = RobustEnrichmentSystem()
    
    # Step 1: Validate current state
    missing, incorrect, correct = system.validate_current_enrichment()
    
    # Step 2: Show what comprehensive expansions would look like
    system.create_comprehensive_expansions()
    
    # Step 3: Apply systematic fix
    if missing or incorrect:
        print(f"\nProceeding with systematic fix for {len(missing + incorrect)} problematic concepts...")
        results = await system.fix_all_enrichments()
        
        # Step 4: Final validation
        print(f"\n{'='*80}")
        print("FINAL VALIDATION RESULTS")
        print(f"{'='*80}")
        correct_count = sum(1 for r in results.values() if r['correct'])
        total_count = len(results)
        print(f"Successfully enriched: {correct_count}/{total_count} concepts")
        
        for name, result in results.items():
            status = "✅" if result['correct'] else "❌"
            print(f"{status} {name}")
    else:
        print("All concepts already have correct enrichment!")

if __name__ == '__main__':
    asyncio.run(main())