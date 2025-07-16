"""
Concept extraction from text and mathematical equations.

This module provides functionality to extract concepts and relationships from
financial mathematics documents, identifying mathematical formulas, variables,
and semantic relationships between concepts.
"""

import logging
import re
from typing import Dict, List, Optional, Set, Tuple, Union, Any
from dataclasses import dataclass, field
from enum import Enum
import json

from .ontology import Concept, Relationship, ConceptType, RelationshipType, FinancialMathOntology
from .utils import normalize_concept_name
from src.ingestion.math_detector import MathDetector
from src.settings import Settings


class ExtractionMethod(Enum):
    """Methods used for concept extraction."""
    REGEX_PATTERN = "regex_pattern"
    MATH_DETECTION = "math_detection"
    SEMANTIC_ANALYSIS = "semantic_analysis"
    CONTEXT_ANALYSIS = "context_analysis"
    OCR_FALLBACK = "ocr_fallback"


@dataclass
class ExtractedConcept:
    """Represents a concept extracted from text."""
    name: str
    concept_type: ConceptType
    description: Optional[str] = None
    notation: Optional[str] = None
    latex: Optional[str] = None
    aliases: Set[str] = field(default_factory=set)
    properties: Dict[str, Any] = field(default_factory=dict)
    source_text: Optional[str] = None
    source_document: Optional[str] = None
    source_page: Optional[int] = None
    confidence: float = 1.0
    extraction_method: ExtractionMethod = ExtractionMethod.REGEX_PATTERN
    context: Optional[str] = None


@dataclass
class ExtractedRelationship:
    """Represents a relationship extracted from text."""
    source_concept: str
    target_concept: str
    relationship_type: RelationshipType
    confidence: float = 1.0
    properties: Dict[str, Any] = field(default_factory=dict)
    source_text: Optional[str] = None
    source_document: Optional[str] = None
    source_page: Optional[int] = None
    context: Optional[str] = None
    extraction_method: ExtractionMethod = ExtractionMethod.SEMANTIC_ANALYSIS


