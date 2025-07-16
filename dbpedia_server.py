#!/usr/bin/env python3
"""
DBpedia Knowledge Graph Visualization Server
Serves the interactive visualization with proper API endpoints
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="DBpedia Knowledge Graph Visualization",
    description="Interactive visualization of financial concepts enriched with DBpedia",
    version="1.0.0"
)

# Mount static files
app.mount("/static", StaticFiles(directory="data"), name="static")

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main visualization page."""
    try:
        html_file = Path("data/knowledge_graph.html")
        if not html_file.exists():
            raise HTTPException(status_code=404, detail="Visualization file not found")
        
        with open(html_file, 'r') as f:
            return HTMLResponse(content=f.read())
    except Exception as e:
        logger.error(f"Error serving main page: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/visualization-data")
async def get_visualization_data():
    """Get the visualization data for the knowledge graph."""
    try:
        data_file = Path("data/visualization_data.json")
        if not data_file.exists():
            raise HTTPException(status_code=404, detail="Visualization data not found")
        
        with open(data_file, 'r') as f:
            data = json.load(f)
        
        return data
    except Exception as e:
        logger.error(f"Error loading visualization data: {e}")
        raise HTTPException(status_code=500, detail="Failed to load visualization data")

@app.get("/api/concepts")
async def get_concepts():
    """Get all concepts with their enrichment information."""
    try:
        data_file = Path("data/visualization_data.json")
        if not data_file.exists():
            raise HTTPException(status_code=404, detail="Data not found")
        
        with open(data_file, 'r') as f:
            data = json.load(f)
        
        concepts = []
        for node in data.get('nodes', []):
            concept = {
                'id': node['id'],
                'name': node['label'],
                'type': node['type'],
                'confidence': node['confidence'],
                'source': node['source'],
                'enriched': node['enriched'],
                'external_source': node.get('external_source'),
                'tooltip': node['tooltip']
            }
            concepts.append(concept)
        
        return {
            'concepts': concepts,
            'total': len(concepts),
            'enriched': len([c for c in concepts if c['enriched']]),
            'local_only': len([c for c in concepts if not c['enriched']])
        }
    except Exception as e:
        logger.error(f"Error getting concepts: {e}")
        raise HTTPException(status_code=500, detail="Failed to get concepts")

@app.get("/api/concepts/{concept_id}")
async def get_concept_detail(concept_id: str):
    """Get detailed information about a specific concept."""
    try:
        data_file = Path("data/visualization_data.json")
        if not data_file.exists():
            raise HTTPException(status_code=404, detail="Data not found")
        
        with open(data_file, 'r') as f:
            data = json.load(f)
        
        # Find the concept
        concept = None
        for node in data.get('nodes', []):
            if node['id'] == concept_id:
                concept = node
                break
        
        if not concept:
            raise HTTPException(status_code=404, detail="Concept not found")
        
        # Get related concepts
        related_concepts = []
        for edge in data.get('edges', []):
            if edge['source'] == concept_id:
                related_concepts.append({
                    'target': edge['target'],
                    'relationship': edge['type'],
                    'confidence': edge['confidence'],
                    'source_type': edge['source_type']
                })
            elif edge['target'] == concept_id:
                related_concepts.append({
                    'source': edge['source'],
                    'relationship': edge['type'],
                    'confidence': edge['confidence'],
                    'source_type': edge['source_type']
                })
        
        return {
            'concept': concept,
            'related_concepts': related_concepts,
            'relationship_count': len(related_concepts)
        }
    except Exception as e:
        logger.error(f"Error getting concept detail: {e}")
        raise HTTPException(status_code=500, detail="Failed to get concept detail")

@app.get("/api/relationships")
async def get_relationships():
    """Get all relationships in the knowledge graph."""
    try:
        data_file = Path("data/visualization_data.json")
        if not data_file.exists():
            raise HTTPException(status_code=404, detail="Data not found")
        
        with open(data_file, 'r') as f:
            data = json.load(f)
        
        relationships = data.get('edges', [])
        
        return {
            'relationships': relationships,
            'total': len(relationships),
            'dbpedia_derived': len([r for r in relationships if r.get('source_type') == 'dbpedia']),
            'locally_derived': len([r for r in relationships if r.get('source_type') == 'derived'])
        }
    except Exception as e:
        logger.error(f"Error getting relationships: {e}")
        raise HTTPException(status_code=500, detail="Failed to get relationships")

