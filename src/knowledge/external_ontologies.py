"""
External ontology connectors for DBpedia, Wikidata, and other knowledge bases.

This module provides interfaces to external knowledge bases for concept enrichment
and relationship discovery in the financial mathematics domain.
"""

import logging
import re
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import time

try:
    import requests
    from requests.adapters import HTTPAdapter
    from requests.packages.urllib3.util.retry import Retry
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    HTTPAdapter = None
    Retry = None

try:
    from SPARQLWrapper import SPARQLWrapper, JSON
    HAS_SPARQL = True
except ImportError:
    HAS_SPARQL = False

from .concept_cache import ConceptCache
from .ontology import Concept, ConceptType
from .utils import generate_cache_key, normalize_concept_name, get_concept_variants
from src.settings import Settings


@dataclass
class ExternalConceptData:
    """Data structure for external concept information."""
    external_id: str
    source: str
    label: str
    description: Optional[str] = None
    aliases: List[str] = field(default_factory=list)
    properties: Dict[str, Any] = field(default_factory=dict)
    related_concepts: List[str] = field(default_factory=list)
    confidence: float = 0.0


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
                'User-Agent': 'AI-Knowledge-Graph/1.0 (Educational/Research Use)',
                'Accept': 'application/json',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive'
            })
            
            # Configure retry strategy
            retry_strategy = Retry(
                total=3,  # Total number of retries
                backoff_factor=1,  # Wait 1, 2, 4 seconds between retries
                status_forcelist=[429, 500, 502, 503, 504],  # Retry on these HTTP status codes
                allowed_methods=["HEAD", "GET", "OPTIONS"],  # Only retry safe methods
                raise_on_status=False  # Don't raise exception on bad status
            )
            
            # Configure connection pooling and timeouts
            adapter = HTTPAdapter(
                max_retries=retry_strategy,
                pool_connections=10,  # Number of connection pools to cache
                pool_maxsize=10,  # Maximum number of connections to save in the pool
                pool_block=False  # Don't block when pool is full
            )
            
            # Mount adapter for both HTTP and HTTPS
            self.session.mount("http://", adapter)
            self.session.mount("https://", adapter)
    
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
        # Enhanced logging for enrichment process
        logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Check cache first
        cache_key = generate_cache_key(self.__class__.__name__, concept.name)
        logger.debug(f"Enriching concept '{concept.name}' (type: {concept.concept_type}, cache_key: {cache_key})")
        
        if cached_data := self.cache.get(cache_key):
            if isinstance(cached_data, ExternalConceptData):
                logger.debug(f"Using cached enrichment for '{concept.name}': {cached_data.label}")
                return self._apply_enrichment(concept, cached_data)
            else:
                # Invalid cache data, remove it
                logger.warning(f"Invalid cache data for '{concept.name}', removing cache entry")
                self.cache.delete(cache_key)
        
        # Search external ontology
        logger.debug(f"Searching external ontology for '{concept.name}'...")
        external_results = self.search_concept(concept.name, concept.concept_type)
        logger.debug(f"Found {len(external_results) if external_results else 0} external results for '{concept.name}'")
        
        if external_results:
            # Find the best match based on concept type and relevance
            best_match = self._find_best_match(external_results, concept)
            
            # Apply minimum relevance threshold based on calculated match score
            if best_match:
                match_score = self._calculate_match_score(best_match, concept)
                # Lower threshold for mathematical/statistical concepts to capture valid matches
                min_threshold = 0.12  # Minimum calculated match score for concepts
                logger.debug(f"Best match for '{concept.name}': {best_match.label} (score: {match_score:.3f}, threshold: {min_threshold})")
                
                if match_score < min_threshold:
                    logger.info(f"Enrichment failed for '{concept.name}': best match '{best_match.label}' below threshold (score: {match_score:.3f} < {min_threshold})")
                    best_match = None
                else:
                    logger.debug(f"Enrichment approved for '{concept.name}': using '{best_match.label}' (score: {match_score:.3f})")
            else:
                logger.info(f"Enrichment failed for '{concept.name}': no valid matches found")
            
            # Get related concepts for enhanced metadata
            if best_match and best_match.external_id:
                try:
                    related_concepts = self.get_related_concepts(best_match.external_id)
                    if related_concepts:
                        # Filter and limit related concepts to relevant financial ones only
                        related_names = []
                        
                        # Enhanced filtering keywords for related concepts
                        filter_keywords = [
                            # Geographic terms
                            'district', 'county', 'city', 'town', 'village', 'municipality', 'region',
                            'state', 'province', 'country', 'nation', 'island', 'river', 'mountain',
                            'lake', 'ocean', 'sea', 'forest', 'park', 'street', 'road', 'avenue',
                            
                            # Non-financial organizations
                            'university', 'college', 'school', 'hospital', 'church', 'museum',
                            'library', 'airport', 'station', 'bridge', 'building', 'tower',
                            
                            # Entertainment and media
                            'film', 'movie', 'album', 'song', 'band', 'artist', 'actor', 'actress',
                            'director', 'producer', 'television', 'tv show', 'game', 'sport',
                            
                            # People and biographical
                            'born', 'died', 'death', 'birth', 'family', 'person', 'people'
                        ]
                        
                        for related in related_concepts[:10]:  # Check more candidates
                            # Extract clean name from label or external_id
                            if related.label:
                                candidate_name = related.label.lower()
                                display_name = related.label
                            elif related.external_id:
                                name = related.external_id.split('/')[-1].replace('_', ' ')
                                candidate_name = name.lower()
                                display_name = name
                            else:
                                continue
                            
                            # Filter out irrelevant concepts
                            is_relevant = True
                            for filter_term in filter_keywords:
                                if filter_term in candidate_name:
                                    is_relevant = False
                                    break
                            
                            # Check for unwanted disambiguations
                            if '(' in candidate_name:
                                unwanted_disambig = ['city', 'town', 'film', 'album', 'song', 'band']
                                if any(f'({unwanted})' in candidate_name for unwanted in unwanted_disambig):
                                    is_relevant = False
                            
                            if is_relevant and len(related_names) < 5:  # Keep only 5 relevant ones
                                related_names.append(display_name)
                        
                        # Add filtered related concepts to best_match properties
                        best_match.properties['related_external_concepts'] = related_names
                except Exception as e:
                    self.logger.warning(f"Failed to get related concepts for {best_match.external_id}: {e}")
            
            # Cache the result
            self.cache.set(cache_key, best_match)
            logger.debug(f"Cached enrichment result for '{concept.name}': {best_match.label if best_match else 'None'}")
            
            # Apply enrichment only if we have a valid match
            if best_match:
                enriched_concept = self._apply_enrichment(concept, best_match)
                logger.info(f"Successfully enriched '{concept.name}' with external data from {best_match.source}")
                return enriched_concept
        else:
            # No external results found
            logger.info(f"No external results found for '{concept.name}' - concept will remain unenriched")
        
        logger.debug(f"Returning unenriched concept: '{concept.name}'")
        return concept
    
    def _find_best_match(self, external_results: List[ExternalConceptData], concept: Concept) -> ExternalConceptData:
        """Find the best match from external results based on concept type and relevance."""
        if not external_results:
            return None
        
        # Score each result
        scored_results = []
        for result in external_results:
            score = self._calculate_match_score(result, concept)
            scored_results.append((score, result))
        
        # Sort by score (highest first) and return the best match
        scored_results.sort(key=lambda x: x[0], reverse=True)
        
        # Debug logging
        if len(scored_results) > 1:
            self.logger.debug(f"Top matches for '{concept.name}':")
            for i, (score, result) in enumerate(scored_results[:3]):
                self.logger.debug(f"  {i+1}. {result.label} (score: {score:.3f})")
        
        return scored_results[0][1]
    
    def _calculate_match_score(self, external_data: ExternalConceptData, concept: Concept) -> float:
        """Calculate a relevance score for an external match with enhanced domain filtering."""
        score = external_data.confidence
        
        # Enhanced domain-aware matching
        text_to_check = (external_data.description or '').lower()
        label_text = (external_data.label or '').lower()
        properties = external_data.properties or {}
        categories = properties.get('categories', [])
        category_text = ' '.join(str(cat) for cat in categories).lower()
        
        # Financial domain keywords (expanded and weighted)
        financial_keywords = {
            # Core investment and portfolio management terms
            'investment': 0.9, 'portfolio': 0.9, 'asset management': 0.9, 'fund management': 0.8,
            'wealth management': 0.8, 'institutional investing': 0.8, 'asset allocation': 0.9,
            'portfolio optimization': 0.9, 'investment strategy': 0.8, 'investment policy': 0.8,
            
            # Portfolio theory and models
            'modern portfolio theory': 0.9, 'markowitz': 0.9, 'efficient frontier': 0.9,
            'capital asset pricing model': 0.9, 'capm': 0.9, 'arbitrage pricing theory': 0.8,
            'black-scholes': 0.9, 'fama-french': 0.8, 'factor models': 0.8,
            
            # Risk and return metrics
            'risk management': 1.0, 'risk assessment': 0.9, 'value at risk': 0.9,
            'expected return': 0.9, 'risk-adjusted return': 0.9, 'sharpe ratio': 0.9,
            'information ratio': 0.8, 'treynor ratio': 0.8, 'jensen alpha': 0.8,
            'tracking error': 0.8, 'beta': 0.8, 'alpha': 0.8,
            
            # Statistical measures in finance
            'volatility': 0.8, 'variance': 0.8, 'covariance': 0.8, 'correlation': 0.8,
            'standard deviation': 0.8, 'skewness': 0.7, 'kurtosis': 0.7, 'drawdown': 0.7,
            
            # Traditional finance terms
            'finance': 0.7, 'financial': 0.7, 'capital': 0.7, 'market': 0.6,
            'securities': 0.8, 'equity': 0.8, 'bond': 0.8, 'derivative': 0.9,
            'option': 0.7, 'futures': 0.8, 'hedge': 0.8, 'arbitrage': 0.9,
            'yield': 0.6, 'return': 0.7, 'interest': 0.5, 'rate': 0.5
        }
        
        # Investment management acronyms with their full forms for better matching
        financial_acronyms = {
            'capm': 'capital asset pricing model',
            'apt': 'arbitrage pricing theory', 
            'var': 'value at risk',
            'cvar': 'conditional value at risk',
            'etf': 'exchange traded fund',
            'reit': 'real estate investment trust',
            'mpt': 'modern portfolio theory',
            'aum': 'assets under management',
            'nav': 'net asset value',
            'pe': 'price to earnings',
            'pb': 'price to book',
            'roe': 'return on equity',
            'roa': 'return on assets',
            'wacc': 'weighted average cost of capital'
        }
        
        # Mathematical domain keywords (enhanced for statistical concepts)
        mathematical_keywords = {
            'optimization': 0.9, 'algorithm': 0.7, 'mathematical': 0.8,
            'statistics': 0.9, 'statistical': 0.9, 'probability': 0.9, 'regression': 0.7,
            'correlation': 0.8, 'variance': 0.9, 'covariance': 0.9, 'deviation': 0.8,
            'stochastic': 0.9, 'monte carlo': 1.0, 'simulation': 0.7,
            'calculus': 0.6, 'matrix': 0.6, 'linear algebra': 0.7,
            'numerical': 0.7, 'computational': 0.7,
            # Additional statistical terms
            'distribution': 0.8, 'random variable': 0.9, 'expectation': 0.8,
            'standard deviation': 0.9, 'moment': 0.8, 'dispersion': 0.8,
            'sampling': 0.7, 'inference': 0.8, 'hypothesis testing': 0.8,
            'analysis of variance': 0.9, 'anova': 0.9, 'squared deviation': 0.8,
            'central moment': 0.8, 'population': 0.6, 'sample': 0.6
        }
        
        # Enhanced irrelevant domain filtering
        irrelevant_keywords = {
            # Entertainment and media
            'video game': -1.0, 'movie': -0.8, 'film': -0.8, 'television': -0.8, 'tv show': -0.8,
            'music': -0.6, 'album': -0.8, 'song': -0.8, 'band': -0.8, 'artist': -0.6,
            
            # Sports and recreation
            'sports': -0.8, 'football': -0.8, 'basketball': -0.8, 'baseball': -0.8, 'soccer': -0.8,
            'tennis': -0.8, 'golf': -0.8, 'olympics': -0.8, 'athlete': -0.8, 'team': -0.6,
            
            # Geography and locations
            'geography': -0.8, 'city': -0.9, 'town': -0.9, 'village': -0.9, 'county': -0.9,
            'state': -0.7, 'province': -0.8, 'region': -0.7, 'district': -0.9, 'municipality': -0.9,
            'country': -0.6, 'nation': -0.6, 'continent': -0.8, 'island': -0.8, 'river': -0.9,
            'mountain': -0.9, 'lake': -0.9, 'ocean': -0.9, 'sea': -0.8, 'forest': -0.8,
            'park': -0.7, 'street': -0.8, 'road': -0.8, 'avenue': -0.8, 'boulevard': -0.8,
            
            # Sciences (non-financial)
            'biology': -0.6, 'chemistry': -0.6, 'physics': -0.4, 'medicine': -0.5,
            'astronomy': -0.7, 'geology': -0.7, 'anthropology': -0.6, 'archaeology': -0.6,
            
            # Humanities
            'history': -0.5, 'literature': -0.6, 'art': -0.6, 'philosophy': -0.4,
            'religion': -0.6, 'theology': -0.6, 'mythology': -0.7,
            
            # Politics and government
            'politics': -0.5, 'politician': -0.7, 'government': -0.4, 'military': -0.6,
            'war': -0.7, 'battle': -0.8, 'army': -0.7, 'navy': -0.7,
            
            # People and biographical
            'born': -0.8, 'died': -0.8, 'death': -0.8, 'birth': -0.8, 'family': -0.6,
            'person': -0.5, 'people': -0.5, 'biography': -0.7, 'life': -0.4,
            
            # Gender-related terms (context-sensitive)
            'gender identity': -1.2, 'gender expression': -1.2, 'gender nonconformity': -1.2,
            'gender roles': -1.0, 'transgender': -1.0, 'non-binary': -1.0, 'androgyny': -1.0,
        }
        
        # Geographic location indicators (stronger penalties)
        geographic_indicators = [
            'located in', 'situated in', 'capital of', 'city in', 'town in', 'village in',
            'county in', 'state in', 'province in', 'region of', 'district of',
            'municipality in', 'part of', 'subdivision of', 'administrative'
        ]
        
        # Domain matching for financial concepts
        if concept.concept_type in [ConceptType.PORTFOLIO, ConceptType.ASSET, ConceptType.RISK, ConceptType.RETURN, ConceptType.STRATEGY, ConceptType.MODEL, ConceptType.OPTIMIZATION, ConceptType.AUTHOR, ConceptType.METHODOLOGY]:
            # Check for financial keywords in label (highest priority)
            for keyword, weight in financial_keywords.items():
                if keyword in label_text:
                    score += weight * 0.7  # Label matches are highly weighted
                elif keyword in text_to_check:
                    score += weight * 0.5  # Description matches
                elif keyword in category_text:
                    score += weight * 0.3  # Category matches
            
            # Check for mathematical keywords (complementary for financial concepts)
            for keyword, weight in mathematical_keywords.items():
                if keyword in label_text:
                    score += weight * 0.4
                elif keyword in text_to_check:
                    score += weight * 0.3
                elif keyword in category_text:
                    score += weight * 0.2
        
        # Domain matching for mathematical concepts  
        elif concept.concept_type in [ConceptType.METHOD, ConceptType.CONCEPT, ConceptType.METRIC, ConceptType.STATISTICAL_MEASURE, ConceptType.FUNCTION, ConceptType.FORMULA, ConceptType.EQUATION]:
            # Prioritize mathematical keywords
            for keyword, weight in mathematical_keywords.items():
                if keyword in label_text:
                    score += weight * 0.7
                elif keyword in text_to_check:
                    score += weight * 0.5
                elif keyword in category_text:
                    score += weight * 0.3
                    
            # Financial keywords still relevant but lower weight
            for keyword, weight in financial_keywords.items():
                if keyword in label_text:
                    score += weight * 0.3
                elif keyword in text_to_check:
                    score += weight * 0.2
        
        # Apply penalties for irrelevant content
        for keyword, penalty in irrelevant_keywords.items():
            if keyword in label_text:
                score += penalty * 0.8  # Heavy penalty for irrelevant labels
            elif keyword in text_to_check:
                score += penalty * 0.5
            elif keyword in category_text:
                score += penalty * 0.3
        
        # Handle acronyms by checking if concept name is an acronym and needs financial context
        concept_name_lower = concept.name.lower()
        if concept_name_lower in financial_acronyms:
            full_form = financial_acronyms[concept_name_lower]
            if full_form.lower() in label_text or full_form.lower() in text_to_check:
                score += 1.5  # Strong boost for acronym matches
                logging.debug(f"Acronym match: {concept.name} -> {full_form}")
        
        # Enhanced disambiguation preferences for investment management
        if '(finance)' in label_text or '(financial)' in label_text:
            score += 2.5  # Strong boost for financial disambiguation
            self.logger.debug(f"Applied financial disambiguation boost (+2.5) to '{external_data.label}'")
        elif '(investment)' in label_text or '(investing)' in label_text:
            score += 1.3  # Prefer investment context
        elif '(portfolio)' in label_text or '(asset management)' in label_text:
            score += 1.4  # Highest preference for portfolio management
        elif '(economics)' in label_text or '(economic)' in label_text:
            score += 0.8
        elif '(business)' in label_text:
            score += 0.6
        elif '(management)' in label_text:
            score += 0.7
        
        # Apply heavy penalties for geographic locations
        for geo_indicator in geographic_indicators:
            if geo_indicator in text_to_check:
                score -= 1.2  # Heavy penalty for geographic descriptions
                logging.debug(f"Geographic penalty applied for '{geo_indicator}' in {concept.name}")
        
        # Penalize clearly unrelated disambiguations
        unwanted_disambig = ['(video game)', '(film)', '(album)', '(song)', '(TV)', '(band)', '(company)', 
                            '(city)', '(town)', '(village)', '(county)', '(district)', '(municipality)',
                            '(river)', '(mountain)', '(lake)', '(island)', '(park)', '(road)']
        for unwanted in unwanted_disambig:
            if unwanted in label_text:
                score -= 1.0  # Increased penalty
        
        # Category-based scoring for mathematical/statistical concepts
        mathematical_categories = {
            'statistical_deviation_and_dispersion': 1.0,
            'moment_(mathematics)': 1.0,
            'statistical_tests': 0.9,
            'analysis_of_variance': 0.9,
            'parametric_statistics': 0.8,
            'probability_theory': 0.9,
            'statistical_inference': 0.8,
            'descriptive_statistics': 0.8,
            'mathematical_analysis': 0.7,
            'mathematical_statistics': 0.9
        }
        
        # Check categories for mathematical content
        for category_uri in categories:
            category_name = category_uri.split('/')[-1].lower().replace('_', ' ')
            for math_cat, weight in mathematical_categories.items():
                if math_cat.replace('_', ' ') in category_name:
                    score += weight * 0.8
                    logging.debug(f"Mathematical category boost: {category_name} (+{weight * 0.8:.2f})")
                    break
        
        # Contextual disambiguation: prefer statistical variance over gender variance
        if concept.concept_type == ConceptType.METRIC and concept.name.lower() == 'variance':
            # Strong boost for statistical variance
            if 'statistical' in text_to_check or 'probability' in text_to_check:
                score += 1.5
                logging.debug(f"Statistical variance boost applied (+1.5)")
            elif 'random variable' in text_to_check or 'squared deviation' in text_to_check:
                score += 1.3
                logging.debug(f"Statistical context boost applied (+1.3)")
            elif 'expectation' in text_to_check or 'mean' in text_to_check:
                score += 1.0
                logging.debug(f"Statistical mean context boost applied (+1.0)")
            
            # Heavy penalty for gender-related variance
            if 'gender' in label_text or 'gender' in text_to_check:
                score -= 2.0
                logging.debug(f"Gender variance penalty applied (-2.0)")
        
        # Ensure score doesn't go below 0
        return max(0.0, score)
    
    def _apply_enrichment(self, concept: Concept, external_data: ExternalConceptData) -> Concept:
        """Apply external data to enrich a concept with domain filtering."""
        # Add external description if concept doesn't have one
        if not concept.description and external_data.description:
            concept.description = external_data.description
        
        # Filter and add relevant external aliases
        if external_data.aliases:
            filtered_aliases = self._filter_domain_relevant_terms(external_data.aliases, is_alias=True)
            if isinstance(external_data.aliases, list):
                concept.aliases.update(filtered_aliases)
            elif isinstance(external_data.aliases, str) and external_data.aliases in filtered_aliases:
                concept.aliases.add(external_data.aliases)
            else:
                # Handle other iterables
                try:
                    concept.aliases.update(filtered_aliases)
                except TypeError:
                    pass
        
        # Filter categories for domain relevance
        filtered_properties = external_data.properties.copy()
        if 'categories' in filtered_properties:
            filtered_categories = self._filter_domain_relevant_terms(filtered_properties['categories'], is_category=True)
            filtered_properties['categories'] = filtered_categories
        
        # Add external properties with filtered content
        concept.properties.update({
            'external_id': external_data.external_id,
            'external_source': external_data.source,
            'external_confidence': external_data.confidence,
            **filtered_properties
        })
        
        # Increase confidence if external match is found
        if external_data.confidence > 0.5:
            concept.confidence = min(1.0, concept.confidence + 0.1)
        
        return concept
    
    def _filter_domain_relevant_terms(self, terms, is_alias=False, is_category=False):
        """Filter terms to keep only domain-relevant aliases and categories."""
        if not terms:
            return []
        
        if isinstance(terms, str):
            terms = [terms]
        
        # Financial and mathematical domain keywords for filtering
        relevant_keywords = {
            # Core finance terms
            'finance', 'financial', 'economics', 'economic', 'investment', 'portfolio', 
            'market', 'trading', 'asset', 'security', 'bond', 'equity', 'stock',
            'risk', 'return', 'volatility', 'correlation', 'covariance', 'variance',
            'optimization', 'model', 'theory', 'pricing', 'valuation', 'analysis',
            
            # Mathematical and statistical terms
            'mathematics', 'mathematical', 'statistics', 'statistical', 'probability',
            'calculus', 'algebra', 'equation', 'formula', 'function', 'optimization',
            'regression', 'distribution', 'deviation', 'moment', 'estimation',
            
            # Academic and research terms
            'research', 'academic', 'university', 'professor', 'laureate', 'economics',
            'business', 'management', 'quantitative', 'empirical', 'theoretical'
        }
        
        # Terms to exclude (expanded for better filtering)
        irrelevant_keywords = {
            # Entertainment and media
            'film', 'movie', 'television', 'tv', 'show', 'series', 'actor', 'actress',
            'director', 'producer', 'music', 'album', 'song', 'band', 'artist', 
            'game', 'video game', 'gaming', 'entertainment',
            
            # Geography and locations
            'city', 'town', 'village', 'county', 'state', 'province', 'country',
            'region', 'district', 'municipality', 'island', 'river', 'mountain',
            'lake', 'ocean', 'sea', 'forest', 'park', 'street', 'road', 'avenue',
            'geography', 'geographical', 'location', 'place',
            
            # Biology and nature
            'biology', 'biological', 'species', 'animal', 'plant', 'organism',
            'gene', 'protein', 'cell', 'molecule', 'medical', 'medicine', 'health',
            'disease', 'treatment', 'therapy', 'pharmaceutical', 'drug',
            
            # Other sciences
            'astronomy', 'astronomical', 'star', 'planet', 'galaxy', 'space',
            'physics', 'physical', 'chemistry', 'chemical', 'geology', 'geological',
            
            # Sports and recreation
            'sport', 'sports', 'football', 'basketball', 'baseball', 'soccer',
            'tennis', 'golf', 'athlete', 'team', 'game', 'competition',
            
            # Technology (non-financial)
            'software', 'hardware', 'computer', 'programming', 'internet',
            'website', 'application', 'technology'
        }
        
        filtered_terms = []
        
        for term in terms:
            if not term:
                continue
                
            # Clean the term (remove URLs, prefixes, etc.)
            clean_term = term
            if isinstance(term, str):
                # Extract category name from DBpedia URLs
                if term.startswith('http://dbpedia.org/resource/Category:'):
                    clean_term = term.split('Category:')[-1].replace('_', ' ').lower()
                elif term.startswith('http://'):
                    clean_term = term.split('/')[-1].replace('_', ' ').lower()
                else:
                    clean_term = term.lower()
            
            # Check if term is relevant to financial/mathematical domain
            is_relevant = False
            is_irrelevant = False
            
            # Check for relevant keywords
            for keyword in relevant_keywords:
                if keyword in clean_term:
                    is_relevant = True
                    break
            
            # Check for irrelevant keywords (override relevance)
            for keyword in irrelevant_keywords:
                if keyword in clean_term:
                    is_irrelevant = True
                    break
            
            # Special handling for specific financial concepts
            if any(fin_term in clean_term for fin_term in ['nobel', 'economics', 'finance', 'portfolio', 'investment', 'risk', 'return']):
                is_relevant = True
                is_irrelevant = False
            
            # For categories, be more restrictive
            if is_category:
                # Only include if strongly relevant and not irrelevant
                if is_relevant and not is_irrelevant:
                    filtered_terms.append(term)
            else:
                # For aliases, be slightly more permissive but still filter
                if is_relevant and not is_irrelevant:
                    filtered_terms.append(term)
                elif not is_irrelevant and len(clean_term.split()) <= 3:  # Short terms that aren't obviously irrelevant
                    filtered_terms.append(term)
        
        return filtered_terms[:10]  # Limit to prevent overwhelming
    
    def close(self):
        """Close the HTTP session and clean up resources."""
        if self.session:
            self.session.close()


