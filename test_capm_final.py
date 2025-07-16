#!/usr/bin/env python3

import sys
sys.path.append('.')

from src.knowledge.external_ontologies import get_external_ontology_manager
from src.knowledge.concept_cache import get_concept_cache  
from src.knowledge.ontology import Concept, ConceptType
from src.settings import Settings

def test_final():
    # Clear cache and get fresh instances
    settings = Settings()
    cache = get_concept_cache(settings)
    cache.clear('dbpedia')
    
    manager = get_external_ontology_manager(settings, cache)
    connector = manager.connectors['dbpedia']
    
    # Test by directly calling the search with debugging
    print("Testing DBpedia connector search...")
    
    # Test both search terms manually
    import time
    
    search_terms = ['CAPM', 'Capital Asset Pricing Model'] 
    
    all_results = []
    for i, search_term in enumerate(search_terms):
        print(f'\nTesting search term: {search_term}')
        
        if i > 0:
            time.sleep(0.5)
            
        params = {
            'label': search_term,
            'format': 'json',
            'maxResults': 3
        }
        
        try:
            response = connector.session.get(
                connector.lookup_endpoint, 
                params=params, 
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            print(f'Raw results: {len(data.get("docs", []))}')
            
            for item in data.get('docs', []):
                resource_list = item.get('resource', [])
                label_list = item.get('label', [search_term])
                score_list = item.get('score', ['0.0'])
                
                confidence = float(score_list[0]) / 10000.0 if score_list else 0.0
                
                # Manual ExternalConceptData creation 
                from src.knowledge.external_ontologies import ExternalConceptData
                result = ExternalConceptData(
                    external_id=resource_list[0] if resource_list else '',
                    source='dbpedia',
                    label=label_list[0] if label_list else search_term,
                    description=item.get('comment', [''])[0],
                    aliases=item.get('redirectlabel', []),
                    properties={
                        'categories': item.get('category', []),
                        'types': item.get('type', []),
                        'typeName': item.get('typeName', [])
                    },
                    confidence=confidence
                )
                
                print(f'  {result.label} - {result.confidence:.3f}')
                if 'capital' in result.label.lower() and 'asset' in result.label.lower():
                    print(f'    *** FOUND CAPM MATCH! ***')
                    
                    # Test match scoring
                    concept = Concept(id='capm', name='CAPM', concept_type=ConceptType.MODEL)
                    match_score = connector._calculate_match_score(result, concept)
                    print(f'    Match score: {match_score:.3f}')
                    print(f'    Passes threshold: {match_score >= 0.15}')
                
                all_results.append(result)
                
        except Exception as e:
            print(f'Error with {search_term}: {e}')
    
    print(f'\nTotal results collected: {len(all_results)}')

if __name__ == '__main__':
    test_final()