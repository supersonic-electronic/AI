"""
DBpedia API router for external knowledge integration.

This module provides API endpoints for DBpedia search, concept enrichment,
and metadata retrieval to support the web interface.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field

from src.settings import Settings
from src.knowledge.external_ontologies import ExternalOntologyManager
from src.knowledge.concept_cache import ConceptCache
from src.knowledge.ontology import Concept, ConceptType


class DBpediaSearchRequest(BaseModel):
    """Request model for DBpedia search."""
    query: str = Field(..., min_length=1, max_length=100)
    concept_type: Optional[str] = None
    limit: int = Field(default=10, ge=1, le=50)


class DBpediaConceptResponse(BaseModel):
    """Response model for DBpedia concept data."""
    external_id: str
    source: str
    label: str
    description: Optional[str] = None
    aliases: List[str] = []
    properties: Dict[str, Any] = {}
    related_concepts: List[str] = []
    confidence: float
    uri: Optional[str] = None
    categories: List[str] = []


class DBpediaEnrichmentRequest(BaseModel):
    """Request model for concept enrichment."""
    concept_name: str = Field(..., min_length=1)
    concept_type: Optional[str] = None


class DBpediaEnrichmentResponse(BaseModel):
    """Response model for concept enrichment."""
    concept_name: str
    enriched: bool
    dbpedia_data: Optional[DBpediaConceptResponse] = None
    error: Optional[str] = None


router = APIRouter()
logger = logging.getLogger(__name__)


def get_settings(request: Request) -> Settings:
    """Dependency to get settings from app state."""
    return request.app.state.settings


def get_dbpedia_manager(settings: Settings = Depends(get_settings)) -> ExternalOntologyManager:
    """Get DBpedia manager dependency."""
    cache = ConceptCache(settings)
    return ExternalOntologyManager(settings, cache)




@router.get("/search", response_model=List[DBpediaConceptResponse])
async def search_dbpedia_concepts(
    query: str = Query(..., min_length=1, max_length=100),
    concept_type: Optional[str] = Query(None),
    limit: int = Query(default=10, ge=1, le=50),
    manager: ExternalOntologyManager = Depends(get_dbpedia_manager)
) -> List[DBpediaConceptResponse]:
    """
    Search for concepts in DBpedia.
    
    Args:
        query: Search term
        concept_type: Optional concept type filter
        limit: Maximum number of results
        manager: External ontology manager
        
    Returns:
        List of DBpedia concept results
    """
    try:
        # Get DBpedia connector
        dbpedia_connector = manager.get_connector('dbpedia')
        if not dbpedia_connector:
            raise HTTPException(status_code=503, detail="DBpedia connector not available")
        
        # Convert concept type if provided
        concept_type_enum = None
        if concept_type:
            try:
                concept_type_enum = ConceptType(concept_type)
            except ValueError:
                logger.warning(f"Invalid concept type: {concept_type}")
        
        # Search DBpedia
        search_results = dbpedia_connector.search_concept(query, concept_type_enum)
        
        # Convert to response format
        responses = []
        for result in search_results[:limit]:
            response = DBpediaConceptResponse(
                external_id=result.external_id,
                source=result.source,
                label=result.label,
                description=result.description,
                aliases=result.aliases,
                properties=result.properties,
                related_concepts=result.related_concepts,
                confidence=result.confidence,
                uri=result.external_id if result.external_id.startswith('http') else None,
                categories=result.properties.get('categories', [])
            )
            responses.append(response)
        
        logger.info(f"DBpedia search for '{query}' returned {len(responses)} results")
        return responses
        
    except Exception as e:
        logger.error(f"DBpedia search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.post("/enrich", response_model=DBpediaEnrichmentResponse)
async def enrich_concept_with_dbpedia(
    request: DBpediaEnrichmentRequest,
    manager: ExternalOntologyManager = Depends(get_dbpedia_manager)
) -> DBpediaEnrichmentResponse:
    """
    Enrich a concept with DBpedia data.
    
    Args:
        request: Enrichment request
        manager: External ontology manager
        
    Returns:
        Enrichment response with DBpedia data
    """
    try:
        # Create concept object
        concept_type_enum = ConceptType.CONCEPT  # Default
        if request.concept_type:
            try:
                concept_type_enum = ConceptType(request.concept_type)
            except ValueError:
                pass
        
        concept = Concept(
            name=request.concept_name,
            concept_type=concept_type_enum,
            confidence=1.0
        )
        
        # Enrich with DBpedia
        enriched_concept = manager.enrich_concept(concept)
        
        # Check if enrichment was successful
        dbpedia_data = None
        enriched = False
        
        if enriched_concept.properties.get('external_source') == 'dbpedia':
            enriched = True
            dbpedia_data = DBpediaConceptResponse(
                external_id=enriched_concept.properties.get('external_id', ''),
                source='dbpedia',
                label=enriched_concept.name,
                description=enriched_concept.description,
                aliases=list(enriched_concept.aliases),
                properties=enriched_concept.properties,
                related_concepts=[],
                confidence=enriched_concept.properties.get('external_confidence', 0.0),
                uri=enriched_concept.properties.get('external_id', ''),
                categories=enriched_concept.properties.get('categories', [])
            )
        
        response = DBpediaEnrichmentResponse(
            concept_name=request.concept_name,
            enriched=enriched,
            dbpedia_data=dbpedia_data
        )
        
        logger.info(f"Concept '{request.concept_name}' enrichment: {enriched}")
        return response
        
    except Exception as e:
        logger.error(f"Concept enrichment failed: {e}")
        return DBpediaEnrichmentResponse(
            concept_name=request.concept_name,
            enriched=False,
            error=str(e)
        )


@router.get("/concepts/{concept_id}", response_model=DBpediaConceptResponse)
async def get_dbpedia_concept_details(
    concept_id: str,
    manager: ExternalOntologyManager = Depends(get_dbpedia_manager)
) -> DBpediaConceptResponse:
    """
    Get detailed information about a specific DBpedia concept.
    
    Args:
        concept_id: DBpedia concept ID or URI
        manager: External ontology manager
        
    Returns:
        Detailed concept information
    """
    try:
        # Get DBpedia connector
        dbpedia_connector = manager.get_connector('dbpedia')
        if not dbpedia_connector:
            raise HTTPException(status_code=503, detail="DBpedia connector not available")
        
        # Get concept details
        concept_data = dbpedia_connector.get_concept_details(concept_id)
        
        if not concept_data:
            raise HTTPException(status_code=404, detail=f"Concept not found: {concept_id}")
        
        # Get related concepts
        related_concepts = dbpedia_connector.get_related_concepts(concept_id)
        
        response = DBpediaConceptResponse(
            external_id=concept_data.external_id,
            source=concept_data.source,
            label=concept_data.label,
            description=concept_data.description,
            aliases=concept_data.aliases,
            properties=concept_data.properties,
            related_concepts=[rel.label for rel in related_concepts],
            confidence=concept_data.confidence,
            uri=concept_data.external_id,
            categories=concept_data.properties.get('categories', [])
        )
        
        logger.info(f"Retrieved DBpedia concept details for: {concept_id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get concept details: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve concept: {str(e)}")


@router.get("/stats")
async def get_dbpedia_stats(
    manager: ExternalOntologyManager = Depends(get_dbpedia_manager)
) -> Dict[str, Any]:
    """
    Get DBpedia integration statistics.
    
    Args:
        manager: External ontology manager
        
    Returns:
        Statistics about DBpedia integration
    """
    try:
        # Get cache stats if available
        cache_stats = {}
        if hasattr(manager, 'cache'):
            cache_stats = {
                'cache_size': len(manager.cache._cache) if hasattr(manager.cache, '_cache') else 0,
                'cache_hits': getattr(manager.cache, '_hits', 0),
                'cache_misses': getattr(manager.cache, '_misses', 0)
            }
        
        return {
            'service': 'dbpedia-integration',
            'status': 'active',
            'connectors_available': list(manager.connectors.keys()),
            'dbpedia_enabled': 'dbpedia' in manager.connectors,
            **cache_stats
        }
        
    except Exception as e:
        logger.error(f"Failed to get DBpedia stats: {e}")
        return {
            'service': 'dbpedia-integration',
            'status': 'error',
            'error': str(e)
        }