class ConceptExtractor:
    """
    Extract concepts and relationships from financial mathematics documents.
    
    This class uses pattern matching, mathematical detection, and semantic analysis
    to identify concepts and their relationships in academic texts.
    """
    
    def __init__(self, settings: Settings, ontology: FinancialMathOntology):
        """Initialize the concept extractor."""
        self.settings = settings
        self.ontology = ontology
        self.logger = logging.getLogger(__name__)
        
        # Initialize math detector
        self.math_detector = MathDetector(settings)
        
        # Initialize enhanced metadata extractor
        self.enhanced_metadata_extractor = EnhancedMetadataExtractor(settings)
        
        # Compile extraction patterns
        self._compile_patterns()
        
        # Load domain-specific dictionaries
        self._load_dictionaries()
        
        # Initialize concept cache
        self.concept_cache: Dict[str, ExtractedConcept] = {}
    
    def _compile_patterns(self) -> None:
        """Compile regex patterns for concept extraction."""
        
        # Financial mathematics concept patterns
        self.finance_patterns = {
            'portfolio_theory': [
                re.compile(r'(?:portfolio|efficient frontier|mean.variance|markowitz)', re.IGNORECASE),
                re.compile(r'(?:asset allocation|diversification|risk.return)', re.IGNORECASE),
            ],
            'risk_metrics': [
                re.compile(r'(?:value at risk|var|expected shortfall|conditional var)', re.IGNORECASE),
                re.compile(r'(?:volatility|standard deviation|variance)', re.IGNORECASE),
            ],
            'optimization': [
                re.compile(r'(?:optimization|minimize|maximize|objective function)', re.IGNORECASE),
                re.compile(r'(?:constraint|lagrangian|karush.kuhn.tucker)', re.IGNORECASE),
            ],
            'performance': [
                re.compile(r'(?:sharpe ratio|information ratio|treynor ratio)', re.IGNORECASE),
                re.compile(r'(?:alpha|beta|jensen.alpha|tracking error)', re.IGNORECASE),
            ]
        }
        
        # Mathematical equation patterns
        self.equation_patterns = [
            re.compile(r'([A-Za-z_]\w*)\s*=\s*([^=\n]+)', re.MULTILINE),  # Variable = expression
            re.compile(r'([A-Za-z_]\w*)\s*:\s*([^:\n]+)', re.MULTILINE),  # Variable : definition
            re.compile(r'let\s+([A-Za-z_]\w*)\s+(?:be|denote|represent)\s+([^.\n]+)', re.IGNORECASE),
        ]
        
        # Variable definition patterns
        self.variable_patterns = [
            re.compile(r'(?:where|let)\s+([A-Za-z_]\w*)\s+(?:is|denotes?|represents?)\s+([^.\n]+)', re.IGNORECASE),
            re.compile(r'([A-Za-z_]\w*)\s+(?:is|denotes?|represents?)\s+(?:the\s+)?([^.\n]+)', re.IGNORECASE),
        ]
        
        # Formula patterns
        self.formula_patterns = [
            re.compile(r'(?:formula|equation|expression)(?:\s+for)?\s+([A-Za-z_]\w*)', re.IGNORECASE),
            re.compile(r'(?:calculate|compute|determine)\s+([A-Za-z_]\w*)', re.IGNORECASE),
        ]
        
        # Relationship patterns
        self.relationship_patterns = {
            RelationshipType.DEPENDS_ON: [
                re.compile(r'([A-Za-z_]\w*)\s+depends\s+on\s+([A-Za-z_]\w*)', re.IGNORECASE),
                re.compile(r'([A-Za-z_]\w*)\s+(?:is\s+)?function\s+of\s+([A-Za-z_]\w*)', re.IGNORECASE),
            ],
            RelationshipType.DERIVES_FROM: [
                re.compile(r'([A-Za-z_]\w*)\s+(?:is\s+)?derived\s+from\s+([A-Za-z_]\w*)', re.IGNORECASE),
                re.compile(r'([A-Za-z_]\w*)\s+follows\s+from\s+([A-Za-z_]\w*)', re.IGNORECASE),
            ],
            RelationshipType.MEASURES: [
                re.compile(r'([A-Za-z_]\w*)\s+measures\s+([A-Za-z_]\w*)', re.IGNORECASE),
                re.compile(r'([A-Za-z_]\w*)\s+(?:is\s+a\s+)?measure\s+of\s+([A-Za-z_]\w*)', re.IGNORECASE),
            ],
            RelationshipType.OPTIMIZES: [
                re.compile(r'(?:minimize|maximize)\s+([A-Za-z_]\w*)', re.IGNORECASE),
                re.compile(r'optimal\s+([A-Za-z_]\w*)', re.IGNORECASE),
            ]
        }
        
        self.logger.debug("Compiled concept extraction patterns")
    
    def _load_dictionaries(self) -> None:
        """Load domain-specific dictionaries and synonyms."""
        
        # Financial mathematics terminology
        self.finance_terms = {
            'portfolio': ['portfolio', 'investment portfolio', 'asset portfolio'],
            'return': ['return', 'returns', 'expected return', 'portfolio return'],
            'risk': ['risk', 'volatility', 'uncertainty', 'standard deviation'],
            'variance': ['variance', 'covariance', 'var', 'σ²'],
            'correlation': ['correlation', 'covariance', 'dependence'],
            'optimization': ['optimization', 'optimisation', 'minimize', 'maximize'],
            'constraint': ['constraint', 'restriction', 'limitation'],
            'sharpe_ratio': ['sharpe ratio', 'sharpe', 'risk-adjusted return'],
            'efficient_frontier': ['efficient frontier', 'efficient set', 'pareto frontier'],
            'mean_variance': ['mean-variance', 'mean variance', 'mv optimization'],
        }
        
        # Mathematical notation mappings
        self.notation_mappings = {
            'μ': 'mu',
            'σ': 'sigma', 
            'ρ': 'rho',
            'Σ': 'covariance_matrix',
            'E': 'expected_value',
            'Var': 'variance',
            'Cov': 'covariance',
            'w': 'weight',
            'R': 'return',
            'π': 'pi',
            'λ': 'lambda',
            'β': 'beta',
            'α': 'alpha'
        }
        
        self.logger.debug("Loaded domain-specific dictionaries")
    
    def extract_concepts_from_text(self, text: str, 
                                 document_name: Optional[str] = None,
                                 page_number: Optional[int] = None,
                                 context: Optional[str] = None) -> List[ExtractedConcept]:
        """
        Extract concepts from a block of text with enhanced metadata.
        
        Args:
            text: Text to analyze
            document_name: Source document name
            page_number: Source page number
            context: Additional context (e.g., section headers, document structure)
            
        Returns:
            List of extracted concepts with enhanced metadata
        """
        concepts = []
        
        # Extract enhanced metadata for the text block
        complexity_level = self.enhanced_metadata_extractor.extract_complexity_level(text, context or "")
        domain = self.enhanced_metadata_extractor.extract_domain(text, context or "")
        prerequisites = self.enhanced_metadata_extractor.extract_prerequisites(text, self.ontology)
        
        # Split text into sentences for better analysis
        sentences = re.split(r'[.!?]', text)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # Extract mathematical concepts
            math_concepts = self._extract_mathematical_concepts(
                sentence, document_name, page_number
            )
            concepts.extend(math_concepts)
            
            # Extract financial concepts
            finance_concepts = self._extract_financial_concepts(
                sentence, document_name, page_number
            )
            concepts.extend(finance_concepts)
            
            # Extract variable definitions
            variable_concepts = self._extract_variable_definitions(
                sentence, document_name, page_number
            )
            concepts.extend(variable_concepts)
            
            # Extract formula concepts
            formula_concepts = self._extract_formula_concepts(
                sentence, document_name, page_number
            )
            concepts.extend(formula_concepts)
        
        # Remove duplicates and merge similar concepts
        unique_concepts = self._deduplicate_concepts(concepts)
        
        # Enhance concepts with extracted metadata
        for concept in unique_concepts:
            # Add enhanced metadata to concept properties
            concept.properties.update({
                'complexity_level': complexity_level,
                'domain': domain,
                'prerequisites': prerequisites
            })
        
        self.logger.debug(f"Extracted {len(unique_concepts)} unique concepts from text with enhanced metadata")
        return unique_concepts
    
    def _extract_mathematical_concepts(self, text: str, 
                                     document_name: Optional[str] = None,
                                     page_number: Optional[int] = None) -> List[ExtractedConcept]:
        """Extract mathematical concepts using math detector."""
        concepts = []
        
        # Use math detector to identify mathematical content
        is_math, confidence, breakdown = self.math_detector.detect_mathematical_content(text)
        
        if is_math and confidence > 0.3:
            # Extract variables from mathematical expressions
            variables = self.math_detector.extract_variables(text)
            
            for var in variables:
                concept = ExtractedConcept(
                    name=var,
                    concept_type=ConceptType.VARIABLE,
                    description=f"Mathematical variable found in: {text[:100]}",
                    notation=var,
                    latex=self.math_detector.convert_to_latex(var),
                    source_text=text,
                    source_document=document_name,
                    source_page=page_number,
                    confidence=confidence,
                    extraction_method=ExtractionMethod.MATH_DETECTION,
                    context=text
                )
                concepts.append(concept)
            
            # If the text contains equations, extract them
            for pattern in self.equation_patterns:
                matches = pattern.findall(text)
                for match in matches:
                    if len(match) >= 2:
                        var_name, expression = match[0], match[1]
                        concept = ExtractedConcept(
                            name=var_name,
                            concept_type=ConceptType.EQUATION,
                            description=f"Equation: {var_name} = {expression}",
                            notation=f"{var_name} = {expression}",
                            latex=self.math_detector.convert_to_latex(f"{var_name} = {expression}"),
                            source_text=text,
                            source_document=document_name,
                            source_page=page_number,
                            confidence=confidence,
                            extraction_method=ExtractionMethod.MATH_DETECTION,
                            context=text
                        )
                        concepts.append(concept)
        
        return concepts
    
    def _extract_financial_concepts(self, text: str,
                                  document_name: Optional[str] = None,
                                  page_number: Optional[int] = None) -> List[ExtractedConcept]:
        """Extract financial concepts using domain patterns."""
        concepts = []
        
        for category, patterns in self.finance_patterns.items():
            for pattern in patterns:
                matches = pattern.findall(text)
                for match in matches:
                    # Determine concept type based on category
                    if category == 'portfolio_theory':
                        concept_type = ConceptType.METHODOLOGY
                    elif category == 'risk_metrics':
                        concept_type = ConceptType.METRIC
                    elif category == 'optimization':
                        concept_type = ConceptType.OPTIMIZATION
                    elif category == 'performance':
                        concept_type = ConceptType.METRIC
                    else:
                        concept_type = ConceptType.METHODOLOGY
                    
                    concept = ExtractedConcept(
                        name=match.lower().replace(' ', '_'),
                        concept_type=concept_type,
                        description=f"Financial concept from {category}: {match}",
                        aliases={match.lower(), match},
                        source_text=text,
                        source_document=document_name,
                        source_page=page_number,
                        confidence=0.8,
                        extraction_method=ExtractionMethod.REGEX_PATTERN,
                        context=text
                    )
                    concepts.append(concept)
        
        return concepts
    
    def _extract_variable_definitions(self, text: str,
                                    document_name: Optional[str] = None,
                                    page_number: Optional[int] = None) -> List[ExtractedConcept]:
        """Extract variable definitions from text."""
        concepts = []
        
        for pattern in self.variable_patterns:
            matches = pattern.findall(text)
            for match in matches:
                if len(match) >= 2:
                    var_name, definition = match[0], match[1]
                    
                    concept = ExtractedConcept(
                        name=var_name,
                        concept_type=ConceptType.VARIABLE,
                        description=definition.strip(),
                        notation=var_name,
                        source_text=text,
                        source_document=document_name,
                        source_page=page_number,
                        confidence=0.7,
                        extraction_method=ExtractionMethod.SEMANTIC_ANALYSIS,
                        context=text
                    )
                    concepts.append(concept)
        
        return concepts
    
    def _extract_formula_concepts(self, text: str,
                                document_name: Optional[str] = None,
                                page_number: Optional[int] = None) -> List[ExtractedConcept]:
        """Extract formula concepts from text."""
        concepts = []
        
        for pattern in self.formula_patterns:
            matches = pattern.findall(text)
            for match in matches:
                concept = ExtractedConcept(
                    name=match,
                    concept_type=ConceptType.FORMULA,
                    description=f"Formula mentioned in: {text[:100]}",
                    source_text=text,
                    source_document=document_name,
                    source_page=page_number,
                    confidence=0.6,
                    extraction_method=ExtractionMethod.REGEX_PATTERN,
                    context=text
                )
                concepts.append(concept)
        
        return concepts
    
    def _deduplicate_concepts(self, concepts: List[ExtractedConcept]) -> List[ExtractedConcept]:
        """Remove duplicate concepts and merge similar ones."""
        unique_concepts = {}
        
        for concept in concepts:
            # Create a normalized key for deduplication
            key = normalize_concept_name(concept.name)
            
            if key in unique_concepts:
                # Merge with existing concept (keep higher confidence)
                existing = unique_concepts[key]
                if concept.confidence > existing.confidence:
                    unique_concepts[key] = concept
                else:
                    # Merge aliases
                    existing.aliases.update(concept.aliases)
            else:
                unique_concepts[key] = concept
        
        return list(unique_concepts.values())
    
    def extract_relationships_from_text(self, text: str,
                                      extracted_concepts: List[ExtractedConcept],
                                      document_name: Optional[str] = None,
                                      page_number: Optional[int] = None) -> List[ExtractedRelationship]:
        """
        Extract relationships between concepts from text.
        
        Args:
            text: Text to analyze
            extracted_concepts: List of concepts to find relationships between
            document_name: Source document name
            page_number: Source page number
            
        Returns:
            List of extracted relationships
        """
        relationships = []
        
        # Create concept name lookup using normalized names
        concept_names = {normalize_concept_name(concept.name): concept.name for concept in extracted_concepts}
        
        # Extract explicit relationships using patterns
        for rel_type, patterns in self.relationship_patterns.items():
            for pattern in patterns:
                matches = pattern.findall(text)
                for match in matches:
                    if len(match) >= 2:
                        source_name = normalize_concept_name(match[0])
                        target_name = normalize_concept_name(match[1])
                        
                        # Check if both concepts exist
                        if source_name in concept_names and target_name in concept_names:
                            relationship = ExtractedRelationship(
                                source_concept=concept_names[source_name],
                                target_concept=concept_names[target_name],
                                relationship_type=rel_type,
                                source_text=text,
                                source_document=document_name,
                                source_page=page_number,
                                confidence=0.7,
                                context=text,
                                extraction_method=ExtractionMethod.REGEX_PATTERN
                            )
                            relationships.append(relationship)
        
        # Extract implicit relationships from equations
        equation_relationships = self._extract_equation_relationships(
            text, extracted_concepts, document_name, page_number
        )
        relationships.extend(equation_relationships)
        
        # Extract contextual relationships
        contextual_relationships = self._extract_contextual_relationships(
            text, extracted_concepts, document_name, page_number
        )
        relationships.extend(contextual_relationships)
        
        self.logger.debug(f"Extracted {len(relationships)} relationships from text")
        return relationships
    
    def _extract_equation_relationships(self, text: str,
                                      extracted_concepts: List[ExtractedConcept],
                                      document_name: Optional[str] = None,
                                      page_number: Optional[int] = None) -> List[ExtractedRelationship]:
        """Extract relationships from mathematical equations."""
        relationships = []
        
        # Create concept lookup
        concept_lookup = {concept.name.lower(): concept for concept in extracted_concepts}
        
        # Find equations in text
        for pattern in self.equation_patterns:
            matches = pattern.findall(text)
            for match in matches:
                if len(match) >= 2:
                    lhs, rhs = match[0], match[1]
                    
                    # Extract variables from both sides
                    lhs_vars = self.math_detector.extract_variables(lhs)
                    rhs_vars = self.math_detector.extract_variables(rhs)
                    
                    # Create dependencies: LHS depends on RHS variables
                    for lhs_var in lhs_vars:
                        for rhs_var in rhs_vars:
                            if lhs_var.lower() in concept_lookup and rhs_var.lower() in concept_lookup:
                                relationship = ExtractedRelationship(
                                    source_concept=lhs_var,
                                    target_concept=rhs_var,
                                    relationship_type=RelationshipType.DEPENDS_ON,
                                    source_text=text,
                                    source_document=document_name,
                                    source_page=page_number,
                                    confidence=0.8,
                                    context=f"Equation: {lhs} = {rhs}",
                                    extraction_method=ExtractionMethod.MATH_DETECTION
                                )
                                relationships.append(relationship)
        
        return relationships
    
    def _extract_contextual_relationships(self, text: str,
                                        extracted_concepts: List[ExtractedConcept],
                                        document_name: Optional[str] = None,
                                        page_number: Optional[int] = None) -> List[ExtractedRelationship]:
        """Extract relationships based on contextual proximity."""
        relationships = []
        
        # Simple proximity-based relationship extraction
        concept_names = [concept.name.lower() for concept in extracted_concepts]
        
        # Find concepts that appear close together in text
        words = text.lower().split()
        for i, word in enumerate(words):
            if word in concept_names:
                # Look for other concepts within a window
                window_size = 10
                start = max(0, i - window_size)
                end = min(len(words), i + window_size + 1)
                
                for j in range(start, end):
                    if j != i and words[j] in concept_names:
                        # Create a weak contextual relationship
                        relationship = ExtractedRelationship(
                            source_concept=word,
                            target_concept=words[j],
                            relationship_type=RelationshipType.MENTIONS,
                            source_text=text,
                            source_document=document_name,
                            source_page=page_number,
                            confidence=0.3,
                            context=f"Contextual proximity in: {' '.join(words[start:end])}",
                            extraction_method=ExtractionMethod.CONTEXT_ANALYSIS
                        )
                        relationships.append(relationship)
        
        return relationships
    
    def process_document_page(self, page_text: str,
                            document_name: str,
                            page_number: int,
                            context: Optional[str] = None) -> Tuple[List[ExtractedConcept], List[ExtractedRelationship]]:
        """
        Process a single document page to extract concepts and relationships.
        
        Args:
            page_text: Text content of the page
            document_name: Name of the source document
            page_number: Page number
            context: Additional context (e.g., section headers, document structure)
            
        Returns:
            Tuple of (extracted_concepts, extracted_relationships)
        """
        # Extract concepts from the page with enhanced metadata
        concepts = self.extract_concepts_from_text(page_text, document_name, page_number, context)
        
        # Extract relationships between concepts
        relationships = self.extract_relationships_from_text(
            page_text, concepts, document_name, page_number
        )
        
        self.logger.info(f"Processed page {page_number}: {len(concepts)} concepts, {len(relationships)} relationships")
        
        return concepts, relationships
    
    def convert_to_ontology_objects(self, extracted_concepts: List[ExtractedConcept],
                                  extracted_relationships: List[ExtractedRelationship],
                                  enable_external_enrichment: bool = True) -> Tuple[List[Concept], List[Relationship]]:
        """
        Convert extracted concepts and relationships to ontology objects.
        
        Args:
            extracted_concepts: List of extracted concepts
            extracted_relationships: List of extracted relationships
            enable_external_enrichment: Enable external ontology enrichment
            
        Returns:
            Tuple of (ontology_concepts, ontology_relationships)
        """
        ontology_concepts = []
        ontology_relationships = []
        
        # Convert concepts
        for extracted in extracted_concepts:
            # Extract enhanced metadata from properties
            complexity_level = extracted.properties.get('complexity_level')
            domain = extracted.properties.get('domain')
            prerequisites = extracted.properties.get('prerequisites', [])
            
            concept = Concept(
                id=f"{extracted.name}_{extracted.source_page or 0}",
                name=extracted.name,
                concept_type=extracted.concept_type,
                description=extracted.description,
                notation=extracted.notation,
                latex=extracted.latex,
                aliases=extracted.aliases,
                properties=extracted.properties,
                source_document=extracted.source_document,
                source_page=extracted.source_page,
                confidence=extracted.confidence,
                # Enhanced metadata fields
                complexity_level=complexity_level,
                domain=domain,
                prerequisites=prerequisites
            )
            
            # Add concept to ontology with enrichment
            if enable_external_enrichment:
                self.ontology.add_concept_with_enrichment(concept)
            else:
                self.ontology.add_concept(concept)
            
            ontology_concepts.append(concept)
        
        # Convert relationships
        for extracted in extracted_relationships:
            relationship = Relationship(
                source_concept_id=f"{extracted.source_concept}_{extracted.source_page or 0}",
                target_concept_id=f"{extracted.target_concept}_{extracted.source_page or 0}",
                relationship_type=extracted.relationship_type,
                confidence=extracted.confidence,
                properties=extracted.properties,
                source_document=extracted.source_document,
                source_page=extracted.source_page,
                context=extracted.context
            )
            
            # Add relationship to ontology
            self.ontology.add_relationship(relationship)
            ontology_relationships.append(relationship)
        
        return ontology_concepts, ontology_relationships
    
    def process_document(self, document_text: str,
                       document_name: str,
                       enable_external_enrichment: bool = True) -> Tuple[List[ExtractedConcept], List[ExtractedRelationship]]:
        """
        Process an entire document to extract concepts and relationships.
        
        Args:
            document_text: Full text content of the document
            document_name: Name of the source document
            enable_external_enrichment: Enable external ontology enrichment
            
        Returns:
            Tuple of (extracted_concepts, extracted_relationships)
        """
        # Split document into pages/sections for processing
        pages = self._split_document_into_pages(document_text)
        
        all_concepts = []
        all_relationships = []
        
        for page_num, page_text in enumerate(pages, 1):
            # Create context from document name and page number
            context = f"Document: {document_name}, Page: {page_num}"
            
            concepts, relationships = self.process_document_page(
                page_text, document_name, page_num, context
            )
            all_concepts.extend(concepts)
            all_relationships.extend(relationships)
        
        # Remove duplicates across pages
        unique_concepts = self._deduplicate_concepts(all_concepts)
        unique_relationships = self._deduplicate_relationships(all_relationships)
        
        # Convert to ontology objects and enrich
        ontology_concepts, ontology_relationships = self.convert_to_ontology_objects(
            unique_concepts, unique_relationships, enable_external_enrichment
        )
        
        self.logger.info(f"Processed document '{document_name}': {len(unique_concepts)} unique concepts, {len(unique_relationships)} unique relationships")
        
        return unique_concepts, unique_relationships
    
    def _split_document_into_pages(self, document_text: str) -> List[str]:
        """Split document text into pages/sections."""
        # Simple page splitting by page breaks or section markers
        pages = []
        
        # Try to split by page breaks
        if '\\f' in document_text:  # Form feed character
            pages = document_text.split('\\f')
        elif '\\n\\n\\n' in document_text:  # Triple newlines
            pages = document_text.split('\\n\\n\\n')
        else:
            # Split by paragraph breaks and group into chunks
            paragraphs = document_text.split('\\n\\n')
            current_page = []
            
            for paragraph in paragraphs:
                current_page.append(paragraph)
                # If page gets too long, start a new one
                if len('\\n\\n'.join(current_page)) > 5000:
                    pages.append('\\n\\n'.join(current_page))
                    current_page = []
            
            # Add final page if it has content
            if current_page:
                pages.append('\\n\\n'.join(current_page))
        
        return [page.strip() for page in pages if page.strip()]
    
    def _deduplicate_relationships(self, relationships: List[ExtractedRelationship]) -> List[ExtractedRelationship]:
        """Remove duplicate relationships."""
        unique_relationships = {}
        
        for relationship in relationships:
            # Create a normalized key for deduplication
            key = f"{relationship.source_concept.lower()}_{relationship.target_concept.lower()}_{relationship.relationship_type.value}"
            
            if key in unique_relationships:
                # Keep the one with higher confidence
                existing = unique_relationships[key]
                if relationship.confidence > existing.confidence:
                    unique_relationships[key] = relationship
            else:
                unique_relationships[key] = relationship
        
        return list(unique_relationships.values())
    
    def enrich_extracted_concepts(self, concepts: List[ExtractedConcept]) -> List[ExtractedConcept]:
        """Enrich extracted concepts with external ontology data."""
        if not getattr(self.settings, 'enable_external_ontologies', False):
            return concepts
        
        enriched_concepts = []
        
        for concept in concepts:
            # Convert to ontology Concept object
            ontology_concept = Concept(
                id=concept.name,
                name=concept.name,
                concept_type=concept.concept_type,
                description=concept.description,
                notation=concept.notation,
                latex=concept.latex,
                aliases=concept.aliases,
                properties=concept.properties,
                source_document=concept.source_document,
                source_page=concept.source_page,
                confidence=concept.confidence
            )
            
            # Enrich with external ontologies
            enriched_ontology_concept = self.ontology.enrich_concept_with_external_ontologies(ontology_concept)
            
            # Convert back to ExtractedConcept
            enriched_concept = ExtractedConcept(
                name=enriched_ontology_concept.name,
                concept_type=enriched_ontology_concept.concept_type,
                description=enriched_ontology_concept.description,
                notation=enriched_ontology_concept.notation,
                latex=enriched_ontology_concept.latex,
                aliases=enriched_ontology_concept.aliases,
                properties=enriched_ontology_concept.properties,
                source_text=concept.source_text,
                source_document=enriched_ontology_concept.source_document,
                source_page=enriched_ontology_concept.source_page,
                confidence=enriched_ontology_concept.confidence,
                extraction_method=concept.extraction_method,
                context=concept.context
            )
            
            enriched_concepts.append(enriched_concept)
        
        return enriched_concepts
    
    def search_external_ontologies(self, concept_name: str, concept_type: Optional[ConceptType] = None) -> Dict[str, Any]:
        """Search external ontologies for concept information."""
        return self.ontology.search_external_ontologies(concept_name, concept_type)
    
    def get_external_ontology_stats(self) -> Dict[str, Any]:
        """Get statistics about external ontology usage."""
        return self.ontology.get_external_ontology_stats()


