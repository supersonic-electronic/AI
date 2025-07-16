"""
Ontology framework for financial and mathematical concepts.

This module defines the conceptual framework for representing financial and
mathematical knowledge in the graph database, including concept types,
relationships, and semantic mappings.
"""

from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, Union
from dataclasses import dataclass, field
import logging


class ConceptType(Enum):
    """Types of concepts in the financial/mathematical ontology."""
    
    # Mathematical concepts
    EQUATION = "equation"
    FORMULA = "formula"
    VARIABLE = "variable"
    CONSTANT = "constant"
    FUNCTION = "function"
    MATRIX = "matrix"
    VECTOR = "vector"
    OPERATOR = "operator"
    THEOREM = "theorem"
    PROOF = "proof"
    
    # Financial concepts
    PORTFOLIO = "portfolio"
    ASSET = "asset"
    RISK = "risk"
    RETURN = "return"
    OPTIMIZATION = "optimization"
    MODEL = "model"
    STRATEGY = "strategy"
    PERFORMANCE = "performance"
    METRIC = "metric"
    CONSTRAINT = "constraint"
    
    # General concepts
    AUTHOR = "author"
    PAPER = "paper"
    METHODOLOGY = "methodology"
    ALGORITHM = "algorithm"
    PARAMETER = "parameter"
    ASSUMPTION = "assumption"
    CONCLUSION = "conclusion"
    
    # Semantic concepts
    DEFINITION = "definition"
    EXAMPLE = "example"
    APPLICATION = "application"
    LIMITATION = "limitation"


class RelationshipType(Enum):
    """Types of relationships between concepts."""
    
    # Mathematical relationships
    DERIVES_FROM = "derives_from"
    EQUALS = "equals"
    IMPLIES = "implies"
    COMPOSED_OF = "composed_of"
    DEPENDS_ON = "depends_on"
    APPROXIMATES = "approximates"
    GENERALIZES = "generalizes"
    SPECIALIZES = "specializes"
    
    # Financial relationships
    OPTIMIZES = "optimizes"
    MEASURES = "measures"
    AFFECTS = "affects"
    CORRELATES_WITH = "correlates_with"
    CONSTRAINS = "constrains"
    MAXIMIZES = "maximizes"
    MINIMIZES = "minimizes"
    
    # Semantic relationships
    DEFINES = "defines"
    MENTIONS = "mentions"
    REFERENCES = "references"
    CITES = "cites"
    EXTENDS = "extends"
    IMPLEMENTS = "implements"
    APPLIES_TO = "applies_to"
    
    # Contextual relationships
    APPEARS_IN = "appears_in"
    PART_OF = "part_of"
    CONTAINS = "contains"
    FOLLOWED_BY = "followed_by"
    PRECEDES = "precedes"


@dataclass
class Concept:
    """Represents a concept in the ontology."""
    
    id: str
    name: str
    concept_type: ConceptType
    description: Optional[str] = None
    notation: Optional[str] = None  # Mathematical notation if applicable
    latex: Optional[str] = None     # LaTeX representation if applicable
    aliases: Set[str] = field(default_factory=set)
    properties: Dict[str, Union[str, float, int, bool]] = field(default_factory=dict)
    source_document: Optional[str] = None
    source_page: Optional[int] = None
    confidence: float = 1.0
    
    def __post_init__(self):
        """Validate the concept after initialization."""
        if not self.name:
            raise ValueError("Concept name cannot be empty")
        if not isinstance(self.concept_type, ConceptType):
            raise ValueError("concept_type must be a ConceptType enum")
        if self.confidence < 0.0 or self.confidence > 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")


@dataclass
class Relationship:
    """Represents a relationship between concepts."""
    
    source_concept_id: str
    target_concept_id: str
    relationship_type: RelationshipType
    confidence: float = 1.0
    properties: Dict[str, Union[str, float, int, bool]] = field(default_factory=dict)
    source_document: Optional[str] = None
    source_page: Optional[int] = None
    context: Optional[str] = None  # Textual context where relationship was found
    
    def __post_init__(self):
        """Validate the relationship after initialization."""
        if not self.source_concept_id or not self.target_concept_id:
            raise ValueError("Source and target concept IDs cannot be empty")
        if not isinstance(self.relationship_type, RelationshipType):
            raise ValueError("relationship_type must be a RelationshipType enum")
        if self.confidence < 0.0 or self.confidence > 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")


