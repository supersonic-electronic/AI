"""
External ontology connectors for DBpedia, Wikidata, and other knowledge bases.

This module provides interfaces to external knowledge bases for concept enrichment
and relationship discovery in the financial mathematics domain.
"""

import logging
import re
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from abc import ABC, abstractmethod
import time

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    from SPARQLWrapper import SPARQLWrapper, JSON
    HAS_SPARQL = True
except ImportError:
    HAS_SPARQL = False

from .concept_cache import ConceptCache
from .ontology import Concept, ConceptType
from src.settings import Settings


@dataclass
class ExternalConceptData:
    """Data structure for external concept information."""
    external_id: str
    source: str
    label: str
    description: Optional[str] = None
    aliases: List[str] = None
    properties: Dict[str, Any] = None
    related_concepts: List[str] = None
    confidence: float = 0.0
    
    def __post_init__(self):
        if self.aliases is None:
            self.aliases = []
        if self.properties is None:
            self.properties = {}
        if self.related_concepts is None:
            self.related_concepts = []


class ExternalOntologyConnector(ABC):
    """Abstract base class for external ontology connectors."""
    
    def __init__(self, settings: Settings, cache: ConceptCache):
        self.settings = settings
        self.cache = cache
        self.logger = logging.getLogger(__name__)
        self.session = None
        
        if HAS_REQUESTS:
            self.session = requests.Session()
            self.session.headers.update({
                'User-Agent': 'AI-Portfolio-Optimizer/1.0 (https://github.com/your-repo)'
            })
    
    @abstractmethod
    def search_concept(self, concept_name: str, concept_type: Optional[ConceptType] = None) -> List[ExternalConceptData]:
        """Search for concepts in the external ontology."""
        pass
    
    @abstractmethod
    def get_concept_details(self, external_id: str) -> Optional[ExternalConceptData]:
        """Get detailed information about a specific concept."""
        pass
    
    @abstractmethod
    def get_related_concepts(self, external_id: str) -> List[ExternalConceptData]:
        """Get concepts related to a given concept."""
        pass
    
    def enrich_concept(self, concept: Concept) -> Concept:
        """Enrich a concept with external ontology data."""
        # Check cache first
        cache_key = f"{self.__class__.__name__}_{concept.name}"
        if cached_data := self.cache.get(cache_key):
            return self._apply_enrichment(concept, cached_data)
        
        # Search external ontology
        external_results = self.search_concept(concept.name, concept.concept_type)
        
        if external_results:
            # Use the best match (first result)
            best_match = external_results[0]
            
            # Cache the result
            self.cache.set(cache_key, best_match)
            
            # Apply enrichment
            return self._apply_enrichment(concept, best_match)
        
        return concept
    
    def _apply_enrichment(self, concept: Concept, external_data: ExternalConceptData) -> Concept:
        """Apply external data to enrich a concept."""
        # Add external description if concept doesn't have one
        if not concept.description and external_data.description:
            concept.description = external_data.description
        
        # Add external aliases
        concept.aliases.update(external_data.aliases)
        
        # Add external properties
        concept.properties.update({
            'external_id': external_data.external_id,
            'external_source': external_data.source,
            'external_confidence': external_data.confidence,
            **external_data.properties
        })
        
        # Increase confidence if external match is found
        if external_data.confidence > 0.5:
            concept.confidence = min(1.0, concept.confidence + 0.1)
        
        return concept


