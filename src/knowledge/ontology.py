"""
Ontology framework for financial and mathematical concepts.

This module defines the conceptual framework for representing financial and
mathematical knowledge in the graph database, including concept types,
relationships, and semantic mappings.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union
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
    
    # Additional types from knowledge graph
    INVESTMENT_VEHICLE = "investment_vehicle"
    METHOD = "method"
    PERFORMANCE_MEASURE = "performance_measure"
    PRICING_MODEL = "pricing_model"
    RESEARCHER = "researcher"
    RISK_MEASURE = "risk_measure"
    STATISTICAL_MEASURE = "statistical_measure"
    THEORY = "theory"
    CONCEPT = "concept"  # Generic concept type


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
    
    # Enhanced metadata fields
    definition: Optional[str] = None        # Formal definition of the concept
    examples: List[str] = field(default_factory=list)  # Usage examples
    related_formulas: List[str] = field(default_factory=list)  # Related mathematical formulas
    applications: List[str] = field(default_factory=list)  # Practical applications
    prerequisites: List[str] = field(default_factory=list)  # Required knowledge
    complexity_level: Optional[str] = None  # beginner, intermediate, advanced
    domain: Optional[str] = None           # mathematics, finance, economics, etc.
    keywords: List[str] = field(default_factory=list)  # Additional search keywords
    external_links: Dict[str, str] = field(default_factory=dict)  # URLs to external resources
    created_at: Optional[str] = None       # Timestamp when concept was added
    updated_at: Optional[str] = None       # Timestamp when concept was last updated
    
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
        """Initialize core financial mathematics concepts with rich metadata."""
        from datetime import datetime
        timestamp = datetime.now().isoformat()
        
        # Enhanced core concepts with detailed metadata
        enhanced_concepts = [
            {
                "id": "portfolio_theory",
                "name": "Portfolio Theory",
                "concept_type": ConceptType.METHODOLOGY,
                "description": "Mathematical framework for constructing optimal investment portfolios",
                "definition": "A theory that describes how to construct portfolios to optimize expected return based on a given level of market risk",
                "latex": r"\text{Portfolio Theory: } E[R_p] = \sum_{i=1}^{n} w_i E[R_i]",
                "examples": ["Modern Portfolio Theory by Markowitz", "Capital Asset Pricing Model", "Efficient frontier construction"],
                "applications": ["Asset allocation", "Risk management", "Investment strategy"],
                "complexity_level": "intermediate",
                "domain": "finance",
                "keywords": ["optimization", "diversification", "risk-return"],
                "external_links": {
                    "wikipedia": "https://en.wikipedia.org/wiki/Modern_portfolio_theory"
                }
            },
            {
                "id": "sharpe_ratio",
                "name": "Sharpe Ratio",
                "concept_type": ConceptType.METRIC,
                "description": "Risk-adjusted return metric measuring excess return per unit of risk",
                "definition": "A measure for calculating risk-adjusted return, defined as the average return earned in excess of the risk-free rate per unit of volatility",
                "latex": r"S = \frac{E[R_p] - R_f}{\sigma_p}",
                "notation": "S = (Expected Return - Risk-free Rate) / Standard Deviation",
                "examples": ["Portfolio performance evaluation", "Fund comparison", "Risk-adjusted benchmarking"],
                "applications": ["Performance measurement", "Portfolio optimization", "Risk assessment"],
                "prerequisites": ["Expected return", "Standard deviation", "Risk-free rate"],
                "complexity_level": "beginner",
                "domain": "finance",
                "keywords": ["risk-adjusted", "performance", "volatility"],
                "related_formulas": ["E[R_p] - R_f", "σ_p = √(Var(R_p))"],
                "external_links": {
                    "investopedia": "https://www.investopedia.com/terms/s/sharperatio.asp"
                }
            },
            {
                "id": "expected_return",
                "name": "Expected Return",
                "concept_type": ConceptType.METRIC,
                "description": "Anticipated return on an investment based on historical data or probability distributions",
                "definition": "The profit or loss an investor anticipates on an investment with various known or anticipated rates of return",
                "latex": r"E[R] = \sum_{i=1}^{n} p_i \cdot r_i",
                "notation": "E[R] = Σ(probability × return)",
                "examples": ["Stock return forecasting", "Portfolio expected return calculation", "Investment decision making"],
                "applications": ["Portfolio optimization", "Risk assessment", "Investment planning"],
                "complexity_level": "beginner",
                "domain": "finance",
                "keywords": ["probability", "forecast", "investment"]
            },
            {
                "id": "efficient_frontier",
                "name": "Efficient Frontier",
                "concept_type": ConceptType.METHODOLOGY,
                "description": "Set of optimal portfolios offering highest expected return for each level of risk",
                "definition": "A curve on a graph representing portfolios that provide the maximum expected return for a given level of risk",
                "latex": r"\text{Minimize: } w^T \Sigma w \text{ subject to: } w^T \mu = \mu_p, \sum w_i = 1",
                "examples": ["Mean-variance optimization", "Asset allocation strategies", "Portfolio construction"],
                "applications": ["Investment management", "Risk budgeting", "Strategic asset allocation"],
                "prerequisites": ["Portfolio theory", "Mean-variance optimization", "Risk-return relationship"],
                "complexity_level": "advanced",
                "domain": "finance",
                "keywords": ["optimization", "risk-return", "portfolio"]
            },
            {
                "id": "covariance_matrix",
                "name": "Covariance Matrix",
                "concept_type": ConceptType.MATRIX,
                "description": "Matrix containing covariances between pairs of asset returns",
                "definition": "A square matrix giving the covariance between each pair of elements in a random vector",
                "latex": r"\Sigma = \begin{pmatrix} \sigma_{11} & \sigma_{12} & \cdots \\ \sigma_{21} & \sigma_{22} & \cdots \\ \vdots & \vdots & \ddots \end{pmatrix}",
                "notation": "Σ (Sigma matrix)",
                "examples": ["Risk model construction", "Portfolio variance calculation", "Correlation analysis"],
                "applications": ["Risk management", "Portfolio optimization", "Factor modeling"],
                "prerequisites": ["Variance", "Covariance", "Matrix operations"],
                "complexity_level": "intermediate",
                "domain": "mathematics",
                "keywords": ["variance", "correlation", "risk modeling"]
            }
        ]
        
        # Create enhanced concept objects
        for concept_data in enhanced_concepts:
            concept = Concept(
                id=concept_data["id"],
                name=concept_data["name"],
                concept_type=concept_data["concept_type"],
                description=concept_data.get("description"),
                definition=concept_data.get("definition"),
                latex=concept_data.get("latex"),
                notation=concept_data.get("notation"),
                examples=concept_data.get("examples", []),
                applications=concept_data.get("applications", []),
                prerequisites=concept_data.get("prerequisites", []),
                complexity_level=concept_data.get("complexity_level"),
                domain=concept_data.get("domain"),
                keywords=concept_data.get("keywords", []),
                related_formulas=concept_data.get("related_formulas", []),
                external_links=concept_data.get("external_links", {}),
                confidence=1.0,
                created_at=timestamp,
                updated_at=timestamp
            )
            self.concepts[concept.id] = concept
    
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
                    "confidence": concept.confidence,
                    "definition": concept.definition,
                    "examples": concept.examples,
                    "related_formulas": concept.related_formulas,
                    "applications": concept.applications,
                    "prerequisites": concept.prerequisites,
                    "complexity_level": concept.complexity_level,
                    "domain": concept.domain,
                    "keywords": concept.keywords,
                    "external_links": concept.external_links,
                    "created_at": concept.created_at,
                    "updated_at": concept.updated_at
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
    
    def export_for_cytoscape(self) -> Dict[str, List[Dict]]:
        """
        Export ontology in Cytoscape.js format for web visualization.
        
        Returns:
            Dictionary with 'nodes' and 'edges' lists in Cytoscape.js format
        """
        # Convert concepts to nodes
        nodes = []
        for concept in self.concepts.values():
            node = {
                "data": {
                    "id": concept.id,
                    "name": concept.name,
                    "type": concept.concept_type.value,
                    "description": concept.description or "",
                    "notation": concept.notation or "",
                    "latex": concept.latex or "",
                    "aliases": list(concept.aliases),
                    "properties": concept.properties,
                    "source_document": concept.source_document or "",
                    "source_page": concept.source_page,
                    "confidence": concept.confidence,
                    "definition": concept.definition or "",
                    "examples": concept.examples,
                    "related_formulas": concept.related_formulas,
                    "applications": concept.applications,
                    "prerequisites": concept.prerequisites,
                    "complexity_level": concept.complexity_level or "",
                    "domain": concept.domain or "",
                    "keywords": concept.keywords,
                    "external_links": concept.external_links,
                    "created_at": concept.created_at or "",
                    "updated_at": concept.updated_at or ""
                }
            }
            nodes.append(node)
        
        # Convert relationships to edges
        edges = []
        for i, relationship in enumerate(self.relationships):
            edge = {
                "data": {
                    "id": f"edge_{i}",
                    "source": relationship.source_concept_id,
                    "target": relationship.target_concept_id,
                    "type": relationship.relationship_type.value,
                    "confidence": relationship.confidence,
                    "properties": relationship.properties,
                    "source_document": relationship.source_document or "",
                    "source_page": relationship.source_page,
                    "context": relationship.context or ""
                }
            }
            edges.append(edge)
        
        return {
            "nodes": nodes,
            "edges": edges
        }
    
    def get_enhanced_color_scheme(self) -> Dict[str, str]:
        """
        Get an enhanced color scheme for web visualization.
        
        Returns professional colors optimized for web display based on
        the existing color scheme but with improved accessibility and aesthetics.
        
        Returns:
            Dictionary mapping concept types to hex colors
        """
        return {
            # Mathematical concepts - Blue family
            ConceptType.EQUATION.value: "#2196F3",      # Material Blue
            ConceptType.FORMULA.value: "#1976D2",       # Material Blue 700
            ConceptType.VARIABLE.value: "#42A5F5",      # Material Blue 400
            ConceptType.CONSTANT.value: "#64B5F6",      # Material Blue 300
            ConceptType.FUNCTION.value: "#90CAF9",      # Material Blue 200
            ConceptType.MATRIX.value: "#BBDEFB",        # Material Blue 100
            ConceptType.VECTOR.value: "#E3F2FD",        # Material Blue 50
            ConceptType.OPERATOR.value: "#1565C0",      # Material Blue 800
            ConceptType.THEOREM.value: "#0D47A1",       # Material Blue 900
            ConceptType.PROOF.value: "#0277BD",         # Light Blue 800
            
            # Financial concepts - Green/Orange family
            ConceptType.PORTFOLIO.value: "#FF8A50",     # Warm orange
            ConceptType.ASSET.value: "#4CAF50",         # Material Green
            ConceptType.RISK.value: "#E91E63",          # Material Pink
            ConceptType.RETURN.value: "#2E7D32",        # Material Green 800
            ConceptType.OPTIMIZATION.value: "#9C27B0",  # Material Purple
            ConceptType.MODEL.value: "#FF5722",         # Material Deep Orange
            ConceptType.STRATEGY.value: "#795548",      # Material Brown
            ConceptType.PERFORMANCE.value: "#607D8B",   # Material Blue Grey
            ConceptType.METRIC.value: "#00BCD4",        # Material Cyan
            ConceptType.CONSTRAINT.value: "#FFC107",    # Material Amber
            
            # General concepts - Grey/Purple family
            ConceptType.AUTHOR.value: "#9E9E9E",        # Material Grey
            ConceptType.PAPER.value: "#757575",         # Material Grey 600
            ConceptType.METHODOLOGY.value: "#673AB7",   # Material Deep Purple
            ConceptType.ALGORITHM.value: "#3F51B5",     # Material Indigo
            ConceptType.PARAMETER.value: "#009688",     # Material Teal
            ConceptType.ASSUMPTION.value: "#8BC34A",    # Material Light Green
            ConceptType.CONCLUSION.value: "#CDDC39",    # Material Lime
            
            # Semantic concepts - Warm family
            ConceptType.DEFINITION.value: "#FF9800",    # Material Orange
            ConceptType.EXAMPLE.value: "#FF5722",       # Material Deep Orange
            ConceptType.APPLICATION.value: "#795548",   # Material Brown
            ConceptType.LIMITATION.value: "#F44336",    # Material Red
        }