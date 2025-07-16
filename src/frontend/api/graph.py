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
from src.knowledge.external_ontologies import ExternalOntologyManager
from src.knowledge.concept_cache import ConceptCache
from src.knowledge.ontology import Concept, ConceptType


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


class ConceptDetailResponse(BaseModel):
    """Response model for detailed concept information."""
    id: str
    name: str
    concept_type: str
    description: Optional[str] = None
    definition: Optional[str] = None
    notation: Optional[str] = None
    latex: Optional[str] = None
    examples: List[str] = []
    applications: List[str] = []
    prerequisites: List[str] = []
    related_formulas: List[str] = []
    complexity_level: Optional[str] = None
    domain: Optional[str] = None
    keywords: List[str] = []
    external_links: Dict[str, str] = {}
    aliases: List[str] = []
    properties: Dict[str, Any] = {}
    source_document: Optional[str] = None
    source_page: Optional[int] = None
    confidence: float = 1.0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    related_concepts: List[Dict[str, Any]] = []


class ConceptSearchResponse(BaseModel):
    """Response model for concept search results."""
    concepts: List[Dict[str, Any]]
    total_count: int
    query: str


# Router instance
router = APIRouter()

# Simple in-memory cache
_cache: Dict[str, Dict[str, Any]] = {}
_cache_timestamps: Dict[str, datetime] = {}


def get_settings(request: Request) -> Settings:
    """Dependency to get settings from app state."""
    return request.app.state.settings


def get_dbpedia_manager(settings: Settings = Depends(get_settings)) -> ExternalOntologyManager:
    """Get DBpedia manager dependency."""
    cache = ConceptCache(settings)
    return ExternalOntologyManager(settings, cache)


def _extract_title_from_filename(source_docs: List[str]) -> str:
    """Extract title from filename by removing common patterns."""
    if not source_docs:
        return ""
    
    # Use the first document as primary source
    filename = source_docs[0]
    
    # Remove file extension
    title = filename.replace('.txt', '').replace('.pdf', '')
    
    # Clean up common patterns
    title = title.replace('_', ' ')
    
    # Handle parenthetical publisher info
    if '(' in title and ')' in title:
        # Extract the main title before publisher info
        main_part = title.split('(')[0].strip()
        if main_part:
            title = main_part
    
    return title


def _extract_authors_from_filename(source_docs: List[str]) -> List[str]:
    """Extract author names from filename patterns."""
    if not source_docs:
        return []
    
    authors = []
    import re
    
    for doc in source_docs:  # Check all docs, not just first 3
        # Look for parenthetical author info like "Roncalli, Thierry - Title"
        if ') ' in doc and ' - ' in doc:
            # Handle complex patterns like "(Publisher) Author, Name - Title"
            parts = doc.split(') ')
            if len(parts) > 1:
                author_part = parts[1].split(' - ')[0]
                if ',' in author_part and len(author_part.split(',')) <= 2:
                    authors.append(author_part.strip())
        elif '(' in doc and ')' in doc and 'Series' not in doc:
            # Simple parenthetical patterns
            paren_content = doc.split('(')[1].split(')')[0]
            if ',' in paren_content and len(paren_content.split(',')) <= 3 and 'CRC' not in paren_content:
                authors.append(paren_content.strip())
        
        # Look for common author name patterns in finance/academic papers
        known_authors = {
            'Fabozzi': 'Frank J. Fabozzi',
            'Markowitz': 'Harry Markowitz', 
            'Alonso': 'Alonso',
            'Roncalli': 'Thierry Roncalli',
            'Idzorek': 'Thomas Idzorek',
            'Black': 'Fischer Black',
            'Litterman': 'Robert Litterman'
        }
        
        for surname, full_name in known_authors.items():
            if surname in doc and full_name not in authors:
                authors.append(full_name)
        
        # Extract author from patterns like "AuthorLastname_Topic.txt" 
        if '_' in doc and not doc.startswith('Mean') and not doc.startswith('Black') and not doc.startswith('('):
            potential_author = doc.split('_')[0]
            if (potential_author and len(potential_author) > 2 and 
                potential_author not in ['Fifty', 'Sixty', 'Approaching'] and
                not any(known in potential_author for known in ['Fabozzi', 'Markowitz', 'Alonso', 'Roncalli', 'Idzorek'])):
                # Clean up the author name
                clean_author = re.sub(r'([a-z])([A-Z])', r'\1 \2', potential_author)
                authors.append(clean_author)
    
    return list(set(authors))  # Remove duplicates


