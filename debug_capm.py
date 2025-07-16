#!/usr/bin/env python3

import sys
import time
import requests

def test_capm_search():
    """Test CAPM search to debug the issue."""
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'AI-Knowledge-Graph/1.0 (Educational/Research Use)',
        'Accept': 'application/json'
    })
    
    lookup_endpoint = 'https://lookup.dbpedia.org/api/search'
    concept_name = 'CAPM'
    
    # Financial acronym expansion
    search_terms = [concept_name]
    financial_acronyms = {
        'capm': 'Capital Asset Pricing Model',
        'apt': 'Arbitrage Pricing Theory', 
        'var': 'Value at Risk'
    }
    
    if concept_name.lower() in financial_acronyms:
        search_terms.append(financial_acronyms[concept_name.lower()])
    
    print(f'Search terms: {search_terms}')
    
    all_results = []
    for i, search_term in enumerate(search_terms):
        print(f'\n--- Processing search term {i+1}: {search_term} ---')
        
        if i > 0:
            time.sleep(0.5)
            
        params = {
            'label': search_term,
            'format': 'json',
            'maxResults': 3
        }
        
        try:
            response = session.get(lookup_endpoint, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            print(f'Raw results for "{search_term}": {len(data.get("docs", []))}')
            
            for item in data.get('docs', []):
                resource_list = item.get('resource', [])
                label_list = item.get('label', [search_term])
                score_list = item.get('score', ['0.0'])
                
                confidence_boost = 0.1 if i > 0 and search_term != concept_name else 0.0
                confidence = (float(score_list[0]) / 10000.0 if score_list else 0.0) + confidence_boost
                
                result = {
                    'external_id': resource_list[0] if resource_list else '',
                    'label': label_list[0] if label_list else search_term,
                    'confidence': confidence
                }
                print(f'  Added: {result["label"]} - conf: {result["confidence"]:.3f}')
                all_results.append(result)
                
        except Exception as e:
            print(f'Error with {search_term}: {e}')
    
    print(f'\nTotal collected results: {len(all_results)}')
    
    # Unique results logic
    unique_results = {}
    for result in all_results:
        external_id = result['external_id']
        if external_id not in unique_results or result['confidence'] > unique_results[external_id]['confidence']:
            unique_results[external_id] = result
    
    print(f'Unique results: {len(unique_results)}')
    final_results = list(unique_results.values())[:5]
    
    print('\nFinal unique results:')
    for i, result in enumerate(final_results):
        print(f'{i+1}. {result["label"]} - {result["confidence"]:.3f}')
        print(f'   ID: {result["external_id"]}')
    
    return final_results

if __name__ == '__main__':
    test_capm_search()