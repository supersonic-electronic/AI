"""
Search API endpoints for finding concepts and relationships.

This module provides REST API endpoints for searching through the
knowledge graph data using various criteria.
"""

import logging
import re
from typing import Dict, List, Any, Optional

from fastapi import APIRouter, HTTPException, Depends, Request, Query
from pydantic import BaseModel

from src.settings import Settings
from .graph import load_knowledge_graph, get_settings, get_cached_data, set_cached_data


# Response models
class SearchResult(BaseModel):
    """Individual search result."""
    id: str
    name: str
    type: str
    frequency: int
    confidence: float
    context: str
    source_docs: List[str]
    relevance_score: float


class SearchResponse(BaseModel):
    """Response model for search results."""
    query: str
    results: List[SearchResult]
    total: int
    search_time_ms: float


# Router instance
router = APIRouter()


def calculate_relevance_score(concept: Dict[str, Any], query: str) -> float:
    """
    Calculate relevance score for a concept based on search query.
    
    Args:
        concept: Concept data
        query: Search query
        
    Returns:
        Relevance score between 0 and 1
    """
    score = 0.0
    query_lower = query.lower()
    
    name = concept.get("name", "").lower()
    context = concept.get("context", "").lower()
    concept_type = concept.get("type", "").lower()
    
    # Exact name match gets highest score
    if query_lower == name:
        score += 1.0
    # Name contains query
    elif query_lower in name:
        score += 0.8
    # Query contains name (for partial matches)
    elif name in query_lower:
        score += 0.6
    
    # Context contains query
    if query_lower in context:
        score += 0.3
    
    # Type contains query
    if query_lower in concept_type:
        score += 0.2
    
    # Boost score based on frequency (normalized)
    frequency = concept.get("frequency", 0)
    if frequency > 0:
        # Normalize frequency contribution (max boost of 0.2)
        frequency_boost = min(0.2, frequency / 10000.0)
        score += frequency_boost
    
    # Boost score based on confidence
    confidence = concept.get("confidence", 1.0)
    score += confidence * 0.1
    
    return min(score, 1.0)  # Cap at 1.0


def search_concepts_by_name(concepts: Dict[str, Any], query: str) -> List[Dict[str, Any]]:
    """
    Search concepts by name using fuzzy matching.
    
    Args:
        concepts: Dictionary of concepts
        query: Search query
        
    Returns:
        List of matching concepts with relevance scores
    """
    results = []
    query_lower = query.lower()
    
    for concept_id, concept in concepts.items():
        relevance_score = calculate_relevance_score(concept, query)
        
        # Only include results with some relevance
        if relevance_score > 0:
            result = concept.copy()
            result["id"] = concept_id
            result["relevance_score"] = relevance_score
            results.append(result)
    
    # Sort by relevance score (descending) then by frequency
    results.sort(key=lambda x: (-x["relevance_score"], -x.get("frequency", 0)))
    
    return results


def search_concepts_by_type(concepts: Dict[str, Any], concept_type: str) -> List[Dict[str, Any]]:
    """
    Search concepts by type.
    
    Args:
        concepts: Dictionary of concepts
        concept_type: Type to search for
        
    Returns:
        List of matching concepts
    """
    results = []
    type_lower = concept_type.lower()
    
    for concept_id, concept in concepts.items():
        if concept.get("type", "").lower() == type_lower:
            result = concept.copy()
            result["id"] = concept_id
            result["relevance_score"] = 1.0  # Perfect type match
            results.append(result)
    
    # Sort by frequency
    results.sort(key=lambda x: -x.get("frequency", 0))
    
    return results


