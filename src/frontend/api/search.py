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
from .graph import load_knowledge_graph, get_settings, get_cached_data, set_cached_data, get_dbpedia_manager
from src.knowledge.external_ontologies import ExternalOntologyManager


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


class DBpediaSearchResult(BaseModel):
    """DBpedia search result."""
    id: str
    name: str
    type: str
    description: Optional[str] = None
    uri: Optional[str] = None
    confidence: float
    source: str = "dbpedia"
    categories: List[str] = []
    aliases: List[str] = []


class CombinedSearchResponse(BaseModel):
    """Response model for combined local + DBpedia search."""
    query: str
    local_results: List[SearchResult]
    dbpedia_results: List[DBpediaSearchResult]
    total_local: int
    total_dbpedia: int
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


@router.get("/search/combined", response_model=CombinedSearchResponse)
async def search_combined(
    q: str = Query(..., min_length=1, description="Search query"),
    limit_local: int = Query(10, ge=1, le=50, description="Maximum local results"),
    limit_dbpedia: int = Query(5, ge=1, le=20, description="Maximum DBpedia results"),
    include_dbpedia: bool = Query(True, description="Include DBpedia results"),
    min_relevance: float = Query(0.1, ge=0.0, le=1.0, description="Minimum relevance score"),
    settings: Settings = Depends(get_settings),
    manager: ExternalOntologyManager = Depends(get_dbpedia_manager)
) -> Dict[str, Any]:
    """
    Combined search across local knowledge graph and DBpedia.
    
    Args:
        q: Search query string
        limit_local: Maximum local results
        limit_dbpedia: Maximum DBpedia results  
        include_dbpedia: Whether to include DBpedia search
        min_relevance: Minimum relevance score for local results
        
    Returns:
        Combined search results from both sources
    """
    import time
    start_time = time.time()
    
    # Create cache key
    cache_key = f"combined_search_{q}_{limit_local}_{limit_dbpedia}_{include_dbpedia}_{min_relevance}"
    cached_data = get_cached_data(cache_key, settings.web_cache_ttl // 4)  # Short cache for search
    
    if cached_data:
        return cached_data
    
    # Search local concepts
    local_results = []
    try:
        graph_data = load_knowledge_graph()
        concepts = graph_data.get("concepts", {})
        local_matches = search_concepts_by_name(concepts, q)
        
        # Filter by minimum relevance and limit
        local_matches = [r for r in local_matches if r["relevance_score"] >= min_relevance]
        local_matches = local_matches[:limit_local]
        
        # Ensure required fields for API response
        for result in local_matches:
            result.setdefault("name", "Unknown")
            result.setdefault("type", "unknown")
            result.setdefault("frequency", 0)
            result.setdefault("confidence", 1.0)
            result.setdefault("context", "")
            result.setdefault("source_docs", [])
        
        local_results = local_matches
        
    except Exception as e:
        logging.error(f"Local search failed: {e}")
    
    # Search DBpedia if enabled
    dbpedia_results = []
    if include_dbpedia and getattr(settings, 'enable_dbpedia', True):
        try:
            dbpedia_connector = manager.get_connector('dbpedia')
            if dbpedia_connector:
                dbpedia_matches = dbpedia_connector.search_concept(q, None)
                
                # Convert to API format
                for match in dbpedia_matches[:limit_dbpedia]:
                    dbpedia_result = DBpediaSearchResult(
                        id=match.external_id,
                        name=match.label,
                        type="dbpedia_concept",
                        description=match.description,
                        uri=match.external_id if match.external_id.startswith('http') else None,
                        confidence=match.confidence,
                        source="dbpedia",
                        categories=match.properties.get('categories', []),
                        aliases=match.aliases
                    )
                    dbpedia_results.append(dbpedia_result)
                    
        except Exception as e:
            logging.error(f"DBpedia search failed: {e}")
    
    search_time = (time.time() - start_time) * 1000  # Convert to milliseconds
    
    response_data = {
        "query": q,
        "local_results": local_results,
        "dbpedia_results": dbpedia_results,
        "total_local": len(local_results),
        "total_dbpedia": len(dbpedia_results),
        "search_time_ms": round(search_time, 2)
    }
    
    # Cache the response
    set_cached_data(cache_key, response_data)
    
    logging.info(f"Combined search for '{q}': {len(local_results)} local + {len(dbpedia_results)} DBpedia results in {search_time:.2f}ms")
    return response_data


@router.get("/search/dbpedia-only")
async def search_dbpedia_only(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results"),
    concept_type: Optional[str] = Query(None, description="Filter by concept type"),
    settings: Settings = Depends(get_settings),
    manager: ExternalOntologyManager = Depends(get_dbpedia_manager)
) -> Dict[str, Any]:
    """
    Search only in DBpedia knowledge base.
    
    Args:
        q: Search query string
        limit: Maximum number of results
        concept_type: Optional concept type filter
        
    Returns:
        DBpedia search results only
    """
    import time
    start_time = time.time()
    
    # Check if DBpedia is enabled
    if not getattr(settings, 'enable_dbpedia', True):
        raise HTTPException(status_code=503, detail="DBpedia search is disabled")
    
    # Create cache key  
    cache_key = f"dbpedia_only_search_{q}_{limit}_{concept_type}"
    cached_data = get_cached_data(cache_key, settings.web_cache_ttl // 2)
    
    if cached_data:
        return cached_data
    
    results = []
    try:
        dbpedia_connector = manager.get_connector('dbpedia')
        if not dbpedia_connector:
            raise HTTPException(status_code=503, detail="DBpedia connector not available")
        
        # Convert concept type if provided
        concept_type_enum = None
        if concept_type:
            try:
                from src.knowledge.ontology import ConceptType
                concept_type_enum = ConceptType(concept_type)
            except ValueError:
                logging.warning(f"Invalid concept type: {concept_type}")
        
        # Search DBpedia
        dbpedia_matches = dbpedia_connector.search_concept(q, concept_type_enum)
        
        # Convert to API format
        for match in dbpedia_matches[:limit]:
            result = {
                "id": match.external_id,
                "name": match.label,
                "type": "dbpedia_concept",
                "description": match.description or "",
                "uri": match.external_id if match.external_id.startswith('http') else None,
                "confidence": match.confidence,
                "source": "dbpedia",
                "categories": match.properties.get('categories', []),
                "aliases": match.aliases,
                "properties": match.properties
            }
            results.append(result)
            
    except Exception as e:
        logging.error(f"DBpedia-only search failed: {e}")
        raise HTTPException(status_code=500, detail=f"DBpedia search failed: {str(e)}")
    
    search_time = (time.time() - start_time) * 1000
    
    response_data = {
        "query": q,
        "results": results,
        "total": len(results),
        "search_time_ms": round(search_time, 2),
        "source": "dbpedia_only"
    }
    
    # Cache the response
    set_cached_data(cache_key, response_data)
    
    logging.info(f"DBpedia-only search for '{q}' returned {len(results)} results in {search_time:.2f}ms")
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
                "priority": 2,  # High priority for starts-with matches
                # Enhanced metadata (FR3.4)
                "complexity_level": concept.get("complexity_level", "intermediate"),
                "domain": concept.get("domain", "finance"),
                "has_prerequisites": len(concept.get("prerequisites", [])) > 0,
                "confidence": concept.get("confidence", 1.0)
            })
        elif query_lower in name_lower:
            suggestions.append({
                "text": name,
                "type": concept.get("type", "unknown"),
                "frequency": concept.get("frequency", 0),
                "priority": 1,  # Lower priority for contains matches
                # Enhanced metadata (FR3.4)
                "complexity_level": concept.get("complexity_level", "intermediate"),
                "domain": concept.get("domain", "finance"),
                "has_prerequisites": len(concept.get("prerequisites", [])) > 0,
                "confidence": concept.get("confidence", 1.0)
            })
    
    # Sort by priority, then frequency, then metadata richness, then alphabetically (FR3.4)
    suggestions.sort(key=lambda x: (
        -x["priority"], 
        -x["frequency"], 
        -x["confidence"],  # Higher confidence first
        -int(x["has_prerequisites"]),  # Concepts with prerequisites first
        x["text"]
    ))
    
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