class FinancialMathOntology:
    """
    Ontology for financial mathematics concepts and relationships.
    
    This class provides the semantic framework for understanding and
    categorizing concepts in financial mathematics literature, with
    support for external ontology integration.
    """
    
    def __init__(self, settings=None):
        """Initialize the ontology."""
        self.logger = logging.getLogger(__name__)
        self.concepts: Dict[str, Concept] = {}
        self.relationships: List[Relationship] = []
        self.settings = settings
        
        # External ontology integration
        self.external_ontology_manager = None
        self.concept_cache = None
        
        # Initialize external ontology support if settings provided
        if settings and getattr(settings, 'enable_external_ontologies', False):
            self._initialize_external_ontologies()
        
        # Initialize predefined concepts
        self._initialize_core_concepts()
        
        # Initialize concept hierarchies
        self._initialize_hierarchies()
    
    def _initialize_external_ontologies(self) -> None:
        """Initialize external ontology integration."""
        try:
            from .concept_cache import get_concept_cache
            from .external_ontologies import get_external_ontology_manager
            
            self.concept_cache = get_concept_cache(self.settings)
            self.external_ontology_manager = get_external_ontology_manager(self.settings, self.concept_cache)
            
            self.logger.info("External ontology integration initialized")
            
        except ImportError as e:
            self.logger.warning(f"External ontology integration not available: {e}")
        except Exception as e:
            self.logger.error(f"Failed to initialize external ontologies: {e}")
    
    def _initialize_core_concepts(self) -> None:
        """Initialize core financial mathematics concepts."""
        
        # Core mathematical concepts
        core_math_concepts = [
            ("portfolio_theory", "Portfolio Theory", ConceptType.METHODOLOGY),
            ("mean_variance", "Mean-Variance Optimization", ConceptType.OPTIMIZATION),
            ("efficient_frontier", "Efficient Frontier", ConceptType.METHODOLOGY),
            ("sharpe_ratio", "Sharpe Ratio", ConceptType.METRIC),
            ("expected_return", "Expected Return", ConceptType.METRIC),
            ("variance", "Variance", ConceptType.METRIC),
            ("covariance", "Covariance", ConceptType.METRIC),
            ("correlation", "Correlation", ConceptType.METRIC),
            ("risk_free_rate", "Risk-Free Rate", ConceptType.PARAMETER),
            ("portfolio_weight", "Portfolio Weight", ConceptType.VARIABLE),
            ("asset_return", "Asset Return", ConceptType.VARIABLE),
            ("portfolio_return", "Portfolio Return", ConceptType.VARIABLE),
            ("risk_aversion", "Risk Aversion", ConceptType.PARAMETER),
            ("lagrangian", "Lagrangian", ConceptType.FUNCTION),
            ("objective_function", "Objective Function", ConceptType.FUNCTION),
            ("constraint", "Constraint", ConceptType.CONSTRAINT),
            ("optimization_problem", "Optimization Problem", ConceptType.METHODOLOGY),
        ]
        
        for concept_id, name, concept_type in core_math_concepts:
            concept = Concept(
                id=concept_id,
                name=name,
                concept_type=concept_type,
                confidence=1.0
            )
            self.concepts[concept_id] = concept
    
    def _initialize_hierarchies(self) -> None:
        """Initialize concept hierarchies and relationships."""
        
        # Define hierarchical relationships
        hierarchies = [
            ("portfolio_theory", "mean_variance", RelationshipType.CONTAINS),
            ("mean_variance", "efficient_frontier", RelationshipType.PRODUCES),
            ("mean_variance", "objective_function", RelationshipType.USES),
            ("objective_function", "expected_return", RelationshipType.DEPENDS_ON),
            ("objective_function", "variance", RelationshipType.DEPENDS_ON),
            ("variance", "covariance", RelationshipType.COMPOSED_OF),
            ("sharpe_ratio", "expected_return", RelationshipType.DEPENDS_ON),
            ("sharpe_ratio", "variance", RelationshipType.DEPENDS_ON),
            ("sharpe_ratio", "risk_free_rate", RelationshipType.DEPENDS_ON),
            ("portfolio_return", "portfolio_weight", RelationshipType.DEPENDS_ON),
            ("portfolio_return", "asset_return", RelationshipType.DEPENDS_ON),
            ("optimization_problem", "objective_function", RelationshipType.CONTAINS),
            ("optimization_problem", "constraint", RelationshipType.CONTAINS),
            ("lagrangian", "objective_function", RelationshipType.EXTENDS),
            ("lagrangian", "constraint", RelationshipType.INCORPORATES),
        ]
        
        for source_id, target_id, rel_type in hierarchies:
            if source_id in self.concepts and target_id in self.concepts:
                relationship = Relationship(
                    source_concept_id=source_id,
                    target_concept_id=target_id,
                    relationship_type=rel_type,
                    confidence=1.0
                )
                self.relationships.append(relationship)
    
    def add_concept(self, concept: Concept) -> None:
        """Add a concept to the ontology."""
        if concept.id in self.concepts:
            self.logger.warning(f"Concept {concept.id} already exists, updating...")
        
        self.concepts[concept.id] = concept
        self.logger.debug(f"Added concept: {concept.name} ({concept.concept_type.value})")
    
    def add_relationship(self, relationship: Relationship) -> None:
        """Add a relationship to the ontology."""
        # Validate that both concepts exist
        if relationship.source_concept_id not in self.concepts:
            raise ValueError(f"Source concept {relationship.source_concept_id} not found")
        if relationship.target_concept_id not in self.concepts:
            raise ValueError(f"Target concept {relationship.target_concept_id} not found")
        
        self.relationships.append(relationship)
        self.logger.debug(f"Added relationship: {relationship.source_concept_id} -> {relationship.target_concept_id}")
    
    def get_concept(self, concept_id: str) -> Optional[Concept]:
        """Get a concept by ID."""
        return self.concepts.get(concept_id)
    
    def get_concepts_by_type(self, concept_type: ConceptType) -> List[Concept]:
        """Get all concepts of a specific type."""
        return [concept for concept in self.concepts.values() 
                if concept.concept_type == concept_type]
    
    def get_relationships_for_concept(self, concept_id: str) -> List[Relationship]:
        """Get all relationships involving a specific concept."""
        return [rel for rel in self.relationships 
                if rel.source_concept_id == concept_id or rel.target_concept_id == concept_id]
    
    def get_related_concepts(self, concept_id: str, 
                           relationship_type: Optional[RelationshipType] = None) -> List[Tuple[str, RelationshipType]]:
        """Get concepts related to a given concept."""
        related = []
        for rel in self.relationships:
            if rel.source_concept_id == concept_id:
                if relationship_type is None or rel.relationship_type == relationship_type:
                    related.append((rel.target_concept_id, rel.relationship_type))
            elif rel.target_concept_id == concept_id:
                if relationship_type is None or rel.relationship_type == relationship_type:
                    related.append((rel.source_concept_id, rel.relationship_type))
        return related
    
    def find_concept_by_name(self, name: str, fuzzy: bool = False) -> List[Concept]:
        """Find concepts by name, optionally with fuzzy matching."""
        matches = []
        name_lower = name.lower()
        
        for concept in self.concepts.values():
            if fuzzy:
                if name_lower in concept.name.lower() or concept.name.lower() in name_lower:
                    matches.append(concept)
                # Check aliases
                for alias in concept.aliases:
                    if name_lower in alias.lower() or alias.lower() in name_lower:
                        matches.append(concept)
                        break
            else:
                if concept.name.lower() == name_lower:
                    matches.append(concept)
                # Check aliases
                elif name_lower in [alias.lower() for alias in concept.aliases]:
                    matches.append(concept)
        
        return matches
    
    def get_concept_hierarchy(self, concept_id: str, max_depth: int = 3) -> Dict[str, List[str]]:
        """Get the hierarchy of concepts related to a given concept."""
        hierarchy = {"ancestors": [], "descendants": [], "siblings": []}
        
        def get_ancestors(cid: str, depth: int = 0) -> List[str]:
            if depth >= max_depth:
                return []
            
            ancestors = []
            for rel in self.relationships:
                if rel.target_concept_id == cid and rel.relationship_type in [
                    RelationshipType.PART_OF, RelationshipType.SPECIALIZES, 
                    RelationshipType.DERIVES_FROM, RelationshipType.DEPENDS_ON
                ]:
                    ancestors.append(rel.source_concept_id)
                    ancestors.extend(get_ancestors(rel.source_concept_id, depth + 1))
            return ancestors
        
        def get_descendants(cid: str, depth: int = 0) -> List[str]:
            if depth >= max_depth:
                return []
            
            descendants = []
            for rel in self.relationships:
                if rel.source_concept_id == cid and rel.relationship_type in [
                    RelationshipType.CONTAINS, RelationshipType.GENERALIZES,
                    RelationshipType.IMPLIES, RelationshipType.PRODUCES
                ]:
                    descendants.append(rel.target_concept_id)
                    descendants.extend(get_descendants(rel.target_concept_id, depth + 1))
            return descendants
        
        hierarchy["ancestors"] = list(set(get_ancestors(concept_id)))
        hierarchy["descendants"] = list(set(get_descendants(concept_id)))
        
        return hierarchy
    
    def enrich_concept_with_external_ontologies(self, concept: Concept) -> Concept:
        """Enrich a concept with external ontology data."""
        if not self.external_ontology_manager:
            return concept
        
        try:
            enriched_concept = self.external_ontology_manager.enrich_concept(concept)
            self.logger.debug(f"Enriched concept '{concept.name}' with external ontologies")
            return enriched_concept
            
        except Exception as e:
            self.logger.error(f"Failed to enrich concept '{concept.name}': {e}")
            return concept
    
    def search_external_ontologies(self, concept_name: str, concept_type: Optional[ConceptType] = None) -> Dict[str, Any]:
        """Search external ontologies for a concept."""
        if not self.external_ontology_manager:
            return {}
        
        try:
            results = self.external_ontology_manager.search_all_ontologies(concept_name, concept_type)
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to search external ontologies for '{concept_name}': {e}")
            return {}
    
    def add_concept_with_enrichment(self, concept: Concept, enable_enrichment: bool = True) -> None:
        """Add a concept to the ontology with optional external enrichment."""
        if enable_enrichment and self.external_ontology_manager:
            concept = self.enrich_concept_with_external_ontologies(concept)
        
        self.add_concept(concept)
    
    def get_external_ontology_stats(self) -> Dict[str, Any]:
        """Get statistics about external ontology usage."""
        if not self.concept_cache:
            return {"error": "External ontology integration not enabled"}
        
        try:
            return self.concept_cache.get_stats()
        except Exception as e:
            self.logger.error(f"Failed to get external ontology stats: {e}")
            return {"error": str(e)}
    
    def cleanup_external_cache(self, source: Optional[str] = None):
        """Clean up external ontology cache."""
        if not self.concept_cache:
            return
        
        try:
            if source:
                self.concept_cache.clear(source)
            else:
                self.concept_cache.cleanup_expired()
            
            self.logger.info(f"Cleaned up external ontology cache{' for source: ' + source if source else ''}")
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup external cache: {e}")
    
    def export_ontology(self) -> Dict[str, Union[List[Dict], Dict]]:
        """Export the ontology to a dictionary format."""
        return {
            "concepts": [
                {
                    "id": concept.id,
                    "name": concept.name,
                    "type": concept.concept_type.value,
                    "description": concept.description,
                    "notation": concept.notation,
                    "latex": concept.latex,
                    "aliases": list(concept.aliases),
                    "properties": concept.properties,
                    "source_document": concept.source_document,
                    "source_page": concept.source_page,
                    "confidence": concept.confidence
                }
                for concept in self.concepts.values()
            ],
            "relationships": [
                {
                    "source": rel.source_concept_id,
                    "target": rel.target_concept_id,
                    "type": rel.relationship_type.value,
                    "confidence": rel.confidence,
                    "properties": rel.properties,
                    "source_document": rel.source_document,
                    "source_page": rel.source_page,
                    "context": rel.context
                }
                for rel in self.relationships
            ]
        }