@router.get("/search", response_model=SearchResponse)
async def search_concepts(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results"),
    concept_type: Optional[str] = Query(None, description="Filter by concept type"),
    min_relevance: float = Query(0.1, ge=0.0, le=1.0, description="Minimum relevance score"),
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """
    Search for concepts in the knowledge graph.
    
    Args:
        q: Search query string
        limit: Maximum number of results to return
        concept_type: Optional filter by concept type
        min_relevance: Minimum relevance score for results
        
    Returns:
        Search results with relevance scores
    """
    import time
    start_time = time.time()
    
    # Create cache key
    cache_key = f"search_{q}_{limit}_{concept_type}_{min_relevance}"
    cached_data = get_cached_data(cache_key, settings.web_cache_ttl // 2)  # Shorter cache for search
    
    if cached_data:
        return cached_data
    
    # Load graph data
    graph_data = load_knowledge_graph()
    concepts = graph_data.get("concepts", {})
    
    # Filter by type first if specified
    if concept_type:
        filtered_concepts = {
            cid: concept for cid, concept in concepts.items()
            if concept.get("type", "").lower() == concept_type.lower()
        }
    else:
        filtered_concepts = concepts
    
    # Search concepts
    results = search_concepts_by_name(filtered_concepts, q)
    
    # Filter by minimum relevance
    results = [r for r in results if r["relevance_score"] >= min_relevance]
    
    # Limit results
    results = results[:limit]
    
    # Ensure required fields
    for result in results:
        result.setdefault("name", "Unknown")
        result.setdefault("type", "unknown")
        result.setdefault("frequency", 0)
        result.setdefault("confidence", 1.0)
        result.setdefault("context", "")
        result.setdefault("source_docs", [])
    
    search_time = (time.time() - start_time) * 1000  # Convert to milliseconds
    
    response_data = {
        "query": q,
        "results": results,
        "total": len(results),
        "search_time_ms": round(search_time, 2)
    }
    
    # Cache the response
    set_cached_data(cache_key, response_data)
    
    logging.info(f"Search for '{q}' returned {len(results)} results in {search_time:.2f}ms")
    return response_data


@router.get("/search/types")
async def get_concept_types(
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """
    Get all available concept types for filtering.
    
    Returns:
        List of concept types with counts
    """
    
    # Check cache first
    cache_key = "concept_types"
    cached_data = get_cached_data(cache_key, settings.web_cache_ttl)
    
    if cached_data:
        return cached_data
    
    # Load graph data
    graph_data = load_knowledge_graph()
    concepts = graph_data.get("concepts", {})
    
    # Count concept types
    type_counts = {}
    for concept in concepts.values():
        concept_type = concept.get("type", "unknown")
        type_counts[concept_type] = type_counts.get(concept_type, 0) + 1
    
    # Convert to list of objects and sort by count
    types_list = [
        {"type": type_name, "count": count}
        for type_name, count in type_counts.items()
    ]
    types_list.sort(key=lambda x: -x["count"])
    
    response_data = {
        "types": types_list,
        "total": len(types_list)
    }
    
    # Cache the response
    set_cached_data(cache_key, response_data)
    
    return response_data


@router.get("/search/suggestions")
async def get_search_suggestions(
    q: str = Query(..., min_length=1, description="Partial query for suggestions"),
    limit: int = Query(10, ge=1, le=20, description="Maximum number of suggestions"),
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """
    Get search suggestions based on partial query.
    
    Args:
        q: Partial search query
        limit: Maximum number of suggestions
        
    Returns:
        List of suggested concept names
    """
    
    # Check cache first
    cache_key = f"suggestions_{q}_{limit}"
    cached_data = get_cached_data(cache_key, settings.web_cache_ttl // 4)  # Very short cache
    
    if cached_data:
        return cached_data
    
    # Load graph data
    graph_data = load_knowledge_graph()
    concepts = graph_data.get("concepts", {})
    
    suggestions = []
    query_lower = q.lower()
    
    # Find concepts that start with or contain the query
    for concept_id, concept in concepts.items():
        name = concept.get("name", "")
        name_lower = name.lower()
        
        # Prioritize names that start with the query
        if name_lower.startswith(query_lower):
            suggestions.append({
                "text": name,
                "type": concept.get("type", "unknown"),
                "frequency": concept.get("frequency", 0),
                "priority": 2  # High priority for starts-with matches
            })
        elif query_lower in name_lower:
            suggestions.append({
                "text": name,
                "type": concept.get("type", "unknown"),
                "frequency": concept.get("frequency", 0),
                "priority": 1  # Lower priority for contains matches
            })
    
    # Sort by priority, then frequency, then alphabetically
    suggestions.sort(key=lambda x: (-x["priority"], -x["frequency"], x["text"]))
    
    # Remove duplicates and limit
    seen = set()
    unique_suggestions = []
    for suggestion in suggestions:
        if suggestion["text"] not in seen:
            seen.add(suggestion["text"])
            unique_suggestions.append(suggestion)
            if len(unique_suggestions) >= limit:
                break
    
    response_data = {
        "query": q,
        "suggestions": unique_suggestions,
        "total": len(unique_suggestions)
    }
    
    # Cache the response
    set_cached_data(cache_key, response_data)
    
    return response_data