@router.get("/search/combined", response_model=CombinedSearchResponse)
async def search_combined(
    q: str = Query(..., min_length=1, description="Search query"),
    limit_local: int = Query(10, ge=1, le=50, description="Maximum local results"),
    limit_dbpedia: int = Query(5, ge=1, le=20, description="Maximum DBpedia results"),
    include_dbpedia: bool = Query(True, description="Include DBpedia results"),
    min_relevance: float = Query(0.1, ge=0.0, le=1.0, description="Minimum relevance score"),
    settings: Settings = Depends(get_settings),
    manager: ExternalOntologyManager = Depends(get_dbpedia_manager)
) -> Dict[str, Any]:
    """
    Combined search across local knowledge graph and DBpedia.
    
    Args:
        q: Search query string
        limit_local: Maximum local results
        limit_dbpedia: Maximum DBpedia results  
        include_dbpedia: Whether to include DBpedia search
        min_relevance: Minimum relevance score for local results
        
    Returns:
        Combined search results from both sources
    """
    import time
    start_time = time.time()
    
    # Create cache key
    cache_key = f"combined_search_{q}_{limit_local}_{limit_dbpedia}_{include_dbpedia}_{min_relevance}"
    cached_data = get_cached_data(cache_key, settings.web_cache_ttl // 4)  # Short cache for search
    
    if cached_data:
        return cached_data
    
    # Search local concepts
    local_results = []
    try:
        graph_data = load_knowledge_graph()
        concepts = graph_data.get("concepts", {})
        local_matches = search_concepts_by_name(concepts, q)
        
        # Filter by minimum relevance and limit
        local_matches = [r for r in local_matches if r["relevance_score"] >= min_relevance]
        local_matches = local_matches[:limit_local]
        
        # Ensure required fields for API response
        for result in local_matches:
            result.setdefault("name", "Unknown")
            result.setdefault("type", "unknown")
            result.setdefault("frequency", 0)
            result.setdefault("confidence", 1.0)
            result.setdefault("context", "")
            result.setdefault("source_docs", [])
        
        local_results = local_matches
        
    except Exception as e:
        logging.error(f"Local search failed: {e}")
    
    # Search DBpedia if enabled
    dbpedia_results = []
    if include_dbpedia and getattr(settings, 'enable_dbpedia', True):
        try:
            dbpedia_connector = manager.get_connector('dbpedia')
            if dbpedia_connector:
                dbpedia_matches = dbpedia_connector.search_concept(q, None)
                
                # Convert to API format
                for match in dbpedia_matches[:limit_dbpedia]:
                    dbpedia_result = DBpediaSearchResult(
                        id=match.external_id,
                        name=match.label,
                        type="dbpedia_concept",
                        description=match.description,
                        uri=match.external_id if match.external_id.startswith('http') else None,
                        confidence=match.confidence,
                        source="dbpedia",
                        categories=match.properties.get('categories', []),
                        aliases=match.aliases
                    )
                    dbpedia_results.append(dbpedia_result)
                    
        except Exception as e:
            logging.error(f"DBpedia search failed: {e}")
    
    search_time = (time.time() - start_time) * 1000  # Convert to milliseconds
    
    response_data = {
        "query": q,
        "local_results": local_results,
        "dbpedia_results": dbpedia_results,
        "total_local": len(local_results),
        "total_dbpedia": len(dbpedia_results),
        "search_time_ms": round(search_time, 2)
    }
    
    # Cache the response
    set_cached_data(cache_key, response_data)
    
    logging.info(f"Combined search for '{q}': {len(local_results)} local + {len(dbpedia_results)} DBpedia results in {search_time:.2f}ms")
    return response_data


@router.get("/search/dbpedia-only")
async def search_dbpedia_only(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results"),
    concept_type: Optional[str] = Query(None, description="Filter by concept type"),
    settings: Settings = Depends(get_settings),
    manager: ExternalOntologyManager = Depends(get_dbpedia_manager)
) -> Dict[str, Any]:
    """
    Search only in DBpedia knowledge base.
    
    Args:
        q: Search query string
        limit: Maximum number of results
        concept_type: Optional concept type filter
        
    Returns:
        DBpedia search results only
    """
    import time
    start_time = time.time()
    
    # Check if DBpedia is enabled
    if not getattr(settings, 'enable_dbpedia', True):
        raise HTTPException(status_code=503, detail="DBpedia search is disabled")
    
    # Create cache key  
    cache_key = f"dbpedia_only_search_{q}_{limit}_{concept_type}"
    cached_data = get_cached_data(cache_key, settings.web_cache_ttl // 2)
    
    if cached_data:
        return cached_data
    
    results = []
    try:
        dbpedia_connector = manager.get_connector('dbpedia')
        if not dbpedia_connector:
            raise HTTPException(status_code=503, detail="DBpedia connector not available")
        
        # Convert concept type if provided
        concept_type_enum = None
        if concept_type:
            try:
                from src.knowledge.ontology import ConceptType
                concept_type_enum = ConceptType(concept_type)
            except ValueError:
                logging.warning(f"Invalid concept type: {concept_type}")
        
        # Search DBpedia
        dbpedia_matches = dbpedia_connector.search_concept(q, concept_type_enum)
        
        # Convert to API format
        for match in dbpedia_matches[:limit]:
            result = {
                "id": match.external_id,
                "name": match.label,
                "type": "dbpedia_concept",
                "description": match.description or "",
                "uri": match.external_id if match.external_id.startswith('http') else None,
                "confidence": match.confidence,
                "source": "dbpedia",
                "categories": match.properties.get('categories', []),
                "aliases": match.aliases,
                "properties": match.properties
            }
            results.append(result)
            
    except Exception as e:
        logging.error(f"DBpedia-only search failed: {e}")
        raise HTTPException(status_code=500, detail=f"DBpedia search failed: {str(e)}")
    
    search_time = (time.time() - start_time) * 1000
    
    response_data = {
        "query": q,
        "results": results,
        "total": len(results),
        "search_time_ms": round(search_time, 2),
        "source": "dbpedia_only"
    }
    
    # Cache the response
    set_cached_data(cache_key, response_data)
    
    logging.info(f"DBpedia-only search for '{q}' returned {len(results)} results in {search_time:.2f}ms")
    return response_data


# Enhanced search endpoints for FR3: Advanced Search and Filtering

@router.get("/search/by-complexity/{complexity_level}")
async def search_by_complexity(
    complexity_level: str,
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results"),
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """
    Search concepts by complexity level (FR3.1).
    
    Args:
        complexity_level: beginner, intermediate, or advanced
        limit: Maximum number of results
        
    Returns:
        List of concepts with the specified complexity level
    """
    valid_levels = {"beginner", "intermediate", "advanced"}
    if complexity_level.lower() not in valid_levels:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid complexity level. Must be one of: {', '.join(valid_levels)}"
        )
    
    # Check cache first
    cache_key = f"complexity_{complexity_level}_{limit}"
    cached_data = get_cached_data(cache_key, settings.web_cache_ttl)
    
    if cached_data:
        return cached_data
    
    # Load graph data
    graph_data = load_knowledge_graph()
    concepts = graph_data.get("concepts", {})
    
    results = []
    for concept_id, concept in concepts.items():
        # Check if concept has complexity level metadata
        concept_complexity = concept.get("complexity_level", "intermediate")  # Default to intermediate
        
        if concept_complexity.lower() == complexity_level.lower():
            result = concept.copy()
            result["id"] = concept_id
            result["relevance_score"] = 1.0  # Perfect complexity match
            results.append(result)
    
    # Sort by frequency and confidence
    results.sort(key=lambda x: (-x.get("frequency", 0), -x.get("confidence", 0)))
    
    # Limit results
    results = results[:limit]
    
    response_data = {
        "complexity_level": complexity_level,
        "results": results,
        "total": len(results),
        "available_levels": list(valid_levels)
    }
    
    # Cache the response
    set_cached_data(cache_key, response_data)
    
    return response_data


@router.get("/search/combined", response_model=CombinedSearchResponse)
async def search_combined(
    q: str = Query(..., min_length=1, description="Search query"),
    limit_local: int = Query(10, ge=1, le=50, description="Maximum local results"),
    limit_dbpedia: int = Query(5, ge=1, le=20, description="Maximum DBpedia results"),
    include_dbpedia: bool = Query(True, description="Include DBpedia results"),
    min_relevance: float = Query(0.1, ge=0.0, le=1.0, description="Minimum relevance score"),
    settings: Settings = Depends(get_settings),
    manager: ExternalOntologyManager = Depends(get_dbpedia_manager)
) -> Dict[str, Any]:
    """
    Combined search across local knowledge graph and DBpedia.
    
    Args:
        q: Search query string
        limit_local: Maximum local results
        limit_dbpedia: Maximum DBpedia results  
        include_dbpedia: Whether to include DBpedia search
        min_relevance: Minimum relevance score for local results
        
    Returns:
        Combined search results from both sources
    """
    import time
    start_time = time.time()
    
    # Create cache key
    cache_key = f"combined_search_{q}_{limit_local}_{limit_dbpedia}_{include_dbpedia}_{min_relevance}"
    cached_data = get_cached_data(cache_key, settings.web_cache_ttl // 4)  # Short cache for search
    
    if cached_data:
        return cached_data
    
    # Search local concepts
    local_results = []
    try:
        graph_data = load_knowledge_graph()
        concepts = graph_data.get("concepts", {})
        local_matches = search_concepts_by_name(concepts, q)
        
        # Filter by minimum relevance and limit
        local_matches = [r for r in local_matches if r["relevance_score"] >= min_relevance]
        local_matches = local_matches[:limit_local]
        
        # Ensure required fields for API response
        for result in local_matches:
            result.setdefault("name", "Unknown")
            result.setdefault("type", "unknown")
            result.setdefault("frequency", 0)
            result.setdefault("confidence", 1.0)
            result.setdefault("context", "")
            result.setdefault("source_docs", [])
        
        local_results = local_matches
        
    except Exception as e:
        logging.error(f"Local search failed: {e}")
    
    # Search DBpedia if enabled
    dbpedia_results = []
    if include_dbpedia and getattr(settings, 'enable_dbpedia', True):
        try:
            dbpedia_connector = manager.get_connector('dbpedia')
            if dbpedia_connector:
                dbpedia_matches = dbpedia_connector.search_concept(q, None)
                
                # Convert to API format
                for match in dbpedia_matches[:limit_dbpedia]:
                    dbpedia_result = DBpediaSearchResult(
                        id=match.external_id,
                        name=match.label,
                        type="dbpedia_concept",
                        description=match.description,
                        uri=match.external_id if match.external_id.startswith('http') else None,
                        confidence=match.confidence,
                        source="dbpedia",
                        categories=match.properties.get('categories', []),
                        aliases=match.aliases
                    )
                    dbpedia_results.append(dbpedia_result)
                    
        except Exception as e:
            logging.error(f"DBpedia search failed: {e}")
    
    search_time = (time.time() - start_time) * 1000  # Convert to milliseconds
    
    response_data = {
        "query": q,
        "local_results": local_results,
        "dbpedia_results": dbpedia_results,
        "total_local": len(local_results),
        "total_dbpedia": len(dbpedia_results),
        "search_time_ms": round(search_time, 2)
    }
    
    # Cache the response
    set_cached_data(cache_key, response_data)
    
    logging.info(f"Combined search for '{q}': {len(local_results)} local + {len(dbpedia_results)} DBpedia results in {search_time:.2f}ms")
    return response_data


@router.get("/search/dbpedia-only")
async def search_dbpedia_only(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results"),
    concept_type: Optional[str] = Query(None, description="Filter by concept type"),
    settings: Settings = Depends(get_settings),
    manager: ExternalOntologyManager = Depends(get_dbpedia_manager)
) -> Dict[str, Any]:
    """
    Search only in DBpedia knowledge base.
    
    Args:
        q: Search query string
        limit: Maximum number of results
        concept_type: Optional concept type filter
        
    Returns:
        DBpedia search results only
    """
    import time
    start_time = time.time()
    
    # Check if DBpedia is enabled
    if not getattr(settings, 'enable_dbpedia', True):
        raise HTTPException(status_code=503, detail="DBpedia search is disabled")
    
    # Create cache key  
    cache_key = f"dbpedia_only_search_{q}_{limit}_{concept_type}"
    cached_data = get_cached_data(cache_key, settings.web_cache_ttl // 2)
    
    if cached_data:
        return cached_data
    
    results = []
    try:
        dbpedia_connector = manager.get_connector('dbpedia')
        if not dbpedia_connector:
            raise HTTPException(status_code=503, detail="DBpedia connector not available")
        
        # Convert concept type if provided
        concept_type_enum = None
        if concept_type:
            try:
                from src.knowledge.ontology import ConceptType
                concept_type_enum = ConceptType(concept_type)
            except ValueError:
                logging.warning(f"Invalid concept type: {concept_type}")
        
        # Search DBpedia
        dbpedia_matches = dbpedia_connector.search_concept(q, concept_type_enum)
        
        # Convert to API format
        for match in dbpedia_matches[:limit]:
            result = {
                "id": match.external_id,
                "name": match.label,
                "type": "dbpedia_concept",
                "description": match.description or "",
                "uri": match.external_id if match.external_id.startswith('http') else None,
                "confidence": match.confidence,
                "source": "dbpedia",
                "categories": match.properties.get('categories', []),
                "aliases": match.aliases,
                "properties": match.properties
            }
            results.append(result)
            
    except Exception as e:
        logging.error(f"DBpedia-only search failed: {e}")
        raise HTTPException(status_code=500, detail=f"DBpedia search failed: {str(e)}")
    
    search_time = (time.time() - start_time) * 1000
    
    response_data = {
        "query": q,
        "results": results,
        "total": len(results),
        "search_time_ms": round(search_time, 2),
        "source": "dbpedia_only"
    }
    
    # Cache the response
    set_cached_data(cache_key, response_data)
    
    logging.info(f"DBpedia-only search for '{q}' returned {len(results)} results in {search_time:.2f}ms")
    return response_data


@router.get("/search/by-domain/{domain}")
async def search_by_domain(
    domain: str,
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results"),
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """
    Search concepts by domain classification (FR3.2).
    
    Args:
        domain: mathematics, finance, economics, statistics, optimization
        limit: Maximum number of results
        
    Returns:
        List of concepts in the specified domain
    """
    valid_domains = {"mathematics", "finance", "economics", "statistics", "optimization"}
    if domain.lower() not in valid_domains:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid domain. Must be one of: {', '.join(valid_domains)}"
        )
    
    # Check cache first
    cache_key = f"domain_{domain}_{limit}"
    cached_data = get_cached_data(cache_key, settings.web_cache_ttl)
    
    if cached_data:
        return cached_data
    
    # Load graph data
    graph_data = load_knowledge_graph()
    concepts = graph_data.get("concepts", {})
    
    results = []
    for concept_id, concept in concepts.items():
        # Check if concept has domain metadata
        concept_domain = concept.get("domain", "finance")  # Default to finance
        
        if concept_domain.lower() == domain.lower():
            result = concept.copy()
            result["id"] = concept_id
            result["relevance_score"] = 1.0  # Perfect domain match
            results.append(result)
    
    # Sort by frequency and confidence
    results.sort(key=lambda x: (-x.get("frequency", 0), -x.get("confidence", 0)))
    
    # Limit results
    results = results[:limit]
    
    response_data = {
        "domain": domain,
        "results": results,
        "total": len(results),
        "available_domains": list(valid_domains)
    }
    
    # Cache the response
    set_cached_data(cache_key, response_data)
    
    return response_data


@router.get("/search/combined", response_model=CombinedSearchResponse)
async def search_combined(
    q: str = Query(..., min_length=1, description="Search query"),
    limit_local: int = Query(10, ge=1, le=50, description="Maximum local results"),
    limit_dbpedia: int = Query(5, ge=1, le=20, description="Maximum DBpedia results"),
    include_dbpedia: bool = Query(True, description="Include DBpedia results"),
    min_relevance: float = Query(0.1, ge=0.0, le=1.0, description="Minimum relevance score"),
    settings: Settings = Depends(get_settings),
    manager: ExternalOntologyManager = Depends(get_dbpedia_manager)
) -> Dict[str, Any]:
    """
    Combined search across local knowledge graph and DBpedia.
    
    Args:
        q: Search query string
        limit_local: Maximum local results
        limit_dbpedia: Maximum DBpedia results  
        include_dbpedia: Whether to include DBpedia search
        min_relevance: Minimum relevance score for local results
        
    Returns:
        Combined search results from both sources
    """
    import time
    start_time = time.time()
    
    # Create cache key
    cache_key = f"combined_search_{q}_{limit_local}_{limit_dbpedia}_{include_dbpedia}_{min_relevance}"
    cached_data = get_cached_data(cache_key, settings.web_cache_ttl // 4)  # Short cache for search
    
    if cached_data:
        return cached_data
    
    # Search local concepts
    local_results = []
    try:
        graph_data = load_knowledge_graph()
        concepts = graph_data.get("concepts", {})
        local_matches = search_concepts_by_name(concepts, q)
        
        # Filter by minimum relevance and limit
        local_matches = [r for r in local_matches if r["relevance_score"] >= min_relevance]
        local_matches = local_matches[:limit_local]
        
        # Ensure required fields for API response
        for result in local_matches:
            result.setdefault("name", "Unknown")
            result.setdefault("type", "unknown")
            result.setdefault("frequency", 0)
            result.setdefault("confidence", 1.0)
            result.setdefault("context", "")
            result.setdefault("source_docs", [])
        
        local_results = local_matches
        
    except Exception as e:
        logging.error(f"Local search failed: {e}")
    
    # Search DBpedia if enabled
    dbpedia_results = []
    if include_dbpedia and getattr(settings, 'enable_dbpedia', True):
        try:
            dbpedia_connector = manager.get_connector('dbpedia')
            if dbpedia_connector:
                dbpedia_matches = dbpedia_connector.search_concept(q, None)
                
                # Convert to API format
                for match in dbpedia_matches[:limit_dbpedia]:
                    dbpedia_result = DBpediaSearchResult(
                        id=match.external_id,
                        name=match.label,
                        type="dbpedia_concept",
                        description=match.description,
                        uri=match.external_id if match.external_id.startswith('http') else None,
                        confidence=match.confidence,
                        source="dbpedia",
                        categories=match.properties.get('categories', []),
                        aliases=match.aliases
                    )
                    dbpedia_results.append(dbpedia_result)
                    
        except Exception as e:
            logging.error(f"DBpedia search failed: {e}")
    
    search_time = (time.time() - start_time) * 1000  # Convert to milliseconds
    
    response_data = {
        "query": q,
        "local_results": local_results,
        "dbpedia_results": dbpedia_results,
        "total_local": len(local_results),
        "total_dbpedia": len(dbpedia_results),
        "search_time_ms": round(search_time, 2)
    }
    
    # Cache the response
    set_cached_data(cache_key, response_data)
    
    logging.info(f"Combined search for '{q}': {len(local_results)} local + {len(dbpedia_results)} DBpedia results in {search_time:.2f}ms")
    return response_data


@router.get("/search/dbpedia-only")
async def search_dbpedia_only(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results"),
    concept_type: Optional[str] = Query(None, description="Filter by concept type"),
    settings: Settings = Depends(get_settings),
    manager: ExternalOntologyManager = Depends(get_dbpedia_manager)
) -> Dict[str, Any]:
    """
    Search only in DBpedia knowledge base.
    
    Args:
        q: Search query string
        limit: Maximum number of results
        concept_type: Optional concept type filter
        
    Returns:
        DBpedia search results only
    """
    import time
    start_time = time.time()
    
    # Check if DBpedia is enabled
    if not getattr(settings, 'enable_dbpedia', True):
        raise HTTPException(status_code=503, detail="DBpedia search is disabled")
    
    # Create cache key  
    cache_key = f"dbpedia_only_search_{q}_{limit}_{concept_type}"
    cached_data = get_cached_data(cache_key, settings.web_cache_ttl // 2)
    
    if cached_data:
        return cached_data
    
    results = []
    try:
        dbpedia_connector = manager.get_connector('dbpedia')
        if not dbpedia_connector:
            raise HTTPException(status_code=503, detail="DBpedia connector not available")
        
        # Convert concept type if provided
        concept_type_enum = None
        if concept_type:
            try:
                from src.knowledge.ontology import ConceptType
                concept_type_enum = ConceptType(concept_type)
            except ValueError:
                logging.warning(f"Invalid concept type: {concept_type}")
        
        # Search DBpedia
        dbpedia_matches = dbpedia_connector.search_concept(q, concept_type_enum)
        
        # Convert to API format
        for match in dbpedia_matches[:limit]:
            result = {
                "id": match.external_id,
                "name": match.label,
                "type": "dbpedia_concept",
                "description": match.description or "",
                "uri": match.external_id if match.external_id.startswith('http') else None,
                "confidence": match.confidence,
                "source": "dbpedia",
                "categories": match.properties.get('categories', []),
                "aliases": match.aliases,
                "properties": match.properties
            }
            results.append(result)
            
    except Exception as e:
        logging.error(f"DBpedia-only search failed: {e}")
        raise HTTPException(status_code=500, detail=f"DBpedia search failed: {str(e)}")
    
    search_time = (time.time() - start_time) * 1000
    
    response_data = {
        "query": q,
        "results": results,
        "total": len(results),
        "search_time_ms": round(search_time, 2),
        "source": "dbpedia_only"
    }
    
    # Cache the response
    set_cached_data(cache_key, response_data)
    
    logging.info(f"DBpedia-only search for '{q}' returned {len(results)} results in {search_time:.2f}ms")
    return response_data


@router.get("/search/prerequisites/{concept_id}")
async def search_prerequisites(
    concept_id: str,
    include_transitive: bool = Query(False, description="Include transitive prerequisites"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results"),
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """
    Find concepts that require specific prerequisite knowledge (FR3.3).
    
    Args:
        concept_id: ID of the prerequisite concept to search for
        include_transitive: Whether to include transitive prerequisite chains
        limit: Maximum number of results
        
    Returns:
        List of concepts that have the specified concept as a prerequisite
    """
    # Check cache first
    cache_key = f"prereqs_{concept_id}_{include_transitive}_{limit}"
    cached_data = get_cached_data(cache_key, settings.web_cache_ttl)
    
    if cached_data:
        return cached_data
    
    # Load graph data
    graph_data = load_knowledge_graph()
    concepts = graph_data.get("concepts", {})
    
    # Find the target concept name for matching
    target_concept = concepts.get(concept_id)
    if not target_concept:
        raise HTTPException(status_code=404, detail=f"Concept '{concept_id}' not found")
    
    target_name = target_concept.get("name", "").lower()
    
    results = []
    for cid, concept in concepts.items():
        if cid == concept_id:  # Skip self
            continue
            
        # Check if this concept has the target as a prerequisite
        prerequisites = concept.get("prerequisites", [])
        
        # Direct prerequisite check
        has_prerequisite = False
        for prereq in prerequisites:
            if (prereq.lower() == target_name or 
                target_name in prereq.lower() or
                prereq.lower() in target_name):
                has_prerequisite = True
                break
        
        if has_prerequisite:
            result = concept.copy()
            result["id"] = cid
            result["prerequisite_type"] = "direct"
            result["relevance_score"] = 1.0
            results.append(result)
        
        # Transitive prerequisite check (if requested)
        elif include_transitive:
            # For transitive search, check if any of this concept's prerequisites
            # have the target as their prerequisite (simple 2-level check)
            for prereq in prerequisites:
                for other_cid, other_concept in concepts.items():
                    if (other_concept.get("name", "").lower() == prereq.lower() and
                        other_cid != concept_id):
                        other_prereqs = other_concept.get("prerequisites", [])
                        for other_prereq in other_prereqs:
                            if (other_prereq.lower() == target_name or 
                                target_name in other_prereq.lower()):
                                result = concept.copy()
                                result["id"] = cid
                                result["prerequisite_type"] = "transitive"
                                result["prerequisite_path"] = [prereq, target_name]
                                result["relevance_score"] = 0.7  # Lower score for transitive
                                results.append(result)
                                break
                        if result in results:  # Break outer loop if found
                            break
    
    # Sort by prerequisite type (direct first), then by frequency
    results.sort(key=lambda x: (x["prerequisite_type"] != "direct", -x.get("frequency", 0)))
    
    # Remove duplicates and limit
    seen = set()
    unique_results = []
    for result in results:
        if result["id"] not in seen:
            seen.add(result["id"])
            unique_results.append(result)
            if len(unique_results) >= limit:
                break
    
    response_data = {
        "prerequisite_concept": {
            "id": concept_id,
            "name": target_concept.get("name", ""),
            "type": target_concept.get("type", "")
        },
        "results": unique_results,
        "total": len(unique_results),
        "includes_transitive": include_transitive
    }
    
    # Cache the response
    set_cached_data(cache_key, response_data)
    
    return response_data


@router.get("/search/combined", response_model=CombinedSearchResponse)
async def search_combined(
    q: str = Query(..., min_length=1, description="Search query"),
    limit_local: int = Query(10, ge=1, le=50, description="Maximum local results"),
    limit_dbpedia: int = Query(5, ge=1, le=20, description="Maximum DBpedia results"),
    include_dbpedia: bool = Query(True, description="Include DBpedia results"),
    min_relevance: float = Query(0.1, ge=0.0, le=1.0, description="Minimum relevance score"),
    settings: Settings = Depends(get_settings),
    manager: ExternalOntologyManager = Depends(get_dbpedia_manager)
) -> Dict[str, Any]:
    """
    Combined search across local knowledge graph and DBpedia.
    
    Args:
        q: Search query string
        limit_local: Maximum local results
        limit_dbpedia: Maximum DBpedia results  
        include_dbpedia: Whether to include DBpedia search
        min_relevance: Minimum relevance score for local results
        
    Returns:
        Combined search results from both sources
    """
    import time
    start_time = time.time()
    
    # Create cache key
    cache_key = f"combined_search_{q}_{limit_local}_{limit_dbpedia}_{include_dbpedia}_{min_relevance}"
    cached_data = get_cached_data(cache_key, settings.web_cache_ttl // 4)  # Short cache for search
    
    if cached_data:
        return cached_data
    
    # Search local concepts
    local_results = []
    try:
        graph_data = load_knowledge_graph()
        concepts = graph_data.get("concepts", {})
        local_matches = search_concepts_by_name(concepts, q)
        
        # Filter by minimum relevance and limit
        local_matches = [r for r in local_matches if r["relevance_score"] >= min_relevance]
        local_matches = local_matches[:limit_local]
        
        # Ensure required fields for API response
        for result in local_matches:
            result.setdefault("name", "Unknown")
            result.setdefault("type", "unknown")
            result.setdefault("frequency", 0)
            result.setdefault("confidence", 1.0)
            result.setdefault("context", "")
            result.setdefault("source_docs", [])
        
        local_results = local_matches
        
    except Exception as e:
        logging.error(f"Local search failed: {e}")
    
    # Search DBpedia if enabled
    dbpedia_results = []
    if include_dbpedia and getattr(settings, 'enable_dbpedia', True):
        try:
            dbpedia_connector = manager.get_connector('dbpedia')
            if dbpedia_connector:
                dbpedia_matches = dbpedia_connector.search_concept(q, None)
                
                # Convert to API format
                for match in dbpedia_matches[:limit_dbpedia]:
                    dbpedia_result = DBpediaSearchResult(
                        id=match.external_id,
                        name=match.label,
                        type="dbpedia_concept",
                        description=match.description,
                        uri=match.external_id if match.external_id.startswith('http') else None,
                        confidence=match.confidence,
                        source="dbpedia",
                        categories=match.properties.get('categories', []),
                        aliases=match.aliases
                    )
                    dbpedia_results.append(dbpedia_result)
                    
        except Exception as e:
            logging.error(f"DBpedia search failed: {e}")
    
    search_time = (time.time() - start_time) * 1000  # Convert to milliseconds
    
    response_data = {
        "query": q,
        "local_results": local_results,
        "dbpedia_results": dbpedia_results,
        "total_local": len(local_results),
        "total_dbpedia": len(dbpedia_results),
        "search_time_ms": round(search_time, 2)
    }
    
    # Cache the response
    set_cached_data(cache_key, response_data)
    
    logging.info(f"Combined search for '{q}': {len(local_results)} local + {len(dbpedia_results)} DBpedia results in {search_time:.2f}ms")
    return response_data


@router.get("/search/dbpedia-only")
async def search_dbpedia_only(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results"),
    concept_type: Optional[str] = Query(None, description="Filter by concept type"),
    settings: Settings = Depends(get_settings),
    manager: ExternalOntologyManager = Depends(get_dbpedia_manager)
) -> Dict[str, Any]:
    """
    Search only in DBpedia knowledge base.
    
    Args:
        q: Search query string
        limit: Maximum number of results
        concept_type: Optional concept type filter
        
    Returns:
        DBpedia search results only
    """
    import time
    start_time = time.time()
    
    # Check if DBpedia is enabled
    if not getattr(settings, 'enable_dbpedia', True):
        raise HTTPException(status_code=503, detail="DBpedia search is disabled")
    
    # Create cache key  
    cache_key = f"dbpedia_only_search_{q}_{limit}_{concept_type}"
    cached_data = get_cached_data(cache_key, settings.web_cache_ttl // 2)
    
    if cached_data:
        return cached_data
    
    results = []
    try:
        dbpedia_connector = manager.get_connector('dbpedia')
        if not dbpedia_connector:
            raise HTTPException(status_code=503, detail="DBpedia connector not available")
        
        # Convert concept type if provided
        concept_type_enum = None
        if concept_type:
            try:
                from src.knowledge.ontology import ConceptType
                concept_type_enum = ConceptType(concept_type)
            except ValueError:
                logging.warning(f"Invalid concept type: {concept_type}")
        
        # Search DBpedia
        dbpedia_matches = dbpedia_connector.search_concept(q, concept_type_enum)
        
        # Convert to API format
        for match in dbpedia_matches[:limit]:
            result = {
                "id": match.external_id,
                "name": match.label,
                "type": "dbpedia_concept",
                "description": match.description or "",
                "uri": match.external_id if match.external_id.startswith('http') else None,
                "confidence": match.confidence,
                "source": "dbpedia",
                "categories": match.properties.get('categories', []),
                "aliases": match.aliases,
                "properties": match.properties
            }
            results.append(result)
            
    except Exception as e:
        logging.error(f"DBpedia-only search failed: {e}")
        raise HTTPException(status_code=500, detail=f"DBpedia search failed: {str(e)}")
    
    search_time = (time.time() - start_time) * 1000
    
    response_data = {
        "query": q,
        "results": results,
        "total": len(results),
        "search_time_ms": round(search_time, 2),
        "source": "dbpedia_only"
    }
    
    # Cache the response
    set_cached_data(cache_key, response_data)
    
    logging.info(f"DBpedia-only search for '{q}' returned {len(results)} results in {search_time:.2f}ms")
    return response_data