"""
Concepts API endpoints for individual concept operations.

This module provides REST API endpoints for accessing individual concepts,
their details, and related information.
"""

import logging
import json
from pathlib import Path
from typing import Dict, List, Any, Optional

from fastapi import APIRouter, HTTPException, Depends, Request, Query
from pydantic import BaseModel

from src.settings import Settings
from src.knowledge.external_ontologies import get_external_ontology_manager
from src.knowledge.concept_cache import get_concept_cache
from .graph import load_knowledge_graph, get_settings, get_cached_data, set_cached_data, enrich_concepts_with_dbpedia_old


# Response models
class ConceptResponse(BaseModel):
    """Response model for individual concept data."""
    id: str
    name: str
    type: str
    frequency: int
    confidence: float
    context: str
    source_docs: List[str]
    
    # Enhanced metadata fields
    description: Optional[str] = None
    definition: Optional[str] = None
    notation: Optional[str] = None
    latex: Optional[str] = None
    examples: List[str] = []
    related_formulas: List[str] = []
    applications: List[str] = []
    prerequisites: List[str] = []
    complexity_level: Optional[str] = None
    domain: Optional[str] = None
    keywords: List[str] = []
    external_links: Dict[str, str] = {}
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    # External enrichment fields
    external_id: Optional[str] = None
    dbpedia_enriched: Optional[bool] = None
    wikidata_enriched: Optional[bool] = None
    dbpedia_uri: Optional[str] = None
    external_source: Optional[str] = None


class ConceptNeighborsResponse(BaseModel):
    """Response model for concept neighbors."""
    concept: ConceptResponse
    neighbors: List[Dict[str, Any]]
    relationships: List[Dict[str, Any]]


class ConceptListResponse(BaseModel):
    """Response model for concept list."""
    concepts: List[ConceptResponse]
    total: int
    page: int
    per_page: int


# Router instance
router = APIRouter()


def find_concept_by_id(graph_data: Dict[str, Any], concept_id: str) -> Optional[Dict[str, Any]]:
    """Find a concept by ID in the graph data."""
    concepts = graph_data.get("concepts", {})
    return concepts.get(concept_id)


def get_concept_relationships(graph_data: Dict[str, Any], concept_id: str) -> List[Dict[str, Any]]:
    """Get all relationships for a specific concept."""
    relationships = graph_data.get("relationships", [])
    concept_relationships = []
    
    for relationship in relationships:
        if relationship.get("source") == concept_id or relationship.get("target") == concept_id:
            concept_relationships.append(relationship)
    
    return concept_relationships


def get_related_concepts(graph_data: Dict[str, Any], concept_id: str) -> List[Dict[str, Any]]:
    """Get all concepts related to a specific concept."""
    concepts = graph_data.get("concepts", {})
    relationships = get_concept_relationships(graph_data, concept_id)
    
    related_concepts = []
    for relationship in relationships:
        # Find the other concept in the relationship
        if relationship.get("source") == concept_id:
            related_id = relationship.get("target")
        else:
            related_id = relationship.get("source")
        
        if related_id and related_id in concepts:
            related_concept = concepts[related_id].copy()
            related_concept["id"] = related_id
            related_concept["relationship"] = relationship
            related_concepts.append(related_concept)
    
    return related_concepts


