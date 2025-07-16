"""
Graph API endpoints for serving knowledge graph data.

This module provides REST API endpoints for accessing the complete
knowledge graph, including concepts and relationships.
"""

import logging
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from src.settings import Settings


# Response models
class GraphDataResponse(BaseModel):
    """Response model for graph data."""
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    stats: Dict[str, Any]


class GraphStatsResponse(BaseModel):
    """Response model for graph statistics."""
    total_concepts: int
    total_relationships: int
    concept_types: Dict[str, int]
    relationship_types: Dict[str, int]
    last_updated: Optional[str] = None


# Router instance
router = APIRouter()

# Simple in-memory cache
_cache: Dict[str, Dict[str, Any]] = {}
_cache_timestamps: Dict[str, datetime] = {}


def get_settings(request: Request) -> Settings:
    """Dependency to get settings from app state."""
    return request.app.state.settings


def get_cached_data(cache_key: str, ttl_seconds: int) -> Optional[Dict[str, Any]]:
    """Get cached data if it exists and hasn't expired."""
    if cache_key not in _cache:
        return None
    
    timestamp = _cache_timestamps.get(cache_key)
    if not timestamp:
        return None
    
    if datetime.now() - timestamp > timedelta(seconds=ttl_seconds):
        # Cache expired, remove it
        _cache.pop(cache_key, None)
        _cache_timestamps.pop(cache_key, None)
        return None
    
    return _cache[cache_key]


def set_cached_data(cache_key: str, data: Dict[str, Any]) -> None:
    """Set data in cache with current timestamp."""
    _cache[cache_key] = data
    _cache_timestamps[cache_key] = datetime.now()


def load_knowledge_graph() -> Dict[str, Any]:
    """Load knowledge graph data from JSON file."""
    try:
        graph_file = Path("./data/knowledge_graph.json")
        
        if not graph_file.exists():
            raise HTTPException(
                status_code=404, 
                detail="Knowledge graph data not found. Please run the ingestion pipeline first."
            )
        
        with open(graph_file, 'r', encoding='utf-8') as f:
            return json.load(f)
            
    except json.JSONDecodeError as e:
        logging.error(f"Failed to parse knowledge graph JSON: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Failed to parse knowledge graph data"
        )
    except Exception as e:
        logging.error(f"Failed to load knowledge graph: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Failed to load knowledge graph data"
        )


def convert_to_cytoscape_format(graph_data: Dict[str, Any]) -> Dict[str, Any]:
    """Convert knowledge graph data to Cytoscape.js format."""
    
    # Convert concepts to nodes
    nodes = []
    concepts = graph_data.get("concepts", {})
    
    for concept_id, concept in concepts.items():
        node = {
            "data": {
                "id": concept_id,
                "name": concept.get("name", "Unknown"),
                "type": concept.get("type", "unknown"),
                "frequency": concept.get("frequency", 0),
                "confidence": concept.get("confidence", 1.0),
                "context": concept.get("context", ""),
                "source_docs": concept.get("source_docs", [])
            }
        }
        nodes.append(node)
    
    # Convert relationships to edges
    edges = []
    relationships = graph_data.get("relationships", [])
    
    for i, relationship in enumerate(relationships):
        edge = {
            "data": {
                "id": f"edge_{i}",
                "source": relationship.get("source", ""),
                "target": relationship.get("target", ""),
                "type": relationship.get("type", "unknown"),
                "confidence": relationship.get("confidence", 1.0)
            }
        }
        edges.append(edge)
    
    return {"nodes": nodes, "edges": edges}


@router.get("/graph", response_model=GraphDataResponse)
async def get_graph_data(
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """
    Get the complete knowledge graph data in Cytoscape.js format.
    
    Returns:
        Complete graph data with nodes and edges
    """
    
    # Check cache first
    cache_key = "full_graph"
    cached_data = get_cached_data(cache_key, settings.web_cache_ttl)
    
    if cached_data:
        logging.debug("Returning cached graph data")
        return cached_data
    
    # Load and convert data
    graph_data = load_knowledge_graph()
    cytoscape_data = convert_to_cytoscape_format(graph_data)
    
    # Calculate statistics
    stats = {
        "total_concepts": len(cytoscape_data["nodes"]),
        "total_relationships": len(cytoscape_data["edges"]),
        "concept_types": {},
        "relationship_types": {}
    }
    
    # Count concept types
    for node in cytoscape_data["nodes"]:
        concept_type = node["data"].get("type", "unknown")
        stats["concept_types"][concept_type] = stats["concept_types"].get(concept_type, 0) + 1
    
    # Count relationship types
    for edge in cytoscape_data["edges"]:
        rel_type = edge["data"].get("type", "unknown")
        stats["relationship_types"][rel_type] = stats["relationship_types"].get(rel_type, 0) + 1
    
    response_data = {
        "nodes": cytoscape_data["nodes"],
        "edges": cytoscape_data["edges"],
        "stats": stats
    }
    
    # Cache the response
    set_cached_data(cache_key, response_data)
    
    logging.info(f"Served graph data: {stats['total_concepts']} concepts, {stats['total_relationships']} relationships")
    return response_data


@router.get("/graph/stats", response_model=GraphStatsResponse)
async def get_graph_stats(
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """
    Get statistics about the knowledge graph.
    
    Returns:
        Graph statistics including counts and types
    """
    
    # Check cache first
    cache_key = "graph_stats"
    cached_data = get_cached_data(cache_key, settings.web_cache_ttl)
    
    if cached_data:
        return cached_data
    
    # Load data and calculate stats
    graph_data = load_knowledge_graph()
    concepts = graph_data.get("concepts", {})
    relationships = graph_data.get("relationships", [])
    
    # Count concept types
    concept_types = {}
    for concept in concepts.values():
        concept_type = concept.get("type", "unknown")
        concept_types[concept_type] = concept_types.get(concept_type, 0) + 1
    
    # Count relationship types
    relationship_types = {}
    for relationship in relationships:
        rel_type = relationship.get("type", "unknown")
        relationship_types[rel_type] = relationship_types.get(rel_type, 0) + 1
    
    # Check file modification time
    graph_file = Path("./data/knowledge_graph.json")
    last_updated = None
    if graph_file.exists():
        last_updated = datetime.fromtimestamp(graph_file.stat().st_mtime).isoformat()
    
    stats_data = {
        "total_concepts": len(concepts),
        "total_relationships": len(relationships),
        "concept_types": concept_types,
        "relationship_types": relationship_types,
        "last_updated": last_updated
    }
    
    # Cache the response
    set_cached_data(cache_key, stats_data)
    
    return stats_data


@router.post("/graph/cache/clear")
async def clear_cache(
    settings: Settings = Depends(get_settings)
) -> Dict[str, str]:
    """
    Clear the graph data cache.
    
    Returns:
        Success message
    """
    
    global _cache, _cache_timestamps
    _cache.clear()
    _cache_timestamps.clear()
    
    logging.info("Graph data cache cleared")
    return {"message": "Cache cleared successfully"}