def _extract_year_from_filename(source_docs: List[str]) -> str:
    """Extract publication year from filename patterns."""
    if not source_docs:
        return ""
    
    import re
    for doc in source_docs:
        # Look for 4-digit years in parentheses or filename
        year_match = re.search(r'\((\d{4})\)|\b(19|20)\d{2}\b', doc)
        if year_match:
            return year_match.group(1) if year_match.group(1) else year_match.group(0)
    
    return ""


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


async def enrich_concepts_with_dbpedia(concepts: Dict[str, Any], manager: ExternalOntologyManager) -> Dict[str, Any]:
    """Enrich concepts with DBpedia data."""
    enriched_concepts = {}
    
async def enrich_and_expand_with_dbpedia(concepts: Dict[str, Any], manager: ExternalOntologyManager) -> tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Enrich concepts with DBpedia data and add neighboring nodes."""
    enriched_concepts = {}
    new_neighboring_concepts = {}
    
    # Cache for neighboring concept enrichment to avoid duplicates
    neighboring_enrichment_cache = {}
    
    for concept_id, concept_data in concepts.items():
        try:
            # Create concept object  
            concept_type = ConceptType.METHODOLOGY  # Default fallback
            try:
                concept_type = ConceptType(concept_data.get("type", "methodology"))
            except ValueError:
                # If type doesn't match any enum value, keep the default
                pass
            
            concept = Concept(
                id=concept_id,
                name=concept_data.get("name", "Unknown"),
                concept_type=concept_type,
                confidence=concept_data.get("confidence", 1.0),
                description=concept_data.get("description", "")
            )
            
            # Add existing properties
            for key, value in concept_data.items():
                if key not in ["name", "type", "confidence", "description"]:
                    concept.properties[key] = value
            
            # Enrich with external ontologies
            enriched_concept = manager.enrich_concept(concept)
            
            # Convert back to dictionary format
            enriched_data = concept_data.copy()
            enriched_data.update({
                "name": enriched_concept.name,
                "description": enriched_concept.description or enriched_data.get("description", ""),
                "confidence": enriched_concept.confidence,
                "aliases": list(enriched_concept.aliases) if enriched_concept.aliases else enriched_data.get("aliases", []),
                "properties": {**enriched_data.get("properties", {}), **enriched_concept.properties}
            })
            
            # Add external metadata if enriched with any external source
            external_source = enriched_concept.properties.get('external_source')
            if external_source in ['dbpedia', 'wikidata']:
                enriched_data.update({
                    "dbpedia_enriched": True,
                    "dbpedia_uri": enriched_concept.properties.get('external_id', ''),
                    "dbpedia_confidence": enriched_concept.properties.get('external_confidence', 0.0),
                    # Keep external_source as 'local' for original concepts that are enriched
                    "external_source": "local"  # This marks it as a local concept enriched with external data
                })
                
                # Add neighboring concepts from related_external_concepts
                related_concepts = enriched_concept.properties.get('related_external_concepts', [])
                if related_concepts:
                    logging.debug(f"🔗 Adding {len(related_concepts[:3])} neighboring concepts for '{enriched_concept.name}'")
                    for i, related_name in enumerate(related_concepts[:3]):  # Limit to 3 neighbors per concept
                        # Create unique ID for related concept
                        related_id = f"ext_{concept_id}_{i}"
                        
                        # Check cache first to avoid re-enriching same concept
                        if related_name in neighboring_enrichment_cache:
                            # Use cached enrichment data
                            cached_data = neighboring_enrichment_cache[related_name]
                            new_neighboring_concepts[related_id] = {
                                **cached_data,
                                "id": related_id,
                                "parent_concept_id": concept_id,
                                "properties": {
                                    **cached_data.get("properties", {}),
                                    "is_neighboring_node": True,
                                    "source_concept": enriched_concept.name
                                }
                            }
                            logging.debug(f"🔄 Using cached enrichment for '{related_name}'")
                        else:
                            # Try to enrich the neighboring concept itself
                            try:
                                neighboring_concept = Concept(
                                    id=related_id,
                                    name=related_name,
                                    concept_type=ConceptType.CONCEPT,
                                    confidence=0.7,
                                    description=f"Related to {enriched_concept.name} via {external_source.title()}"
                                )
                                
                                # Enrich the neighboring concept
                                enriched_neighbor = manager.enrich_concept(neighboring_concept)
                                
                                # Create enriched neighboring concept node
                                neighbor_external_source = enriched_neighbor.properties.get('external_source', f"{external_source}_related")
                                neighbor_confidence = enriched_neighbor.properties.get('external_confidence', 0.7)
                                
                                # Determine the proper type for the neighboring node
                                neighbor_type = "concept"  # Default fallback
                                if enriched_neighbor.properties.get('types'):
                                    # Use the first available type from DBpedia
                                    neighbor_type = enriched_neighbor.properties['types'][0].replace('http://dbpedia.org/ontology/', '').lower()
                                elif enriched_neighbor.properties.get('typeName'):
                                    # Use typeName if available
                                    neighbor_type = enriched_neighbor.properties['typeName'][0].lower() if isinstance(enriched_neighbor.properties['typeName'], list) else enriched_neighbor.properties['typeName'].lower()
                                elif enriched_neighbor.concept_type:
                                    # Use the concept type from the enriched neighbor
                                    neighbor_type = enriched_neighbor.concept_type.value if hasattr(enriched_neighbor.concept_type, 'value') else str(enriched_neighbor.concept_type)
                                
                                neighbor_node_data = {
                                    "name": enriched_neighbor.name,
                                    "type": neighbor_type, 
                                    "description": enriched_neighbor.description or f"Related to {enriched_concept.name} via {external_source.title()}",
                                    "confidence": neighbor_confidence,
                                    "frequency": max(10, int(neighbor_confidence * 50)),  # Give it some visual weight
                                    "dbpedia_enriched": neighbor_external_source in ['dbpedia', 'wikidata'],
                                    "external_source": neighbor_external_source if neighbor_external_source in ['dbpedia', 'wikidata'] else "dbpedia",
                                    "aliases": list(enriched_neighbor.aliases) if enriched_neighbor.aliases else [],
                                    "properties": enriched_neighbor.properties
                                }
                                
                                # Cache the enrichment for reuse
                                neighboring_enrichment_cache[related_name] = neighbor_node_data
                                
                                new_neighboring_concepts[related_id] = {
                                    **neighbor_node_data,
                                    "id": related_id,
                                    "parent_concept_id": concept_id,
                                    "properties": {
                                        **neighbor_node_data["properties"],
                                        "is_neighboring_node": True,
                                        "source_concept": enriched_concept.name
                                    }
                                }
                                
                                logging.debug(f"✨ Enriched neighboring concept '{related_name}' with {neighbor_external_source}")
                                
                            except Exception as e:
                                logging.debug(f"⚠️ Failed to enrich neighboring concept '{related_name}': {e}")
                                # Fallback to simple placeholder
                                fallback_data = {
                                    "name": related_name,
                                    "type": "concept",  # Use generic concept type for fallback
                                    "description": f"Related to {enriched_concept.name} via {external_source.title()}",
                                    "confidence": 0.7,
                                    "frequency": 25,  # Default visual weight
                                    "dbpedia_enriched": False,
                                    "external_source": "dbpedia",  # Mark as DBpedia source
                                    "aliases": [],
                                    "properties": {}
                                }
                                
                                neighboring_enrichment_cache[related_name] = fallback_data
                                
                                new_neighboring_concepts[related_id] = {
                                    **fallback_data,
                                    "id": related_id,
                                    "parent_concept_id": concept_id,
                                    "properties": {
                                        "is_neighboring_node": True,
                                        "source_concept": enriched_concept.name
                                    }
                                }
            else:
                enriched_data["dbpedia_enriched"] = False
                enriched_data["external_source"] = "local"
            
            enriched_concepts[concept_id] = enriched_data
            
        except Exception as e:
            logging.warning(f"Failed to enrich concept {concept_id} (name: {concept_data.get('name', 'unknown')}): {str(e)}")
            # Use original data if enrichment fails
            concept_data["dbpedia_enriched"] = False
            concept_data["wikidata_enriched"] = False
            concept_data["external_source"] = "local"
            # Add source document metadata for error cases too
            concept_data["source_documents"] = concept_data.get("source_docs", [])
            concept_data["source_context_snippet"] = concept_data.get("context", "")
            concept_data["concept_frequency"] = concept_data.get("frequency", 0)
            enriched_concepts[concept_id] = concept_data
    
    # Create relationships between original concepts and neighboring concepts
    new_relationships = []
    neighboring_concepts_by_parent = {}
    
    # Group neighboring concepts by parent for cross-connections
    for related_id, related_concept in new_neighboring_concepts.items():
        parent_id = related_concept["parent_concept_id"]
        if parent_id not in neighboring_concepts_by_parent:
            neighboring_concepts_by_parent[parent_id] = []
        neighboring_concepts_by_parent[parent_id].append((related_id, related_concept))
        
        # Create relationship from parent to neighboring node
        new_relationships.append({
            "id": f"rel_{parent_id}_{related_id}",
            "source": parent_id,
            "target": related_id,
            "type": "related_to",
            "weight": 0.7,
            "confidence": 0.7,
            "source_type": "external_relation",
            "properties": {
                "external_source": True,
                "relationship_type": "semantic_similarity"
            }
        })
    
    # Create cross-connections between neighboring nodes that share semantic similarity
    created_cross_connections = set()
    for parent_id, neighbors in neighboring_concepts_by_parent.items():
        for i, (id1, concept1) in enumerate(neighbors):
            for j, (id2, concept2) in enumerate(neighbors[i+1:], i+1):
                # Create bidirectional connections between related neighboring nodes
                connection_key = tuple(sorted([id1, id2]))
                if connection_key not in created_cross_connections:
                    new_relationships.append({
                        "id": f"cross_{id1}_{id2}",
                        "source": id1,
                        "target": id2,
                        "type": "semantic_similarity",
                        "weight": 0.5,
                        "confidence": 0.6,
                        "source_type": "cross_reference",
                        "properties": {
                            "external_source": True,
                            "relationship_type": "cross_reference",
                            "shared_parent": parent_id
                        }
                    })
                    created_cross_connections.add(connection_key)
    
    # Merge original and neighboring concepts
    all_concepts = {**enriched_concepts, **new_neighboring_concepts}
    logging.info(f"Added {len(new_neighboring_concepts)} neighboring DBpedia concepts and {len(new_relationships)} relationships to {len(enriched_concepts)} original concepts")
    
    return all_concepts, new_relationships


async def enrich_concepts_with_dbpedia_old(concepts: Dict[str, Any], manager: ExternalOntologyManager) -> Dict[str, Any]:
    """Original enrichment function without neighboring nodes."""
    enriched_concepts = {}
    
    for concept_id, concept_data in concepts.items():
        try:
            # Create concept object  
            concept_type = ConceptType.METHODOLOGY  # Default fallback
            try:
                concept_type = ConceptType(concept_data.get("type", "methodology"))
            except ValueError:
                # If type doesn't match any enum value, keep the default
                pass
            
            concept = Concept(
                id=concept_id,
                name=concept_data.get("name", "Unknown"),
                concept_type=concept_type,
                confidence=concept_data.get("confidence", 1.0),
                description=concept_data.get("description", "")
            )
            
            # Add existing properties
            for key, value in concept_data.items():
                if key not in ["name", "type", "confidence", "description"]:
                    concept.properties[key] = value
            
            # Enrich with external ontologies
            enriched_concept = manager.enrich_concept(concept)
            
            # Convert back to dictionary format
            enriched_data = concept_data.copy()
            enriched_data.update({
                "name": enriched_concept.name,
                "description": enriched_concept.description or enriched_data.get("description", ""),
                "confidence": enriched_concept.confidence,
                "aliases": list(enriched_concept.aliases) if enriched_concept.aliases else enriched_data.get("aliases", []),
                "properties": {**enriched_data.get("properties", {}), **enriched_concept.properties}
            })
            
            # Add external ontology metadata if enriched
            external_source = enriched_concept.properties.get('external_source')
            
            # Check for dual source enrichment
            has_dbpedia = external_source == 'dbpedia' or enriched_concept.properties.get('dbpedia_id')
            has_wikidata = external_source == 'wikidata' or enriched_concept.properties.get('wikidata_id')
            
            if external_source in ['dbpedia', 'wikidata'] or has_dbpedia or has_wikidata:
                logging.debug(f"Enriching concept '{enriched_concept.name}' with external data (DBpedia: {has_dbpedia}, Wikidata: {has_wikidata})")
                
                # Build external URLs dictionary
                external_urls = {}
                if has_dbpedia:
                    dbpedia_uri = enriched_concept.properties.get('dbpedia_id') or (enriched_concept.properties.get('external_id') if external_source == 'dbpedia' else '')
                    external_urls['dbpedia'] = f"http://dbpedia.org/resource/{dbpedia_uri.split('/')[-1]}" if dbpedia_uri else ''
                    external_urls['dbpedia_id'] = dbpedia_uri
                    
                if has_wikidata:
                    wikidata_uri = enriched_concept.properties.get('wikidata_id') or (enriched_concept.properties.get('external_id') if external_source == 'wikidata' else '')
                    wikidata_url = enriched_concept.properties.get('url') or enriched_concept.properties.get('concepturi', '')
                    external_urls['wikidata'] = wikidata_url or f"https://www.wikidata.org/wiki/{wikidata_uri}" if wikidata_uri else ''
                    external_urls['wikidata_id'] = wikidata_uri
                
                enriched_data.update({
                    # Badge indicators for dual sources
                    "dbpedia_enriched": has_dbpedia,
                    "wikidata_enriched": has_wikidata,
                    "external_source": "local",  # Keep as local since it's an enriched local concept
                    
                    # Primary source metadata (backward compatibility) 
                    "external_id": enriched_concept.properties.get('external_id', ''),
                    "dbpedia_uri": enriched_concept.properties.get('external_id', '') if external_source == 'dbpedia' else enriched_concept.properties.get('dbpedia_id', ''),
                    "dbpedia_confidence": enriched_concept.properties.get('external_confidence', 0.0) if external_source == 'dbpedia' else enriched_concept.properties.get('dbpedia_confidence', 0.0),
                    
                    # Enhanced metadata for tooltips from all sources
                    "external_categories": enriched_concept.properties.get('categories', []),
                    "external_types": enriched_concept.properties.get('types', []),
                    "external_type_names": enriched_concept.properties.get('typeName', []),
                    "external_related_concepts": enriched_concept.properties.get('related_external_concepts', []),
                    "external_urls": external_urls,
                    "external_comments": enriched_concept.properties.get('comment', ''),
                    "external_redirect_labels": enriched_concept.properties.get('redirectlabel', []),
                    
                    # Wikidata-specific semantic metadata
                    "wikidata_instance_of": enriched_concept.properties.get('instanceOf', []),
                    "wikidata_subclass_of": enriched_concept.properties.get('subclassOf', []),
                    
                    # Dual-source metadata
                    "wikidata_id": enriched_concept.properties.get('wikidata_id', ''),
                    "wikidata_confidence": enriched_concept.properties.get('wikidata_confidence', 0.0),
                    "dbpedia_id": enriched_concept.properties.get('dbpedia_id', ''),
                    "dbpedia_secondary_confidence": enriched_concept.properties.get('dbpedia_confidence', 0.0),
                    
                    # Source document metadata (will be extracted during conversion)
                    "source_documents": concept_data.get("source_docs", []),
                    "source_context_snippet": concept_data.get("context", ""),
                    "concept_frequency": concept_data.get("frequency", 0)
                })
            else:
                enriched_data["dbpedia_enriched"] = False
                enriched_data["wikidata_enriched"] = False
                enriched_data["external_source"] = "local"
                
                # Add empty source document metadata for non-enriched concepts
                enriched_data["source_documents"] = concept_data.get("source_docs", [])
                enriched_data["source_context_snippet"] = concept_data.get("context", "")
                enriched_data["concept_frequency"] = concept_data.get("frequency", 0)
            
            enriched_concepts[concept_id] = enriched_data
            
        except Exception as e:
            logging.warning(f"Failed to enrich concept {concept_id} (name: {concept_data.get('name', 'unknown')}): {str(e)}")
            # Use original data if enrichment fails
            concept_data["dbpedia_enriched"] = False
            concept_data["wikidata_enriched"] = False
            concept_data["external_source"] = "local"
            # Add source document metadata for error cases too
            concept_data["source_documents"] = concept_data.get("source_docs", [])
            concept_data["source_context_snippet"] = concept_data.get("context", "")
            concept_data["concept_frequency"] = concept_data.get("frequency", 0)
            enriched_concepts[concept_id] = concept_data
    
    return enriched_concepts


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
                "description": concept.get("description", ""),
                "definition": concept.get("definition", ""),
                "notation": concept.get("notation", ""),
                "latex": concept.get("latex", ""),
                "examples": concept.get("examples", []),
                "applications": concept.get("applications", []),
                "prerequisites": concept.get("prerequisites", []),
                "related_formulas": concept.get("related_formulas", []),
                "complexity_level": concept.get("complexity_level", ""),
                "domain": concept.get("domain", ""),
                "keywords": concept.get("keywords", []),
                "external_links": concept.get("external_links", {}),
                "aliases": concept.get("aliases", []),
                "properties": concept.get("properties", {}),
                "source_document": concept.get("source_document", ""),
                "source_page": concept.get("source_page"),
                "confidence": concept.get("confidence", 1.0),
                "created_at": concept.get("created_at", ""),
                "updated_at": concept.get("updated_at", ""),
                # Legacy fields for backward compatibility
                "frequency": concept.get("frequency", 0),
                "context": concept.get("context", ""),
                "source_docs": concept.get("source_docs", []),
                # External ontology integration fields
                "dbpedia_enriched": concept.get("dbpedia_enriched", False),
                "wikidata_enriched": concept.get("wikidata_enriched", False),
                "dbpedia_uri": concept.get("dbpedia_uri", ""),
                "dbpedia_confidence": concept.get("dbpedia_confidence", 0.0),
                "external_source": concept.get("external_source", "local"),
                
                # Enhanced external metadata from properties
                "categories": concept.get("properties", {}).get("categories", []),
                "types": concept.get("properties", {}).get("types", []),
                "typeName": concept.get("properties", {}).get("typeName", []),
                "related_external_concepts": concept.get("properties", {}).get("related_external_concepts", []),
                "external_id": concept.get("properties", {}).get("external_id", ""),
                "external_confidence": concept.get("properties", {}).get("external_confidence", 0.0),
                "concepturi": concept.get("properties", {}).get("concepturi", ""),
                "url": concept.get("properties", {}).get("url", ""),
                
                # Enhanced tooltip metadata
                "external_categories": concept.get("external_categories", []),
                "external_types": concept.get("external_types", []),
                "external_type_names": concept.get("external_type_names", []),
                "external_related_concepts": concept.get("external_related_concepts", []),
                "external_urls": concept.get("external_urls", {}),
                "external_comments": concept.get("external_comments", ""),
                "external_redirect_labels": concept.get("external_redirect_labels", []),
                
                # Wikidata-specific semantic metadata
                "wikidata_enriched": concept.get("wikidata_enriched", False),
                "wikidata_instance_of": concept.get("wikidata_instance_of", []),
                "wikidata_subclass_of": concept.get("wikidata_subclass_of", []),
                
                # Source document context metadata extracted at conversion time
                "source_documents": concept.get("source_docs", []),
                "source_context_snippet": concept.get("context", ""),
                "concept_frequency": concept.get("frequency", 0),
                "source_title": _extract_title_from_filename(concept.get("source_docs", [])),
                "source_authors": _extract_authors_from_filename(concept.get("source_docs", [])),
                "source_publication_year": _extract_year_from_filename(concept.get("source_docs", [])),
                "source_journal": concept.get("source_journal", ""),
                "source_doi": concept.get("source_doi", ""),
                "primary_source_doc": concept.get("source_docs", ["Unknown"])[0] if concept.get("source_docs") else "Unknown",
                
                # Additional secondary source metadata
                "wikidata_id": concept.get("wikidata_id", ""),
                "wikidata_confidence": concept.get("wikidata_confidence", 0.0),
                "dbpedia_id": concept.get("dbpedia_id", ""),
                "dbpedia_local_confidence": concept.get("properties", {}).get("dbpedia_confidence", 0.0),
                
                # Additional metadata that might be available
                "is_neighboring_node": concept.get("properties", {}).get("is_neighboring_node", False),
                "source_concept": concept.get("properties", {}).get("source_concept", ""),
                "parent_concept_id": concept.get("parent_concept_id", "")
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
                "confidence": relationship.get("confidence", 1.0),
                "source_type": relationship.get("source_type", "derived"),
                "external_source": relationship.get("external_source", "local")
            }
        }
        edges.append(edge)
    
    return {"nodes": nodes, "edges": edges}


@router.get("/graph", response_model=GraphDataResponse)
async def get_graph_data(
    enrich_dbpedia: bool = True,
    settings: Settings = Depends(get_settings),
    manager: ExternalOntologyManager = Depends(get_dbpedia_manager)
) -> Dict[str, Any]:
    """
    Get the complete knowledge graph data in Cytoscape.js format.
    
    Args:
        enrich_dbpedia: Whether to enrich concepts with DBpedia data
        
    Returns:
        Complete graph data with nodes and edges
    """
    
    # Check cache first
    cache_key = f"full_graph_dbpedia_{enrich_dbpedia}"
    cached_data = get_cached_data(cache_key, settings.web_cache_ttl)
    
    if cached_data:
        logging.debug("Returning cached graph data")
        return cached_data
    
    # Load graph data
    graph_data = load_knowledge_graph()
    
    # Enrich with DBpedia if requested
    if enrich_dbpedia and getattr(settings, 'enable_dbpedia', True):
        try:
            concepts = graph_data.get("concepts", {})
            logging.info(f"🔍 Starting DBpedia enrichment for {len(concepts)} concepts")
            enriched_concepts = await enrich_concepts_with_dbpedia_old(concepts, manager)
            graph_data["concepts"] = enriched_concepts
            
            # Count enriched concepts for debugging
            enriched_count = sum(1 for c in enriched_concepts.values() if c.get('dbpedia_enriched', False))
            
            logging.info(f"✅ Enriched {enriched_count} concepts with DBpedia data (enrichment-only mode)")
        except Exception as e:
            logging.warning(f"❌ DBpedia enrichment failed, using local data only: {e}")
            import traceback
            logging.error(f"Full traceback: {traceback.format_exc()}")
    else:
        logging.info(f"🚫 DBpedia enrichment disabled: enrich_dbpedia={enrich_dbpedia}, enable_dbpedia={getattr(settings, 'enable_dbpedia', False)}")
    
    # Convert to Cytoscape format
    cytoscape_data = convert_to_cytoscape_format(graph_data)
    
    # Calculate statistics
    stats = {
        "total_concepts": len(cytoscape_data["nodes"]),
        "total_relationships": len(cytoscape_data["edges"]),
        "concept_types": {},
        "relationship_types": {},
        "dbpedia_enriched": 0,
        "local_concepts": 0,
        "data_sources": {}
    }
    
    # Count concept types and sources
    for node in cytoscape_data["nodes"]:
        concept_type = node["data"].get("type", "unknown")
        stats["concept_types"][concept_type] = stats["concept_types"].get(concept_type, 0) + 1
        
        # Count DBpedia enrichment
        if node["data"].get("dbpedia_enriched", False):
            stats["dbpedia_enriched"] += 1
        else:
            stats["local_concepts"] += 1
            
        # Count data sources
        source = node["data"].get("external_source", "local")
        stats["data_sources"][source] = stats["data_sources"].get(source, 0) + 1
    
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


@router.get("/concept/{concept_id}", response_model=ConceptDetailResponse)
async def get_concept_details(
    concept_id: str,
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """
    Get detailed information about a specific concept.
    
    Args:
        concept_id: Unique identifier for the concept
        
    Returns:
        Detailed concept information including metadata, formulas, and relationships
    """
    
    # Check cache first
    cache_key = f"concept_detail_{concept_id}"
    cached_data = get_cached_data(cache_key, settings.web_cache_ttl)
    
    if cached_data:
        logging.debug(f"Returning cached concept details for {concept_id}")
        return cached_data
    
    # Load graph data
    graph_data = load_knowledge_graph()
    concepts = graph_data.get("concepts", {})
    relationships = graph_data.get("relationships", [])
    
    # Find the requested concept
    if concept_id not in concepts:
        raise HTTPException(
            status_code=404,
            detail=f"Concept '{concept_id}' not found"
        )
    
    concept = concepts[concept_id]
    
    # Find related concepts through relationships
    related_concepts = []
    for rel in relationships:
        related_concept_id = None
        relationship_type = rel.get("type", "unknown")
        
        if rel.get("source") == concept_id:
            related_concept_id = rel.get("target")
            direction = "outgoing"
        elif rel.get("target") == concept_id:
            related_concept_id = rel.get("source")
            direction = "incoming"
        
        if related_concept_id and related_concept_id in concepts:
            related_concept = concepts[related_concept_id]
            related_concepts.append({
                "id": related_concept_id,
                "name": related_concept.get("name", "Unknown"),
                "type": related_concept.get("type", "unknown"),
                "relationship_type": relationship_type,
                "direction": direction,
                "confidence": rel.get("confidence", 1.0)
            })
    
    # Build detailed response
    concept_details = {
        "id": concept_id,
        "name": concept.get("name", "Unknown"),
        "concept_type": concept.get("type", "unknown"),
        "description": concept.get("description", ""),
        "definition": concept.get("definition", ""),
        "notation": concept.get("notation", ""),
        "latex": concept.get("latex", ""),
        "examples": concept.get("examples", []),
        "applications": concept.get("applications", []),
        "prerequisites": concept.get("prerequisites", []),
        "related_formulas": concept.get("related_formulas", []),
        "complexity_level": concept.get("complexity_level", ""),
        "domain": concept.get("domain", ""),
        "keywords": concept.get("keywords", []),
        "external_links": concept.get("external_links", {}),
        "aliases": concept.get("aliases", []),
        "properties": concept.get("properties", {}),
        "source_document": concept.get("source_document", ""),
        "source_page": concept.get("source_page"),
        "confidence": concept.get("confidence", 1.0),
        "created_at": concept.get("created_at", ""),
        "updated_at": concept.get("updated_at", ""),
        "related_concepts": related_concepts
    }
    
    # Cache the response
    set_cached_data(cache_key, concept_details)
    
    logging.info(f"Served concept details for: {concept_id}")
    return concept_details


@router.get("/concepts/search", response_model=ConceptSearchResponse)
async def search_concepts(
    q: str,
    concept_type: Optional[str] = None,
    domain: Optional[str] = None,
    complexity: Optional[str] = None,
    limit: int = 20,
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """
    Search for concepts by name, keywords, or other criteria.
    
    Args:
        q: Search query string
        concept_type: Filter by concept type (optional)
        domain: Filter by domain (optional)
        complexity: Filter by complexity level (optional)
        limit: Maximum number of results to return
        
    Returns:
        List of matching concepts with summary information
    """
    
    # Check cache first
    cache_key = f"concept_search_{q}_{concept_type}_{domain}_{complexity}_{limit}"
    cached_data = get_cached_data(cache_key, settings.web_cache_ttl)
    
    if cached_data:
        logging.debug(f"Returning cached search results for: {q}")
        return cached_data
    
    # Load graph data
    graph_data = load_knowledge_graph()
    concepts = graph_data.get("concepts", {})
    
    # Perform search
    matching_concepts = []
    query_lower = q.lower()
    
    for concept_id, concept in concepts.items():
        # Check if concept matches search criteria
        matches = False
        
        # Search in name
        if query_lower in concept.get("name", "").lower():
            matches = True
        
        # Search in description
        elif query_lower in concept.get("description", "").lower():
            matches = True
        
        # Search in keywords
        elif any(query_lower in keyword.lower() for keyword in concept.get("keywords", [])):
            matches = True
        
        # Search in aliases
        elif any(query_lower in alias.lower() for alias in concept.get("aliases", [])):
            matches = True
        
        # Apply filters
        if matches:
            if concept_type and concept.get("type") != concept_type:
                matches = False
            if domain and concept.get("domain") != domain:
                matches = False
            if complexity and concept.get("complexity_level") != complexity:
                matches = False
        
        if matches:
            matching_concepts.append({
                "id": concept_id,
                "name": concept.get("name", "Unknown"),
                "type": concept.get("type", "unknown"),
                "description": concept.get("description", ""),
                "domain": concept.get("domain", ""),
                "complexity_level": concept.get("complexity_level", ""),
                "confidence": concept.get("confidence", 1.0)
            })
    
    # Sort by confidence and limit results
    matching_concepts.sort(key=lambda x: x["confidence"], reverse=True)
    limited_concepts = matching_concepts[:limit]
    
    search_results = {
        "concepts": limited_concepts,
        "total_count": len(matching_concepts),
        "query": q
    }
    
    # Cache the response
    set_cached_data(cache_key, search_results)
    
    logging.info(f"Served search results for '{q}': {len(limited_concepts)} concepts")
    return search_results


@router.get("/concepts/types")
async def get_concept_types(
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """
    Get all available concept types and their counts.
    
    Returns:
        Dictionary of concept types with counts and metadata
    """
    
    # Check cache first
    cache_key = "concept_types"
    cached_data = get_cached_data(cache_key, settings.web_cache_ttl)
    
    if cached_data:
        return cached_data
    
    # Load graph data
    graph_data = load_knowledge_graph()
    concepts = graph_data.get("concepts", {})
    
    # Count types and collect metadata
    type_info = {}
    for concept in concepts.values():
        concept_type = concept.get("type", "unknown")
        domain = concept.get("domain", "")
        
        if concept_type not in type_info:
            type_info[concept_type] = {
                "count": 0,
                "domains": set(),
                "complexity_levels": set()
            }
        
        type_info[concept_type]["count"] += 1
        if domain:
            type_info[concept_type]["domains"].add(domain)
        
        complexity = concept.get("complexity_level")
        if complexity:
            type_info[concept_type]["complexity_levels"].add(complexity)
    
    # Convert sets to lists for JSON serialization
    for type_data in type_info.values():
        type_data["domains"] = list(type_data["domains"])
        type_data["complexity_levels"] = list(type_data["complexity_levels"])
    
    # Cache the response
    set_cached_data(cache_key, type_info)
    
    return type_info


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