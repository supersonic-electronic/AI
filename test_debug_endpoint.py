#!/usr/bin/env python3

import sys
sys.path.append('.')

from fastapi import FastAPI, HTTPException
from src.settings import Settings
from src.knowledge.external_ontologies import get_external_ontology_manager
from src.knowledge.concept_cache import get_concept_cache
from src.frontend.api.graph import load_knowledge_graph, enrich_concepts_with_dbpedia_old
import logging
import json

# Setup logging
logging.basicConfig(level=logging.INFO)

app = FastAPI()

@app.get("/debug/enrichment")
async def debug_enrichment():
    """Debug endpoint to test enrichment directly."""
    try:
        # Load settings
        settings = Settings()
        
        # Load concepts
        graph_data = load_knowledge_graph()
        concepts = graph_data.get("concepts", {})
        
        result = {
            "original_concept_count": len(concepts),
            "settings": {
                "dbpedia_auto_enrich": getattr(settings, 'dbpedia_auto_enrich', 'NOT_SET'),
                "enable_dbpedia": getattr(settings, 'enable_dbpedia', 'NOT_SET')
            },
            "sample_original_concepts": [],
            "enrichment_attempted": False,
            "enrichment_successful": False,
            "enriched_concept_count": 0,
            "sample_enriched_concepts": [],
            "error": None
        }
        
        # Show sample original concepts
        for i, (concept_id, concept) in enumerate(list(concepts.items())[:3]):
            result["sample_original_concepts"].append({
                "id": concept_id,
                "name": concept.get("name", "Unknown"),
                "has_dbpedia_enriched": "dbpedia_enriched" in concept,
                "dbpedia_enriched": concept.get("dbpedia_enriched", False)
            })
        
        # Try enrichment
        auto_enrich = getattr(settings, 'dbpedia_auto_enrich', True)
        enable_dbpedia = getattr(settings, 'enable_dbpedia', True)
        
        if auto_enrich and enable_dbpedia:
            result["enrichment_attempted"] = True
            
            try:
                cache = get_concept_cache(settings)
                manager = get_external_ontology_manager(settings, cache)
                enriched_concepts = await enrich_concepts_with_dbpedia_old(concepts, manager)
                
                result["enrichment_successful"] = True
                result["enriched_concept_count"] = len(enriched_concepts)
                
                # Count actually enriched concepts
                actually_enriched = sum(1 for c in enriched_concepts.values() 
                                      if c.get('dbpedia_enriched', False) or c.get('wikidata_enriched', False))
                result["actually_enriched_count"] = actually_enriched
                
                # Show sample enriched concepts
                for i, (concept_id, concept) in enumerate(list(enriched_concepts.items())[:3]):
                    result["sample_enriched_concepts"].append({
                        "id": concept_id,
                        "name": concept.get("name", "Unknown"),
                        "dbpedia_enriched": concept.get("dbpedia_enriched", False),
                        "wikidata_enriched": concept.get("wikidata_enriched", False),
                        "external_id": concept.get("external_id", "N/A"),
                        "external_source": concept.get("external_source", "N/A")
                    })
                    
            except Exception as e:
                result["error"] = str(e)
                import traceback
                result["traceback"] = traceback.format_exc()
        
        return result
        
    except Exception as e:
        return {"error": f"Failed to debug enrichment: {e}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)