class DBpediaConnector(ExternalOntologyConnector):
    """Connector for DBpedia knowledge base."""
    
    def __init__(self, settings: Settings, cache: ConceptCache):
        super().__init__(settings, cache)
        self.sparql_endpoint = "https://dbpedia.org/sparql"
        self.lookup_endpoint = "https://lookup.dbpedia.org/api/search"
        
        # Rate limiting settings
        self.last_request_time = 0
        self.min_request_interval = 0.5  # Minimum 500ms between requests
        
        # Financial acronym and term mapping for better search results
        self.financial_acronyms = {
            'capm': 'Capital Asset Pricing Model',
            'apt': 'Arbitrage Pricing Theory', 
            'var': 'Value at Risk',
            'cvar': 'Conditional Value at Risk',
            'etf': 'Exchange Traded Fund',
            'reit': 'Real Estate Investment Trust',
            'mpt': 'Modern Portfolio Theory',
            'aum': 'Assets Under Management',
            'nav': 'Net Asset Value',
            'pe': 'Price to Earnings',
            'pb': 'Price to Book',
            'roe': 'Return on Equity',
            'roa': 'Return on Assets',
            'wacc': 'Weighted Average Cost of Capital'
        }
        
        # Financial term expansions for better matching
        self.financial_term_expansions = {
            'markowitz': ['Harry Markowitz', 'Markowitz portfolio theory', 'Markowitz model'],
            'black-scholes': ['Black-Scholes model', 'Black-Scholes equation', 'Black-Scholes formula'],
            'black scholes': ['Black-Scholes model', 'Black-Scholes equation', 'Black-Scholes formula'],
            'beta': ['Beta (finance)', 'Systematic risk', 'Market beta', 'Financial beta'],
            'alpha': ['Alpha (finance)', 'Jensen alpha', 'Portfolio alpha', 'Abnormal return']
        }
        
        if HAS_SPARQL:
            self.sparql = SPARQLWrapper(self.sparql_endpoint)
            self.sparql.setReturnFormat(JSON)
    
    def search_concept(self, concept_name: str, concept_type: Optional[ConceptType] = None) -> List[ExternalConceptData]:
        """Search for concepts in DBpedia."""
        if not HAS_REQUESTS:
            self.logger.warning("requests library not available for DBpedia search")
            return []
        
        try:
            # Implement rate limiting
            current_time = time.time()
            time_since_last_request = current_time - self.last_request_time
            if time_since_last_request < self.min_request_interval:
                time.sleep(self.min_request_interval - time_since_last_request)
            
            # Financial acronym and term expansion for better DBpedia matching
            search_terms = [concept_name]
            
            # If concept is an acronym, also search for the expanded form
            if concept_name.lower() in self.financial_acronyms:
                expanded_term = self.financial_acronyms[concept_name.lower()]
                search_terms.append(expanded_term)
                self.logger.info(f"DBpedia: Expanding acronym '{concept_name}' to include '{expanded_term}'")
            
            # If concept has financial term expansions, add them
            concept_key = concept_name.lower().replace('-', ' ')
            if concept_key in self.financial_term_expansions:
                expansions = self.financial_term_expansions[concept_key]
                search_terms.extend(expansions[:2])  # Add up to 2 expansions to avoid too many requests
                self.logger.info(f"DBpedia: Expanding term '{concept_name}' to include {expansions[:2]}")
            
            all_results = []
            self.logger.info(f"DBpedia: Processing {len(search_terms)} search terms: {search_terms}")
            
            for i, search_term in enumerate(search_terms):
                self.logger.info(f"DBpedia: Searching for term {i+1}: '{search_term}'")
                
                # Rate limiting between multiple searches
                if i > 0:
                    time.sleep(0.5)
                    
                # Use DBpedia Lookup API
                params = {
                    'label': search_term,
                    'format': 'json',
                    'maxResults': 5
                }
                
                # Add type filter if specified
                if concept_type:
                    type_filter = self._map_concept_type_to_dbpedia_class(concept_type)
                    if type_filter:
                        params['type'] = type_filter
                
                # Make request with timeout and better error handling
                response = self.session.get(
                    self.lookup_endpoint, 
                    params=params, 
                    timeout=(5, 15)  # (connection timeout, read timeout)
                )
                response.raise_for_status()
                
                data = response.json()
                docs = data.get('docs', [])
                self.logger.info(f"DBpedia: Found {len(docs)} results for '{search_term}'")
                
                for item in docs:
                    # Handle array fields in DBpedia response
                    resource_list = item.get('resource', [])
                    label_list = item.get('label', [search_term])
                    comment_list = item.get('comment', [])
                    score_list = item.get('score', ['0.0'])
                    
                    # Boost confidence for expanded acronym matches
                    confidence_boost = 0.1 if i > 0 and search_term != concept_name else 0.0
                    
                    # Additional boost for financial disambiguation terms
                    label = label_list[0] if label_list else search_term
                    if ('(finance)' in label.lower() or 
                        '(financial)' in label.lower() or
                        '(investment)' in label.lower() or
                        '(economics)' in label.lower()):
                        confidence_boost += 0.5  # Strong boost for financial disambiguation
                        self.logger.info(f"DBpedia: Applied financial disambiguation boost to '{label}'")
                    
                    external_data = ExternalConceptData(
                        external_id=resource_list[0] if resource_list else '',
                        source='dbpedia',
                        label=label,
                        description=comment_list[0] if comment_list else '',
                        aliases=item.get('redirectlabel', []),
                        properties={
                            'categories': item.get('category', []),
                            'types': item.get('type', []),
                            'typeName': item.get('typeName', [])
                        },
                        confidence=(float(score_list[0]) / 10000.0 if score_list else 0.0) + confidence_boost
                    )
                    all_results.append(external_data)
                    self.logger.info(f"DBpedia: Added result '{external_data.label}' with confidence {external_data.confidence:.3f}")
            
            # Update last request time after all requests
            self.last_request_time = time.time()
            
            # Return unique results based on external_id, preferring higher confidence
            self.logger.info(f"DBpedia: Collected {len(all_results)} total results")
            
            unique_results = {}
            for result in all_results:
                if result.external_id not in unique_results or result.confidence > unique_results[result.external_id].confidence:
                    unique_results[result.external_id] = result
            
            # Sort by confidence (highest first) and take top 5
            final_results = sorted(unique_results.values(), key=lambda x: x.confidence, reverse=True)[:5]
            self.logger.info(f"DBpedia: Returning {len(final_results)} unique results (sorted by confidence)")
            
            for result in final_results:
                self.logger.info(f"DBpedia: Final result: '{result.label}' - confidence: {result.confidence:.3f}")
            
            return final_results
            
        except requests.exceptions.ConnectTimeout:
            self.logger.warning(f"DBpedia connection timeout for '{concept_name}' - service may be slow")
            return []
        except requests.exceptions.ConnectionError as e:
            self.logger.warning(f"DBpedia connection error for '{concept_name}': {str(e)[:100]}")
            return []
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                self.logger.warning(f"DBpedia rate limit exceeded for '{concept_name}'")
            else:
                self.logger.warning(f"DBpedia HTTP error {e.response.status_code} for '{concept_name}'")
            return []
        except requests.exceptions.Timeout:
            self.logger.warning(f"DBpedia read timeout for '{concept_name}' - response too slow")
            return []
        except requests.exceptions.RequestException as e:
            self.logger.warning(f"DBpedia request failed for '{concept_name}': {type(e).__name__}")
            return []
        except (ValueError, KeyError) as e:
            self.logger.warning(f"DBpedia response parsing error for '{concept_name}': {str(e)[:100]}")
            return []
        except Exception as e:
            self.logger.error(f"Unexpected DBpedia error for '{concept_name}': {type(e).__name__}: {str(e)[:100]}")
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
                external_id = item.get('id', '')
                
                # Get detailed information including instanceOf and subclassOf
                detailed_data = self.get_concept_details(external_id) if external_id else None
                
                if detailed_data:
                    # Use the detailed data which includes semantic metadata
                    results.append(detailed_data)
                else:
                    # Fallback to basic search result
                    external_data = ExternalConceptData(
                        external_id=external_id,
                        source='wikidata',
                        label=item.get('label', concept_name),
                        description=item.get('description', ''),
                        aliases=item.get('aliases', []),
                        properties={
                            'concepturi': item.get('concepturi', ''),
                            'url': item.get('url', ''),
                            'instanceOf': [],  # Empty arrays for missing semantic data
                            'subclassOf': []
                        },
                        confidence=0.7
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
            SELECT ?label ?description ?instanceOf ?instanceOfLabel ?subclassOf ?subclassOfLabel WHERE {{
                wd:{external_id} rdfs:label ?label ;
                                schema:description ?description .
                OPTIONAL {{ 
                    wd:{external_id} wdt:P31 ?instanceOf .
                    ?instanceOf rdfs:label ?instanceOfLabel .
                    FILTER(LANG(?instanceOfLabel) = "en")
                }}
                OPTIONAL {{ 
                    wd:{external_id} wdt:P279 ?subclassOf .
                    ?subclassOf rdfs:label ?subclassOfLabel .
                    FILTER(LANG(?subclassOfLabel) = "en")
                }}
                FILTER(LANG(?label) = "en")
                FILTER(LANG(?description) = "en")
            }}
            LIMIT 10
            """
            
            self.sparql.setQuery(query)
            results = self.sparql.query().convert()
            
            if results['results']['bindings']:
                bindings = results['results']['bindings']
                first_binding = bindings[0]
                
                label = first_binding.get('label', {}).get('value', '')
                description = first_binding.get('description', {}).get('value', '')
                
                # Collect instanceOf and subclassOf with human-readable labels
                instance_of_labels = []
                subclass_of_labels = []
                instance_of_uris = []
                subclass_of_uris = []
                
                for binding in bindings:
                    instance_of_uri = binding.get('instanceOf', {}).get('value', '')
                    instance_of_label = binding.get('instanceOfLabel', {}).get('value', '')
                    subclass_of_uri = binding.get('subclassOf', {}).get('value', '')
                    subclass_of_label = binding.get('subclassOfLabel', {}).get('value', '')
                    
                    if instance_of_uri and instance_of_uri not in instance_of_uris:
                        instance_of_uris.append(instance_of_uri)
                        instance_of_labels.append(instance_of_label or instance_of_uri.split('/')[-1])
                    
                    if subclass_of_uri and subclass_of_uri not in subclass_of_uris:
                        subclass_of_uris.append(subclass_of_uri)
                        subclass_of_labels.append(subclass_of_label or subclass_of_uri.split('/')[-1])
                
                return ExternalConceptData(
                    external_id=external_id,
                    source='wikidata',
                    label=label,
                    description=description,
                    properties={
                        'instanceOf': instance_of_labels,
                        'subclassOf': subclass_of_labels,
                        'instanceOfUris': instance_of_uris,
                        'subclassOfUris': subclass_of_uris
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
        """Enrich a concept using all available external ontologies with DBpedia priority."""
        enriched_concept = concept
        
        successful_enrichments = 0
        failed_connectors = []
        primary_source_found = False
        
        # Process connectors in priority order: DBpedia first, then others
        connector_priority = ['dbpedia', 'wikidata']
        
        for connector_name in connector_priority:
            if connector_name not in self.connectors:
                continue
                
            connector = self.connectors[connector_name]
            try:
                # Create a proper copy of the current state for testing
                if connector_name == 'dbpedia':
                    temp_enriched = connector.enrich_concept(enriched_concept)
                else:
                    # For subsequent connectors, work on a copy to test results
                    temp_concept = Concept(
                        id=enriched_concept.id,
                        name=enriched_concept.name,
                        concept_type=enriched_concept.concept_type,
                        confidence=enriched_concept.confidence,
                        description=enriched_concept.description,
                        aliases=enriched_concept.aliases.copy(),
                        properties=enriched_concept.properties.copy()
                    )
                    temp_enriched = connector.enrich_concept(temp_concept)
                
                # Check if this connector found data
                external_source = temp_enriched.properties.get('external_source')
                if external_source == connector_name:
                    # If this is DBpedia and we found data, use it as primary
                    if connector_name == 'dbpedia':
                        enriched_concept = temp_enriched
                        primary_source_found = True
                        self.logger.debug(f"Using DBpedia as primary source for '{concept.name}'")
                    # If this is not DBpedia but we haven't found primary source yet, use it
                    elif not primary_source_found:
                        enriched_concept = temp_enriched
                        self.logger.debug(f"Using {connector_name} as source for '{concept.name}' (no DBpedia data)")
                    else:
                        # Merge additional metadata without overwriting primary source
                        self._merge_secondary_metadata(enriched_concept, temp_enriched, connector_name)
                        self.logger.debug(f"Merged additional metadata from {connector_name} for '{concept.name}'")
                    
                    successful_enrichments += 1
                    
            except Exception as e:
                self.logger.warning(f"Failed to enrich concept '{concept.name}' with {connector_name}: {type(e).__name__}")
                failed_connectors.append(connector_name)
                continue
        
        # Log overall enrichment status
        if successful_enrichments == 0 and failed_connectors:
            self.logger.debug(f"All enrichment sources failed for '{concept.name}': {', '.join(failed_connectors)}")
        elif failed_connectors:
            self.logger.debug(f"Partial enrichment for '{concept.name}' - failed: {', '.join(failed_connectors)}")
        
        return enriched_concept
    
    def _merge_secondary_metadata(self, primary_concept: Concept, secondary_concept: Concept, secondary_source: str):
        """Merge metadata from secondary source without overwriting primary source info."""
        # Merge categories
        primary_categories = primary_concept.properties.get('categories', [])
        secondary_categories = secondary_concept.properties.get('categories', [])
        if secondary_categories:
            # Add unique categories from secondary source
            merged_categories = list(set(primary_categories + secondary_categories))
            primary_concept.properties['categories'] = merged_categories
        
        # Merge types
        primary_types = primary_concept.properties.get('types', [])
        secondary_types = secondary_concept.properties.get('types', [])
        if secondary_types:
            merged_types = list(set(primary_types + secondary_types))
            primary_concept.properties['types'] = merged_types
        
        # Merge related concepts
        primary_related = primary_concept.properties.get('related_external_concepts', [])
        secondary_related = secondary_concept.properties.get('related_external_concepts', [])
        if secondary_related:
            merged_related = list(set(primary_related + secondary_related))
            primary_concept.properties['related_external_concepts'] = merged_related
        
        # Add secondary source info without overwriting primary
        primary_concept.properties[f'{secondary_source}_id'] = secondary_concept.properties.get('external_id', '')
        primary_concept.properties[f'{secondary_source}_confidence'] = secondary_concept.properties.get('external_confidence', 0.0)
    
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
    
    def close(self):
        """Close all connectors and clean up resources."""
        for connector_name, connector in self.connectors.items():
            try:
                connector.close()
                self.logger.debug(f"Closed {connector_name} connector")
            except Exception as e:
                self.logger.warning(f"Error closing {connector_name} connector: {e}")


def get_external_ontology_manager(settings: Settings, cache: ConceptCache) -> ExternalOntologyManager:
    """Factory function to create an external ontology manager."""
    return ExternalOntologyManager(settings, cache)