@router.get("/concepts", response_model=ConceptListResponse)
async def get_concepts(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    concept_type: Optional[str] = Query(None, description="Filter by concept type"),
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """
    Get a paginated list of concepts.
    
    Args:
        page: Page number (1-based)
        per_page: Number of items per page
        concept_type: Optional filter by concept type
        
    Returns:
        Paginated list of concepts
    """
    
    # Create cache key based on parameters  
    cache_key = f"concepts_page_{page}_per_{per_page}_type_{concept_type}"
    
    # DISABLE CACHE to ensure enrichment is applied
    cached_data = None  # Force no cache
    if cached_data:
        return cached_data
    
    # Load graph data
    graph_data = load_knowledge_graph()
    concepts = graph_data.get("concepts", {})
    
    # Apply enrichment if enabled
    auto_enrich = getattr(settings, 'dbpedia_auto_enrich', True)
    enable_dbpedia = getattr(settings, 'enable_dbpedia', True)
    logging.info(f"Concepts API enrichment check: auto_enrich={auto_enrich}, enable_dbpedia={enable_dbpedia}")
    print(f"DEBUG: Concepts API enrichment check: auto_enrich={auto_enrich}, enable_dbpedia={enable_dbpedia}")
    
    if auto_enrich and enable_dbpedia:
        try:
            logging.info(f"Starting enrichment for {len(concepts)} concepts in concepts API")
            print(f"DEBUG: Starting enrichment for {len(concepts)} concepts in concepts API")
            cache = get_concept_cache(settings)
            manager = get_external_ontology_manager(settings, cache)
            concepts = await enrich_concepts_with_dbpedia_old(concepts, manager)
            print(f"DEBUG: Enrichment completed")
            
            # Count enriched concepts
            enriched_count = sum(1 for c in concepts.values() if c.get('dbpedia_enriched', False) or c.get('wikidata_enriched', False))
            logging.info(f"Concepts API enrichment complete: {enriched_count}/{len(concepts)} concepts enriched")
        except Exception as e:
            logging.error(f"Failed to apply enrichment to concepts API: {e}")
            import traceback
            logging.error(traceback.format_exc())
            print(f"ERROR: Concepts API enrichment failed: {e}")
            print(f"Traceback: {traceback.format_exc()}")
            # Continue with non-enriched concepts
    else:
        logging.info("Concepts API enrichment disabled or not configured")
    
    # Convert to list and filter
    concept_list = []
    for concept_id, concept in concepts.items():
        if concept_type and concept.get("type") != concept_type:
            continue
        
        concept_data = concept.copy()
        concept_data["id"] = concept_id
        # Ensure required fields have defaults
        concept_data.setdefault("confidence", 1.0)
        concept_data.setdefault("name", "Unknown")
        concept_data.setdefault("type", "unknown")
        concept_data.setdefault("frequency", 0)
        concept_data.setdefault("context", "")
        concept_data.setdefault("source_docs", [])
        
        # Enhanced metadata fields with defaults
        concept_data.setdefault("description", "")
        concept_data.setdefault("definition", "")
        concept_data.setdefault("notation", "")
        concept_data.setdefault("latex", "")
        concept_data.setdefault("examples", [])
        concept_data.setdefault("related_formulas", [])
        concept_data.setdefault("applications", [])
        concept_data.setdefault("prerequisites", [])
        concept_data.setdefault("complexity_level", "")
        concept_data.setdefault("domain", "")
        concept_data.setdefault("keywords", [])
        concept_data.setdefault("external_links", {})
        concept_data.setdefault("created_at", "")
        concept_data.setdefault("updated_at", "")
        
        # External enrichment fields with defaults
        concept_data.setdefault("external_id", "")
        concept_data.setdefault("dbpedia_enriched", False)
        concept_data.setdefault("wikidata_enriched", False)
        concept_data.setdefault("dbpedia_uri", "")
        concept_data.setdefault("external_source", "local")
        concept_list.append(concept_data)
    
    # Sort by frequency (descending) then by name
    concept_list.sort(key=lambda x: (-x.get("frequency", 0), x.get("name", "")))
    
    # Paginate
    total = len(concept_list)
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    paginated_concepts = concept_list[start_idx:end_idx]
    
    response_data = {
        "concepts": paginated_concepts,
        "total": total,
        "page": page,
        "per_page": per_page
    }
    
    # Cache the response
    set_cached_data(cache_key, response_data)
    
    return response_data


@router.get("/concepts/{concept_id}", response_model=ConceptResponse)
async def get_concept(
    concept_id: str,
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """
    Get detailed information about a specific concept.
    
    Args:
        concept_id: The ID of the concept to retrieve
        
    Returns:
        Detailed concept information
    """
    
    # Check cache first
    cache_key = f"concept_{concept_id}"
    cached_data = get_cached_data(cache_key, settings.web_cache_ttl)
    
    if cached_data:
        return cached_data
    
    # Load graph data
    graph_data = load_knowledge_graph()
    concepts = graph_data.get("concepts", {})
    
    # Apply enrichment if enabled
    if getattr(settings, 'dbpedia_auto_enrich', True) and getattr(settings, 'enable_dbpedia', True):
        try:
            cache = get_concept_cache(settings)
            manager = get_external_ontology_manager(settings, cache)
            concepts = await enrich_concepts_with_dbpedia_old(concepts, manager)
            logging.info(f"Applied enrichment to concepts for individual concept API")
        except Exception as e:
            logging.warning(f"Failed to apply enrichment to individual concept API: {e}")
    
    concept = concepts.get(concept_id)
    
    if not concept:
        raise HTTPException(status_code=404, detail=f"Concept {concept_id} not found")
    
    # Add ID to concept data
    concept_data = concept.copy()
    concept_data["id"] = concept_id
    
    # Ensure required fields have defaults
    concept_data.setdefault("name", "Unknown")
    concept_data.setdefault("type", "unknown")
    concept_data.setdefault("frequency", 0)
    concept_data.setdefault("confidence", 1.0)
    concept_data.setdefault("context", "")
    concept_data.setdefault("source_docs", [])
    
    # Enhanced metadata fields with defaults
    concept_data.setdefault("description", "")
    concept_data.setdefault("definition", "")
    concept_data.setdefault("notation", "")
    concept_data.setdefault("latex", "")
    concept_data.setdefault("examples", [])
    concept_data.setdefault("related_formulas", [])
    concept_data.setdefault("applications", [])
    concept_data.setdefault("prerequisites", [])
    concept_data.setdefault("complexity_level", "")
    concept_data.setdefault("domain", "")
    concept_data.setdefault("keywords", [])
    concept_data.setdefault("external_links", {})
    concept_data.setdefault("created_at", "")
    concept_data.setdefault("updated_at", "")
    
    # External enrichment fields with defaults
    concept_data.setdefault("external_id", "")
    concept_data.setdefault("dbpedia_enriched", False)
    concept_data.setdefault("wikidata_enriched", False)
    concept_data.setdefault("dbpedia_uri", "")
    concept_data.setdefault("external_source", "local")
    
    # Cache the response
    set_cached_data(cache_key, concept_data)
    
    return concept_data


@router.get("/concepts/{concept_id}/neighbors", response_model=ConceptNeighborsResponse)
async def get_concept_neighbors(
    concept_id: str,
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """
    Get neighboring concepts and relationships for a specific concept.
    
    Args:
        concept_id: The ID of the concept to get neighbors for
        
    Returns:
        Concept details with neighbors and relationships
    """
    
    # Check cache first
    cache_key = f"concept_neighbors_{concept_id}"
    cached_data = get_cached_data(cache_key, settings.web_cache_ttl)
    
    if cached_data:
        return cached_data
    
    # Load graph data
    graph_data = load_knowledge_graph()
    concepts = graph_data.get("concepts", {})
    
    # Apply enrichment if enabled
    if getattr(settings, 'dbpedia_auto_enrich', True) and getattr(settings, 'enable_dbpedia', True):
        try:
            cache = get_concept_cache(settings)
            manager = get_external_ontology_manager(settings, cache)
            concepts = await enrich_concepts_with_dbpedia_old(concepts, manager)
            logging.info(f"Applied enrichment to concepts for neighbors API")
        except Exception as e:
            logging.warning(f"Failed to apply enrichment to neighbors API: {e}")
    
    concept = concepts.get(concept_id)
    
    if not concept:
        raise HTTPException(status_code=404, detail=f"Concept {concept_id} not found")
    
    # Get concept data
    concept_data = concept.copy()
    concept_data["id"] = concept_id
    concept_data.setdefault("name", "Unknown")
    concept_data.setdefault("type", "unknown")
    concept_data.setdefault("frequency", 0)
    concept_data.setdefault("confidence", 1.0)
    concept_data.setdefault("context", "")
    concept_data.setdefault("source_docs", [])
    
    # Enhanced metadata fields with defaults
    concept_data.setdefault("description", "")
    concept_data.setdefault("definition", "")
    concept_data.setdefault("notation", "")
    concept_data.setdefault("latex", "")
    concept_data.setdefault("examples", [])
    concept_data.setdefault("related_formulas", [])
    concept_data.setdefault("applications", [])
    concept_data.setdefault("prerequisites", [])
    concept_data.setdefault("complexity_level", "")
    concept_data.setdefault("domain", "")
    concept_data.setdefault("keywords", [])
    concept_data.setdefault("external_links", {})
    concept_data.setdefault("created_at", "")
    concept_data.setdefault("updated_at", "")
    
    # External enrichment fields with defaults
    concept_data.setdefault("external_id", "")
    concept_data.setdefault("dbpedia_enriched", False)
    concept_data.setdefault("wikidata_enriched", False)
    concept_data.setdefault("dbpedia_uri", "")
    concept_data.setdefault("external_source", "local")
    
    # Get related concepts and relationships
    relationships = get_concept_relationships(graph_data, concept_id)
    neighbors = get_related_concepts(graph_data, concept_id)
    
    response_data = {
        "concept": concept_data,
        "neighbors": neighbors,
        "relationships": relationships
    }
    
    # Cache the response
    set_cached_data(cache_key, response_data)
    
    logging.info(f"Retrieved {len(neighbors)} neighbors for concept {concept_id}")
    return response_data


@router.get("/documents")
async def get_documents(
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """
    Get a list of all source documents in the knowledge graph.
    
    Returns:
        List of documents with concept counts
    """
    
    # Check cache first
    cache_key = "documents_list"
    cached_data = get_cached_data(cache_key, settings.web_cache_ttl)
    
    if cached_data:
        return cached_data
    
    # Load graph data
    graph_data = load_knowledge_graph()
    concepts = graph_data.get("concepts", {})
    
    # Collect document information
    documents = {}
    for concept_id, concept in concepts.items():
        source_docs = concept.get("source_docs", [])
        for doc in source_docs:
            if doc not in documents:
                documents[doc] = {"name": doc, "concept_count": 0, "concepts": []}
            documents[doc]["concept_count"] += 1
            documents[doc]["concepts"].append({
                "id": concept_id,
                "name": concept.get("name", "Unknown"),
                "type": concept.get("type", "unknown")
            })
    
    # Convert to list and sort by concept count
    document_list = list(documents.values())
    document_list.sort(key=lambda x: -x["concept_count"])
    
    response_data = {
        "documents": document_list,
        "total": len(document_list)
    }
    
    # Cache the response
    set_cached_data(cache_key, response_data)
    
    return response_data


@router.get("/documents/{document_name}/concepts")
async def get_document_concepts(
    document_name: str,
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """
    Get all concepts from a specific document.
    
    Args:
        document_name: Name of the document
        
    Returns:
        List of concepts from the specified document
    """
    
    # Check cache first
    cache_key = f"document_concepts_{document_name}"
    cached_data = get_cached_data(cache_key, settings.web_cache_ttl)
    
    if cached_data:
        return cached_data
    
    # Load graph data
    graph_data = load_knowledge_graph()
    concepts = graph_data.get("concepts", {})
    
    # Find concepts from this document
    document_concepts = []
    for concept_id, concept in concepts.items():
        source_docs = concept.get("source_docs", [])
        if document_name in source_docs:
            concept_data = concept.copy()
            concept_data["id"] = concept_id
            document_concepts.append(concept_data)
    
    if not document_concepts:
        raise HTTPException(status_code=404, detail=f"Document {document_name} not found or has no concepts")
    
    # Sort by frequency
    document_concepts.sort(key=lambda x: -x.get("frequency", 0))
    
    response_data = {
        "document": document_name,
        "concepts": document_concepts,
        "total": len(document_concepts)
    }
    
    # Cache the response
    set_cached_data(cache_key, response_data)
    
    return response_data