@app.get("/api/statistics")
async def get_statistics():
    """Get comprehensive statistics about the knowledge graph."""
    try:
        data_file = Path("data/visualization_data.json")
        if not data_file.exists():
            raise HTTPException(status_code=404, detail="Data not found")
        
        with open(data_file, 'r') as f:
            data = json.load(f)
        
        nodes = data.get('nodes', [])
        edges = data.get('edges', [])
        metadata = data.get('metadata', {})
        
        # Calculate detailed statistics
        stats = {
            'overview': {
                'total_concepts': len(nodes),
                'total_relationships': len(edges),
                'enriched_concepts': len([n for n in nodes if n.get('enriched')]),
                'local_concepts': len([n for n in nodes if not n.get('enriched')]),
                'dbpedia_relationships': len([e for e in edges if e.get('source_type') == 'dbpedia']),
                'derived_relationships': len([e for e in edges if e.get('source_type') == 'derived'])
            },
            'concept_types': {},
            'relationship_types': {},
            'sources': {
                'local_document': len([n for n in nodes if n.get('source') == 'local_document']),
                'dbpedia_enhanced': len([n for n in nodes if n.get('enriched')])
            },
            'metadata': metadata
        }
        
        # Count concept types
        for node in nodes:
            concept_type = node.get('type', 'unknown')
            stats['concept_types'][concept_type] = stats['concept_types'].get(concept_type, 0) + 1
        
        # Count relationship types
        for edge in edges:
            rel_type = edge.get('type', 'unknown')
            stats['relationship_types'][rel_type] = stats['relationship_types'].get(rel_type, 0) + 1
        
        return stats
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get statistics")

@app.get("/api/search")
async def search_concepts(q: str = ""):
    """Search for concepts by name, type, or description."""
    try:
        if not q:
            raise HTTPException(status_code=400, detail="Search query is required")
        
        data_file = Path("data/visualization_data.json")
        if not data_file.exists():
            raise HTTPException(status_code=404, detail="Data not found")
        
        with open(data_file, 'r') as f:
            data = json.load(f)
        
        # Search concepts
        results = []
        query_lower = q.lower()
        
        for node in data.get('nodes', []):
            # Search in name, type, and tooltip data
            if (query_lower in node.get('label', '').lower() or
                query_lower in node.get('type', '').lower() or
                query_lower in str(node.get('tooltip', {})).lower()):
                
                results.append({
                    'id': node['id'],
                    'name': node['label'],
                    'type': node['type'],
                    'confidence': node['confidence'],
                    'source': node['source'],
                    'enriched': node['enriched'],
                    'tooltip': node['tooltip']
                })
        
        return {
            'query': q,
            'results': results,
            'total_results': len(results)
        }
    except Exception as e:
        logger.error(f"Error searching concepts: {e}")
        raise HTTPException(status_code=500, detail="Failed to search concepts")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "DBpedia Knowledge Graph Visualization"}

def main():
    """Run the server."""
    logger.info("🚀 Starting DBpedia Knowledge Graph Visualization Server")
    logger.info("=" * 70)
    
    # Check if required files exist
    required_files = [
        "data/visualization_data.json",
        "data/knowledge_graph.html"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        logger.error("❌ Missing required files:")
        for file_path in missing_files:
            logger.error(f"  - {file_path}")
        logger.error("Please run the workflow first: python run_dbpedia_workflow.py")
        return
    
    logger.info("✅ All required files found")
    logger.info("🌐 Server starting on http://localhost:8080")
    logger.info("📊 API documentation available at http://localhost:8080/docs")
    logger.info("🔗 Interactive visualization at http://localhost:8080")
    
    # Run the server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8080,
        log_level="info"
    )

if __name__ == "__main__":
    main()