class DBpediaConnector(ExternalOntologyConnector):
    """Connector for DBpedia knowledge base."""
    
    def __init__(self, settings: Settings, cache: ConceptCache):
        super().__init__(settings, cache)
        self.sparql_endpoint = "https://dbpedia.org/sparql"
        self.lookup_endpoint = "https://lookup.dbpedia.org/api/search"
        
        if HAS_SPARQL:
            self.sparql = SPARQLWrapper(self.sparql_endpoint)
            self.sparql.setReturnFormat(JSON)
    
    def search_concept(self, concept_name: str, concept_type: Optional[ConceptType] = None) -> List[ExternalConceptData]:
        """Search for concepts in DBpedia."""
        if not HAS_REQUESTS:
            self.logger.warning("requests library not available for DBpedia search")
            return []
        
        try:
            # Use DBpedia Lookup API
            params = {
                'label': concept_name,
                'format': 'json',
                'maxResults': 5
            }
            
            # Add type filter if specified
            if concept_type:
                type_filter = self._map_concept_type_to_dbpedia_class(concept_type)
                if type_filter:
                    params['type'] = type_filter
            
            response = self.session.get(self.lookup_endpoint, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            for item in data.get('docs', []):
                external_data = ExternalConceptData(
                    external_id=item.get('resource', [{}])[0].get('uri', ''),
                    source='dbpedia',
                    label=item.get('label', [concept_name])[0],
                    description=item.get('comment', [{}])[0].get('value', ''),
                    aliases=item.get('redirect', []),
                    properties={
                        'categories': item.get('category', []),
                        'types': item.get('type', [])
                    },
                    confidence=float(item.get('score', 0.0))
                )
                results.append(external_data)
            
            return results
            
        except Exception as e:
            self.logger.error(f"DBpedia search failed for '{concept_name}': {e}")
            return []
    
    def get_concept_details(self, external_id: str) -> Optional[ExternalConceptData]:
        """Get detailed information about a DBpedia concept."""
        if not HAS_SPARQL:
            self.logger.warning("SPARQLWrapper not available for DBpedia details")
            return None
        
        try:
            query = f"""
            SELECT ?label ?comment ?type ?category WHERE {{
                <{external_id}> rdfs:label ?label ;
                               rdfs:comment ?comment ;
                               rdf:type ?type ;
                               dct:subject ?category .
                FILTER(LANG(?label) = "en")
                FILTER(LANG(?comment) = "en")
            }}
            LIMIT 10
            """
            
            self.sparql.setQuery(query)
            results = self.sparql.query().convert()
            
            if results['results']['bindings']:
                binding = results['results']['bindings'][0]
                
                return ExternalConceptData(
                    external_id=external_id,
                    source='dbpedia',
                    label=binding.get('label', {}).get('value', ''),
                    description=binding.get('comment', {}).get('value', ''),
                    properties={
                        'types': [b.get('type', {}).get('value', '') for b in results['results']['bindings']],
                        'categories': [b.get('category', {}).get('value', '') for b in results['results']['bindings']]
                    },
                    confidence=0.8
                )
            
            return None
            
        except Exception as e:
            self.logger.error(f"DBpedia details failed for '{external_id}': {e}")
            return None
    
    def get_related_concepts(self, external_id: str) -> List[ExternalConceptData]:
        """Get concepts related to a DBpedia concept."""
        if not HAS_SPARQL:
            return []
        
        try:
            query = f"""
            SELECT ?related ?label ?comment WHERE {{
                {{
                    <{external_id}> ?p ?related .
                    ?related rdfs:label ?label ;
                             rdfs:comment ?comment .
                }}
                UNION
                {{
                    ?related ?p <{external_id}> .
                    ?related rdfs:label ?label ;
                             rdfs:comment ?comment .
                }}
                FILTER(LANG(?label) = "en")
                FILTER(LANG(?comment) = "en")
                FILTER(isURI(?related))
            }}
            LIMIT 10
            """
            
            self.sparql.setQuery(query)
            results = self.sparql.query().convert()
            
            related_concepts = []
            for binding in results['results']['bindings']:
                related_data = ExternalConceptData(
                    external_id=binding.get('related', {}).get('value', ''),
                    source='dbpedia',
                    label=binding.get('label', {}).get('value', ''),
                    description=binding.get('comment', {}).get('value', ''),
                    confidence=0.6
                )
                related_concepts.append(related_data)
            
            return related_concepts
            
        except Exception as e:
            self.logger.error(f"DBpedia related concepts failed for '{external_id}': {e}")
            return []
    
    def _map_concept_type_to_dbpedia_class(self, concept_type: ConceptType) -> Optional[str]:
        """Map internal concept types to DBpedia classes."""
        type_mapping = {
            ConceptType.EQUATION: 'dbo:Equation',
            ConceptType.FORMULA: 'dbo:Formula',
            ConceptType.FUNCTION: 'dbo:Function',
            ConceptType.THEOREM: 'dbo:Theorem',
            ConceptType.ALGORITHM: 'dbo:Algorithm',
            ConceptType.METHODOLOGY: 'dbo:Method',
            ConceptType.METRIC: 'dbo:Measurement',
            ConceptType.MODEL: 'dbo:Model',
        }
        return type_mapping.get(concept_type)


class WikidataConnector(ExternalOntologyConnector):
    """Connector for Wikidata knowledge base."""
    
    def __init__(self, settings: Settings, cache: ConceptCache):
        super().__init__(settings, cache)
        self.sparql_endpoint = "https://query.wikidata.org/sparql"
        self.search_endpoint = "https://www.wikidata.org/w/api.php"
        
        if HAS_SPARQL:
            self.sparql = SPARQLWrapper(self.sparql_endpoint)
            self.sparql.setReturnFormat(JSON)
    
    def search_concept(self, concept_name: str, concept_type: Optional[ConceptType] = None) -> List[ExternalConceptData]:
        """Search for concepts in Wikidata."""
        if not HAS_REQUESTS:
            self.logger.warning("requests library not available for Wikidata search")
            return []
        
        try:
            # Use Wikidata API search
            params = {
                'action': 'wbsearchentities',
                'search': concept_name,
                'language': 'en',
                'format': 'json',
                'limit': 5
            }
            
            response = self.session.get(self.search_endpoint, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            for item in data.get('search', []):
                external_data = ExternalConceptData(
                    external_id=item.get('id', ''),
                    source='wikidata',
                    label=item.get('label', concept_name),
                    description=item.get('description', ''),
                    aliases=item.get('aliases', []),
                    properties={
                        'concepturi': item.get('concepturi', ''),
                        'url': item.get('url', '')
                    },
                    confidence=0.7  # Wikidata search is generally good quality
                )
                results.append(external_data)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Wikidata search failed for '{concept_name}': {e}")
            return []
    
    def get_concept_details(self, external_id: str) -> Optional[ExternalConceptData]:
        """Get detailed information about a Wikidata concept."""
        if not HAS_SPARQL:
            self.logger.warning("SPARQLWrapper not available for Wikidata details")
            return None
        
        try:
            query = f"""
            SELECT ?label ?description ?instanceOf ?subclassOf WHERE {{
                wd:{external_id} rdfs:label ?label ;
                                schema:description ?description .
                OPTIONAL {{ wd:{external_id} wdt:P31 ?instanceOf . }}
                OPTIONAL {{ wd:{external_id} wdt:P279 ?subclassOf . }}
                FILTER(LANG(?label) = "en")
                FILTER(LANG(?description) = "en")
            }}
            LIMIT 10
            """
            
            self.sparql.setQuery(query)
            results = self.sparql.query().convert()
            
            if results['results']['bindings']:
                binding = results['results']['bindings'][0]
                
                return ExternalConceptData(
                    external_id=external_id,
                    source='wikidata',
                    label=binding.get('label', {}).get('value', ''),
                    description=binding.get('description', {}).get('value', ''),
                    properties={
                        'instanceOf': [b.get('instanceOf', {}).get('value', '') for b in results['results']['bindings']],
                        'subclassOf': [b.get('subclassOf', {}).get('value', '') for b in results['results']['bindings']]
                    },
                    confidence=0.8
                )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Wikidata details failed for '{external_id}': {e}")
            return None
    
    def get_related_concepts(self, external_id: str) -> List[ExternalConceptData]:
        """Get concepts related to a Wikidata concept."""
        if not HAS_SPARQL:
            return []
        
        try:
            query = f"""
            SELECT ?related ?label ?description WHERE {{
                {{
                    wd:{external_id} ?p ?related .
                    ?related rdfs:label ?label ;
                             schema:description ?description .
                }}
                UNION
                {{
                    ?related ?p wd:{external_id} .
                    ?related rdfs:label ?label ;
                             schema:description ?description .
                }}
                FILTER(LANG(?label) = "en")
                FILTER(LANG(?description) = "en")
                FILTER(STRSTARTS(STR(?related), "http://www.wikidata.org/entity/Q"))
            }}
            LIMIT 10
            """
            
            self.sparql.setQuery(query)
            results = self.sparql.query().convert()
            
            related_concepts = []
            for binding in results['results']['bindings']:
                # Extract Wikidata ID from URI
                uri = binding.get('related', {}).get('value', '')
                wikidata_id = uri.split('/')[-1] if uri else ''
                
                related_data = ExternalConceptData(
                    external_id=wikidata_id,
                    source='wikidata',
                    label=binding.get('label', {}).get('value', ''),
                    description=binding.get('description', {}).get('value', ''),
                    confidence=0.6
                )
                related_concepts.append(related_data)
            
            return related_concepts
            
        except Exception as e:
            self.logger.error(f"Wikidata related concepts failed for '{external_id}': {e}")
            return []


class ExternalOntologyManager:
    """Manager for multiple external ontology connectors."""
    
    def __init__(self, settings: Settings, cache: ConceptCache):
        self.settings = settings
        self.cache = cache
        self.logger = logging.getLogger(__name__)
        
        # Initialize connectors
        self.connectors = {}
        
        if getattr(settings, 'enable_dbpedia', True):
            self.connectors['dbpedia'] = DBpediaConnector(settings, cache)
        
        if getattr(settings, 'enable_wikidata', True):
            self.connectors['wikidata'] = WikidataConnector(settings, cache)
    
    def enrich_concept(self, concept: Concept) -> Concept:
        """Enrich a concept using all available external ontologies."""
        enriched_concept = concept
        
        for connector_name, connector in self.connectors.items():
            try:
                enriched_concept = connector.enrich_concept(enriched_concept)
                self.logger.debug(f"Enriched concept '{concept.name}' with {connector_name}")
            except Exception as e:
                self.logger.error(f"Failed to enrich concept with {connector_name}: {e}")
        
        return enriched_concept
    
    def search_all_ontologies(self, concept_name: str, concept_type: Optional[ConceptType] = None) -> Dict[str, List[ExternalConceptData]]:
        """Search all external ontologies for a concept."""
        results = {}
        
        for connector_name, connector in self.connectors.items():
            try:
                results[connector_name] = connector.search_concept(concept_name, concept_type)
            except Exception as e:
                self.logger.error(f"Search failed in {connector_name}: {e}")
                results[connector_name] = []
        
        return results
    
    def get_connector(self, source: str) -> Optional[ExternalOntologyConnector]:
        """Get a specific connector by source name."""
        return self.connectors.get(source)


def get_external_ontology_manager(settings: Settings, cache: ConceptCache) -> ExternalOntologyManager:
    """Factory function to create an external ontology manager."""
    return ExternalOntologyManager(settings, cache)