class EnhancedMetadataExtractor:
    """
    Enhanced metadata extractor for complexity levels, prerequisites, and domain classification.
    
    This class implements FR1 requirements for automated extraction of enhanced metadata
    from financial mathematics documents.
    """
    
    def __init__(self, settings: Settings):
        """Initialize the enhanced metadata extractor."""
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        
        # Complexity level indicators
        self.complexity_indicators = {
            'beginner': [
                re.compile(r'introduction\s+to|basic|fundamental|elementary|simple', re.IGNORECASE),
                re.compile(r'primer|overview|getting\s+started|basics', re.IGNORECASE),
                re.compile(r'introductory|elementary|simple\s+example', re.IGNORECASE),
            ],
            'intermediate': [
                re.compile(r'intermediate|moderate|standard|typical', re.IGNORECASE),
                re.compile(r'application|practical|implementation', re.IGNORECASE),
                re.compile(r'case\s+study|real.world|empirical', re.IGNORECASE),
            ],
            'advanced': [
                re.compile(r'advanced|sophisticated|complex|rigorous', re.IGNORECASE),
                re.compile(r'theoretical|mathematical\s+proof|derivation', re.IGNORECASE),
                re.compile(r'research|cutting.edge|state.of.the.art', re.IGNORECASE),
                re.compile(r'phd|doctoral|graduate.level', re.IGNORECASE),
            ]
        }
        
        # Mathematical complexity indicators
        self.math_complexity_patterns = [
            # Advanced: Multiple integrals, differential equations
            (re.compile(r'∫∫|∭|∂²|∇²|differential\s+equation'), 'advanced'),
            # Advanced: Matrix operations, eigenvalues
            (re.compile(r'eigenvalue|eigenvector|matrix\s+inverse|determinant'), 'advanced'),
            # Intermediate: Single integrals, derivatives
            (re.compile(r'∫|∂|derivative|integral'), 'intermediate'),
            # Intermediate: Summations, products
            (re.compile(r'∑|∏|summation|product'), 'intermediate'),
            # Beginner: Basic arithmetic operations
            (re.compile(r'[+\-*/=]|arithmetic|calculation'), 'beginner'),
        ]
        
        # Prerequisite indicators
        self.prerequisite_patterns = [
            re.compile(r'assumes?\s+(?:familiarity\s+with|knowledge\s+of|understanding\s+of)\s+([^.,;]+)', re.IGNORECASE),
            re.compile(r'requires?\s+(?:knowledge\s+of|understanding\s+of|familiarity\s+with)\s+([^.,;]+)', re.IGNORECASE),
            re.compile(r'builds?\s+(?:on|upon)\s+([^.,;]+)', re.IGNORECASE),
            re.compile(r'based\s+on\s+([^.,;]+)', re.IGNORECASE),
            re.compile(r'given\s+(?:knowledge\s+of|understanding\s+of)\s+([^.,;]+)', re.IGNORECASE),
            re.compile(r'prerequisite[s]?\s*:\s*([^.,;]+)', re.IGNORECASE),
            re.compile(r'background\s+in\s+([^.,;]+)', re.IGNORECASE),
        ]
        
        # Domain classification patterns
        self.domain_patterns = {
            'mathematics': [
                re.compile(r'mathematical|theorem|proof|lemma|corollary', re.IGNORECASE),
                re.compile(r'algebra|calculus|statistics|probability|geometry', re.IGNORECASE),
                re.compile(r'analysis|topology|number\s+theory', re.IGNORECASE),
            ],
            'finance': [
                re.compile(r'financial|portfolio|investment|trading|market', re.IGNORECASE),
                re.compile(r'asset|security|bond|stock|option|derivative', re.IGNORECASE),
                re.compile(r'risk\s+management|capital|banking|hedge', re.IGNORECASE),
            ],
            'economics': [
                re.compile(r'economic|economy|econometric|microeconomic|macroeconomic', re.IGNORECASE),
                re.compile(r'supply|demand|market\s+equilibrium|elasticity', re.IGNORECASE),
                re.compile(r'gdp|inflation|monetary|fiscal|policy', re.IGNORECASE),
            ],
            'statistics': [
                re.compile(r'statistical|regression|correlation|hypothesis', re.IGNORECASE),
                re.compile(r'distribution|normal|gaussian|chi.square|t.test', re.IGNORECASE),
                re.compile(r'confidence\s+interval|p.value|significance', re.IGNORECASE),
            ],
            'optimization': [
                re.compile(r'optimization|minimize|maximize|constraint|lagrange', re.IGNORECASE),
                re.compile(r'linear\s+programming|quadratic\s+programming|convex', re.IGNORECASE),
                re.compile(r'objective\s+function|feasible\s+region|optimal', re.IGNORECASE),
            ]
        }
        
        self.logger.debug("Enhanced metadata extractor initialized")
    
    def extract_complexity_level(self, text: str, context: str = "") -> str:
        """
        Extract complexity level from document text and context.
        
        Args:
            text: Text content to analyze
            context: Additional context (e.g., section headers, document structure)
            
        Returns:
            Complexity level: "beginner", "intermediate", or "advanced"
        """
        full_text = f"{context} {text}".lower()
        
        # Score based on indicators
        scores = {'beginner': 0, 'intermediate': 0, 'advanced': 0}
        
        # Check textual indicators
        for level, patterns in self.complexity_indicators.items():
            for pattern in patterns:
                matches = len(pattern.findall(full_text))
                scores[level] += matches
        
        # Check mathematical complexity
        for pattern, level in self.math_complexity_patterns:
            matches = len(pattern.findall(text))
            scores[level] += matches * 2  # Weight math patterns higher
        
        # Additional heuristics
        # Length-based complexity (longer derivations tend to be more advanced)
        if len(text) > 2000:
            scores['advanced'] += 1
        elif len(text) < 500:
            scores['beginner'] += 1
        
        # Equation density
        math_symbols = len(re.findall(r'[∫∂∑∏√±≤≥≠∞∈∉⊂⊆∪∩]', text))
        if math_symbols > 20:
            scores['advanced'] += 2
        elif math_symbols > 5:
            scores['intermediate'] += 1
        
        # Return level with highest score, default to intermediate
        if scores['advanced'] > scores['intermediate'] and scores['advanced'] > scores['beginner']:
            return 'advanced'
        elif scores['beginner'] > scores['intermediate']:
            return 'beginner'
        else:
            return 'intermediate'  # Default for financial mathematics
    
    def extract_prerequisites(self, text: str, ontology: FinancialMathOntology) -> List[str]:
        """
        Extract prerequisite concepts from document text.
        
        Args:
            text: Text content to analyze
            ontology: Financial mathematics ontology for concept mapping
            
        Returns:
            List of prerequisite concept names/IDs
        """
        prerequisites = set()
        
        for pattern in self.prerequisite_patterns:
            matches = pattern.findall(text)
            for match in matches:
                # Clean up the matched text
                prereq_text = match.strip().rstrip('.,;')
                
                # Try to map to existing concepts in ontology
                mapped_concepts = self._map_to_ontology_concepts(prereq_text, ontology)
                prerequisites.update(mapped_concepts)
                
                # Also add the raw text if no mapping found
                if not mapped_concepts:
                    prerequisites.add(prereq_text)
        
        return list(prerequisites)
    
    def extract_domain(self, text: str, context: str = "") -> str:
        """
        Extract domain classification from document text and context.
        
        Args:
            text: Text content to analyze
            context: Additional context (e.g., document title, section headers)
            
        Returns:
            Domain classification: "mathematics", "finance", "economics", "statistics", "optimization"
        """
        full_text = f"{context} {text}".lower()
        
        # Score each domain
        domain_scores = {}
        for domain, patterns in self.domain_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(pattern.findall(full_text))
                score += matches
            domain_scores[domain] = score
        
        # Return domain with highest score, default to finance
        if domain_scores:
            max_domain = max(domain_scores, key=domain_scores.get)
            if domain_scores[max_domain] > 0:
                return max_domain
        
        return 'finance'  # Default for financial mathematics corpus
    
    def _map_to_ontology_concepts(self, prereq_text: str, ontology: FinancialMathOntology) -> List[str]:
        """
        Map prerequisite text to existing concepts in the ontology.
        
        Args:
            prereq_text: Prerequisite text to map
            ontology: Financial mathematics ontology
            
        Returns:
            List of mapped concept names/IDs
        """
        mapped_concepts = []
        prereq_lower = prereq_text.lower()
        
        # Direct name matching
        for concept_id, concept in ontology.concepts.items():
            if concept.name.lower() in prereq_lower or prereq_lower in concept.name.lower():
                mapped_concepts.append(concept.name)
                continue
            
            # Check aliases
            for alias in concept.aliases:
                if alias.lower() in prereq_lower or prereq_lower in alias.lower():
                    mapped_concepts.append(concept.name)
                    break
        
        return mapped_concepts


def get_concept_extractor(settings: Settings, ontology: Optional[FinancialMathOntology] = None) -> ConceptExtractor:
    """
    Factory function to create a concept extractor.
    
    Args:
        settings: Application settings
        ontology: Optional ontology instance (creates new if None)
        
    Returns:
        ConceptExtractor instance
    """
    if ontology is None:
        ontology = FinancialMathOntology(settings)
    
    return ConceptExtractor(settings, ontology)


def get_enhanced_metadata_extractor(settings: Settings) -> EnhancedMetadataExtractor:
    """
    Factory function to create an enhanced metadata extractor.
    
    Args:
        settings: Application settings
        
    Returns:
        EnhancedMetadataExtractor instance
    """
    return EnhancedMetadataExtractor(settings)