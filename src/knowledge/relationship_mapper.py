"""
Relationship mapping algorithms for building knowledge graphs.

This module provides advanced algorithms for mapping relationships between concepts
in financial mathematics documents, including dependency analysis, semantic similarity,
and contextual relationship inference.
"""

import logging
import re
from typing import Dict, List, Optional, Set, Tuple, Union, Any
from dataclasses import dataclass, field
from enum import Enum
import json
from collections import defaultdict, Counter
import networkx as nx

from .ontology import Concept, Relationship, ConceptType, RelationshipType, FinancialMathOntology
from .concept_extractor import ExtractedConcept, ExtractedRelationship, ExtractionMethod
from src.settings import Settings


class RelationshipStrength(Enum):
    """Strength levels for relationships."""
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"
    VERY_STRONG = "very_strong"


@dataclass
class RelationshipScore:
    """Scoring information for a relationship."""
    base_score: float
    context_score: float
    frequency_score: float
    semantic_score: float
    mathematical_score: float
    total_score: float
    strength: RelationshipStrength
    evidence: List[str] = field(default_factory=list)


class RelationshipMapper:
    """
    Advanced relationship mapping for knowledge graph construction.
    
    This class provides sophisticated algorithms for identifying and scoring
    relationships between concepts in financial mathematics documents.
    """
    
    def __init__(self, settings: Settings, ontology: FinancialMathOntology):
        """Initialize the relationship mapper."""
        self.settings = settings
        self.ontology = ontology
        self.logger = logging.getLogger(__name__)
        
        # Initialize relationship scoring parameters
        self.scoring_weights = {
            'base_score': 0.3,
            'context_score': 0.2,
            'frequency_score': 0.15,
            'semantic_score': 0.2,
            'mathematical_score': 0.15
        }
        
        # Relationship strength thresholds
        self.strength_thresholds = {
            RelationshipStrength.WEAK: 0.3,
            RelationshipStrength.MODERATE: 0.5,
            RelationshipStrength.STRONG: 0.7,
            RelationshipStrength.VERY_STRONG: 0.9
        }
        
        # Initialize pattern matchers
        self._initialize_patterns()
        
        # Initialize semantic similarity mappings
        self._initialize_semantic_mappings()
        
        # Relationship co-occurrence tracker
        self.relationship_cooccurrence: Dict[Tuple[str, str], int] = defaultdict(int)
        
        # Mathematical dependency patterns
        self.dependency_patterns = self._compile_dependency_patterns()
        
        self.logger.debug("Relationship mapper initialized")
    
    def _initialize_patterns(self) -> None:
        """Initialize relationship detection patterns."""
        
        # Mathematical dependency patterns
        self.math_dependency_patterns = {
            RelationshipType.DEPENDS_ON: [
                re.compile(r'([A-Za-z_]\w*)\s*=\s*.*?([A-Za-z_]\w*)', re.MULTILINE),
                re.compile(r'([A-Za-z_]\w*)\s*\(\s*([A-Za-z_]\w*)\s*\)', re.MULTILINE),
                re.compile(r'f\s*\(\s*([A-Za-z_]\w*)\s*\)', re.MULTILINE),
            ],
            RelationshipType.COMPOSED_OF: [
                re.compile(r'([A-Za-z_]\w*)\s*=\s*([A-Za-z_]\w*)\s*\+\s*([A-Za-z_]\w*)', re.MULTILINE),
                re.compile(r'([A-Za-z_]\w*)\s*=\s*∑.*?([A-Za-z_]\w*)', re.MULTILINE),
            ],
            RelationshipType.MEASURES: [
                re.compile(r'([A-Za-z_]\w*)\s+measures?\s+([A-Za-z_]\w*)', re.IGNORECASE),
                re.compile(r'([A-Za-z_]\w*)\s+(?:is\s+)?(?:a\s+)?measure\s+of\s+([A-Za-z_]\w*)', re.IGNORECASE),
            ]
        }
        
        # Semantic relationship patterns
        self.semantic_patterns = {
            RelationshipType.DEFINES: [
                re.compile(r'([A-Za-z_]\w*)\s+(?:is\s+)?defined\s+as\s+([^.]+)', re.IGNORECASE),
                re.compile(r'define\s+([A-Za-z_]\w*)\s+as\s+([^.]+)', re.IGNORECASE),
            ],
            RelationshipType.IMPLIES: [
                re.compile(r'([A-Za-z_]\w*)\s+implies\s+([A-Za-z_]\w*)', re.IGNORECASE),
                re.compile(r'if\s+([A-Za-z_]\w*)\s+then\s+([A-Za-z_]\w*)', re.IGNORECASE),
            ],
            RelationshipType.EXTENDS: [
                re.compile(r'([A-Za-z_]\w*)\s+extends\s+([A-Za-z_]\w*)', re.IGNORECASE),
                re.compile(r'([A-Za-z_]\w*)\s+(?:is\s+)?(?:an?\s+)?extension\s+of\s+([A-Za-z_]\w*)', re.IGNORECASE),
            ]
        }
        
        # Financial relationship patterns
        self.financial_patterns = {
            RelationshipType.OPTIMIZES: [
                re.compile(r'(?:minimize|maximize)\s+([A-Za-z_]\w*)', re.IGNORECASE),
                re.compile(r'([A-Za-z_]\w*)\s+(?:is\s+)?optimized', re.IGNORECASE),
            ],
            RelationshipType.CONSTRAINS: [
                re.compile(r'([A-Za-z_]\w*)\s+constrained?\s+by\s+([A-Za-z_]\w*)', re.IGNORECASE),
                re.compile(r'subject\s+to\s+([A-Za-z_]\w*)', re.IGNORECASE),
            ],
            RelationshipType.AFFECTS: [
                re.compile(r'([A-Za-z_]\w*)\s+affects?\s+([A-Za-z_]\w*)', re.IGNORECASE),
                re.compile(r'([A-Za-z_]\w*)\s+(?:has\s+)?(?:an?\s+)?impact\s+on\s+([A-Za-z_]\w*)', re.IGNORECASE),
            ]
        }
    
    def _initialize_semantic_mappings(self) -> None:
        """Initialize semantic similarity mappings."""
        
        # Concept similarity groups
        self.similarity_groups = {
            'risk_concepts': ['risk', 'volatility', 'variance', 'standard_deviation', 'uncertainty'],
            'return_concepts': ['return', 'yield', 'profit', 'gain', 'performance'],
            'portfolio_concepts': ['portfolio', 'asset_mix', 'allocation', 'diversification'],
            'optimization_concepts': ['optimization', 'minimization', 'maximization', 'efficient'],
            'metric_concepts': ['ratio', 'measure', 'metric', 'indicator', 'index'],
            'mathematical_concepts': ['equation', 'formula', 'function', 'expression', 'variable']
        }
        
        # Relationship type similarities
        self.relationship_similarities = {
            RelationshipType.DEPENDS_ON: [RelationshipType.COMPOSED_OF, RelationshipType.DERIVES_FROM],
            RelationshipType.MEASURES: [RelationshipType.AFFECTS, RelationshipType.CORRELATES_WITH],
            RelationshipType.OPTIMIZES: [RelationshipType.MAXIMIZES, RelationshipType.MINIMIZES],
            RelationshipType.DEFINES: [RelationshipType.EQUALS, RelationshipType.MENTIONS],
        }
    
    def _compile_dependency_patterns(self) -> Dict[str, List[re.Pattern]]:
        """Compile mathematical dependency patterns."""
        patterns = {}
        
        # Variable assignment patterns
        patterns['assignment'] = [
            re.compile(r'([A-Za-z_]\w*)\s*=\s*([^=\n]+)', re.MULTILINE),
            re.compile(r'([A-Za-z_]\w*)\s*:=\s*([^=\n]+)', re.MULTILINE),
        ]
        
        # Function dependency patterns
        patterns['function'] = [
            re.compile(r'([A-Za-z_]\w*)\s*\(\s*([A-Za-z_,\s\w]*)\s*\)', re.MULTILINE),
            re.compile(r'([A-Za-z_]\w*)\s*=\s*f\s*\(\s*([A-Za-z_,\s\w]*)\s*\)', re.MULTILINE),
        ]
        
        # Matrix/vector operations
        patterns['matrix'] = [
            re.compile(r'([A-Za-z_]\w*)\s*=\s*([A-Za-z_]\w*)\s*[\'T]\s*([A-Za-z_]\w*)', re.MULTILINE),
            re.compile(r'([A-Za-z_]\w*)\s*=\s*([A-Za-z_]\w*)\s*\*\s*([A-Za-z_]\w*)', re.MULTILINE),
        ]
        
        # Summation patterns
        patterns['summation'] = [
            re.compile(r'([A-Za-z_]\w*)\s*=\s*∑.*?([A-Za-z_]\w*)', re.MULTILINE),
            re.compile(r'([A-Za-z_]\w*)\s*=\s*\\sum.*?([A-Za-z_]\w*)', re.MULTILINE),
        ]
        
        return patterns
    
    def map_relationships(self, extracted_concepts: List[ExtractedConcept],
                         extracted_relationships: List[ExtractedRelationship],
                         document_texts: Dict[int, str]) -> List[Relationship]:
        """
        Map and score relationships between concepts.
        
        Args:
            extracted_concepts: List of extracted concepts
            extracted_relationships: List of initially extracted relationships
            document_texts: Dictionary mapping page numbers to full text
            
        Returns:
            List of scored and validated relationships
        """
        # Create concept lookup
        concept_lookup = {concept.name: concept for concept in extracted_concepts}
        
        # Initialize relationship candidates
        relationship_candidates = defaultdict(list)
        
        # Add initially extracted relationships
        for rel in extracted_relationships:
            key = (rel.source_concept, rel.target_concept, rel.relationship_type)
            relationship_candidates[key].append(rel)
        
        # Discover additional relationships
        additional_relationships = self._discover_additional_relationships(
            extracted_concepts, document_texts
        )
        
        for rel in additional_relationships:
            key = (rel.source_concept, rel.target_concept, rel.relationship_type)
            relationship_candidates[key].append(rel)
        
        # Score and validate relationships
        final_relationships = []
        
        for (source, target, rel_type), candidates in relationship_candidates.items():
            if source in concept_lookup and target in concept_lookup:
                # Calculate relationship score
                score = self._calculate_relationship_score(
                    candidates, concept_lookup[source], concept_lookup[target], document_texts
                )
                
                # Only keep relationships above threshold
                if score.total_score >= self.strength_thresholds[RelationshipStrength.WEAK]:
                    relationship = Relationship(
                        source_concept_id=source,
                        target_concept_id=target,
                        relationship_type=rel_type,
                        confidence=score.total_score,
                        properties={
                            'strength': score.strength.value,
                            'base_score': score.base_score,
                            'context_score': score.context_score,
                            'frequency_score': score.frequency_score,
                            'semantic_score': score.semantic_score,
                            'mathematical_score': score.mathematical_score,
                            'evidence': score.evidence
                        },
                        source_document=candidates[0].source_document,
                        source_page=candidates[0].source_page,
                        context=candidates[0].context
                    )
                    final_relationships.append(relationship)
        
        # Apply relationship filtering and enhancement
        filtered_relationships = self._filter_and_enhance_relationships(
            final_relationships, concept_lookup
        )
        
        self.logger.info(f"Mapped {len(filtered_relationships)} relationships from {len(relationship_candidates)} candidates")
        
        return filtered_relationships
    
    def _discover_additional_relationships(self, extracted_concepts: List[ExtractedConcept],
                                         document_texts: Dict[int, str]) -> List[ExtractedRelationship]:
        """Discover additional relationships through advanced pattern matching."""
        additional_relationships = []
        
        # Create concept name lookup
        concept_names = {concept.name for concept in extracted_concepts}
        
        # Analyze each page of text
        for page_num, text in document_texts.items():
            # Mathematical dependency analysis
            math_relationships = self._analyze_mathematical_dependencies(
                text, concept_names, page_num
            )
            additional_relationships.extend(math_relationships)
            
            # Semantic relationship analysis
            semantic_relationships = self._analyze_semantic_relationships(
                text, concept_names, page_num
            )
            additional_relationships.extend(semantic_relationships)
            
            # Co-occurrence analysis
            cooccurrence_relationships = self._analyze_concept_cooccurrence(
                text, concept_names, page_num
            )
            additional_relationships.extend(cooccurrence_relationships)
        
        return additional_relationships
    
    def _analyze_mathematical_dependencies(self, text: str, concept_names: Set[str], page_num: int) -> List[ExtractedRelationship]:
        """Analyze mathematical dependencies in text."""
        relationships = []
        
        # Analyze assignment patterns
        for pattern in self.dependency_patterns['assignment']:
            matches = pattern.findall(text)
            for match in matches:
                if len(match) >= 2:
                    lhs, rhs = match[0], match[1]
                    
                    # Extract variables from RHS
                    rhs_variables = re.findall(r'[A-Za-z_]\w*', rhs)
                    
                    # Create dependency relationships
                    for var in rhs_variables:
                        if lhs in concept_names and var in concept_names and lhs != var:
                            relationship = ExtractedRelationship(
                                source_concept=lhs,
                                target_concept=var,
                                relationship_type=RelationshipType.DEPENDS_ON,
                                source_page=page_num,
                                confidence=0.8,
                                context=f"Mathematical dependency: {lhs} = {rhs}",
                                extraction_method=ExtractionMethod.MATH_DETECTION
                            )
                            relationships.append(relationship)
        
        # Analyze function patterns
        for pattern in self.dependency_patterns['function']:
            matches = pattern.findall(text)
            for match in matches:
                if len(match) >= 2:
                    func_name, args = match[0], match[1]
                    
                    # Extract argument variables
                    arg_variables = re.findall(r'[A-Za-z_]\w*', args)
                    
                    # Create function dependency relationships
                    for var in arg_variables:
                        if func_name in concept_names and var in concept_names:
                            relationship = ExtractedRelationship(
                                source_concept=func_name,
                                target_concept=var,
                                relationship_type=RelationshipType.DEPENDS_ON,
                                source_page=page_num,
                                confidence=0.9,
                                context=f"Function dependency: {func_name}({args})",
                                extraction_method=ExtractionMethod.MATH_DETECTION
                            )
                            relationships.append(relationship)
        
        return relationships
    
    def _analyze_semantic_relationships(self, text: str, concept_names: Set[str], page_num: int) -> List[ExtractedRelationship]:
        """Analyze semantic relationships in text."""
        relationships = []
        
        # Analyze each semantic pattern group
        for rel_type, patterns in self.semantic_patterns.items():
            for pattern in patterns:
                matches = pattern.findall(text)
                for match in matches:
                    if len(match) >= 2:
                        source, target = match[0], match[1]
                        
                        # Extract concept names from target
                        target_concepts = re.findall(r'[A-Za-z_]\w*', target)
                        
                        for target_concept in target_concepts:
                            if source in concept_names and target_concept in concept_names:
                                relationship = ExtractedRelationship(
                                    source_concept=source,
                                    target_concept=target_concept,
                                    relationship_type=rel_type,
                                    source_page=page_num,
                                    confidence=0.7,
                                    context=f"Semantic relationship: {source} -> {target}",
                                    extraction_method=ExtractionMethod.SEMANTIC_ANALYSIS
                                )
                                relationships.append(relationship)
        
        return relationships
    
    def _analyze_concept_cooccurrence(self, text: str, concept_names: Set[str], page_num: int) -> List[ExtractedRelationship]:
        """Analyze concept co-occurrence patterns."""
        relationships = []
        
        # Tokenize text
        words = re.findall(r'[A-Za-z_]\w*', text.lower())
        
        # Find concept positions
        concept_positions = {}
        for i, word in enumerate(words):
            if word in concept_names:
                if word not in concept_positions:
                    concept_positions[word] = []
                concept_positions[word].append(i)
        
        # Analyze co-occurrence within windows
        window_size = 20
        for concept1, positions1 in concept_positions.items():
            for concept2, positions2 in concept_positions.items():
                if concept1 != concept2:
                    # Count co-occurrences
                    cooccurrences = 0
                    for pos1 in positions1:
                        for pos2 in positions2:
                            if abs(pos1 - pos2) <= window_size:
                                cooccurrences += 1
                    
                    # Create relationship if significant co-occurrence
                    if cooccurrences >= 2:
                        self.relationship_cooccurrence[(concept1, concept2)] += cooccurrences
                        
                        relationship = ExtractedRelationship(
                            source_concept=concept1,
                            target_concept=concept2,
                            relationship_type=RelationshipType.MENTIONS,
                            source_page=page_num,
                            confidence=min(0.6, cooccurrences * 0.1),
                            context=f"Co-occurrence: {cooccurrences} times within {window_size} words",
                            extraction_method=ExtractionMethod.CONTEXT_ANALYSIS
                        )
                        relationships.append(relationship)
        
        return relationships
    
    def _calculate_relationship_score(self, candidates: List[ExtractedRelationship],
                                    source_concept: ExtractedConcept,
                                    target_concept: ExtractedConcept,
                                    document_texts: Dict[int, str]) -> RelationshipScore:
        """Calculate a comprehensive score for a relationship."""
        
        # Base score from extraction confidence
        base_score = max(candidate.confidence for candidate in candidates)
        
        # Context score based on extraction method quality
        context_score = self._calculate_context_score(candidates)
        
        # Frequency score based on how often relationship appears
        frequency_score = min(1.0, len(candidates) * 0.2)
        
        # Semantic score based on concept similarity
        semantic_score = self._calculate_semantic_similarity(source_concept, target_concept)
        
        # Mathematical score based on mathematical relationship patterns
        mathematical_score = self._calculate_mathematical_score(candidates, document_texts)
        
        # Calculate weighted total score
        total_score = (
            base_score * self.scoring_weights['base_score'] +
            context_score * self.scoring_weights['context_score'] +
            frequency_score * self.scoring_weights['frequency_score'] +
            semantic_score * self.scoring_weights['semantic_score'] +
            mathematical_score * self.scoring_weights['mathematical_score']
        )
        
        # Determine relationship strength
        strength = RelationshipStrength.WEAK
        for strength_level, threshold in sorted(self.strength_thresholds.items(), 
                                              key=lambda x: x[1], reverse=True):
            if total_score >= threshold:
                strength = strength_level
                break
        
        # Collect evidence
        evidence = []
        for candidate in candidates:
            if candidate.context:
                evidence.append(f"{candidate.extraction_method.value}: {candidate.context[:100]}")
        
        return RelationshipScore(
            base_score=base_score,
            context_score=context_score,
            frequency_score=frequency_score,
            semantic_score=semantic_score,
            mathematical_score=mathematical_score,
            total_score=total_score,
            strength=strength,
            evidence=evidence
        )
    
    def _calculate_context_score(self, candidates: List[ExtractedRelationship]) -> float:
        """Calculate context quality score."""
        method_scores = {
            ExtractionMethod.MATH_DETECTION: 1.0,
            ExtractionMethod.SEMANTIC_ANALYSIS: 0.8,
            ExtractionMethod.REGEX_PATTERN: 0.6,
            ExtractionMethod.CONTEXT_ANALYSIS: 0.4,
            ExtractionMethod.OCR_FALLBACK: 0.3
        }
        
        if not candidates:
            return 0.0
        
        # Return best method score
        return max(method_scores.get(candidate.extraction_method, 0.5) for candidate in candidates)
    
    def _calculate_semantic_similarity(self, source_concept: ExtractedConcept, 
                                     target_concept: ExtractedConcept) -> float:
        """Calculate semantic similarity between concepts."""
        # Check if concepts are in same similarity group
        for group_concepts in self.similarity_groups.values():
            if source_concept.name in group_concepts and target_concept.name in group_concepts:
                return 0.8
        
        # Check concept types
        if source_concept.concept_type == target_concept.concept_type:
            return 0.6
        
        # Check compatible concept types
        compatible_types = [
            (ConceptType.VARIABLE, ConceptType.EQUATION),
            (ConceptType.FORMULA, ConceptType.FUNCTION),
            (ConceptType.METRIC, ConceptType.PERFORMANCE),
            (ConceptType.OPTIMIZATION, ConceptType.CONSTRAINT)
        ]
        
        for type1, type2 in compatible_types:
            if ((source_concept.concept_type == type1 and target_concept.concept_type == type2) or
                (source_concept.concept_type == type2 and target_concept.concept_type == type1)):
                return 0.4
        
        return 0.2
    
    def _calculate_mathematical_score(self, candidates: List[ExtractedRelationship],
                                    document_texts: Dict[int, str]) -> float:
        """Calculate mathematical relationship score."""
        math_score = 0.0
        
        for candidate in candidates:
            if candidate.extraction_method == ExtractionMethod.MATH_DETECTION:
                math_score += 0.5
            
            # Check for mathematical context
            if candidate.context:
                if any(symbol in candidate.context for symbol in ['=', '+', '-', '*', '/', '^']):
                    math_score += 0.3
                
                if any(symbol in candidate.context for symbol in ['∑', '∫', '∏', '∂']):
                    math_score += 0.4
        
        return min(1.0, math_score)
    
    def _filter_and_enhance_relationships(self, relationships: List[Relationship],
                                        concept_lookup: Dict[str, ExtractedConcept]) -> List[Relationship]:
        """Filter and enhance relationships using graph analysis."""
        
        # Create NetworkX graph for analysis
        G = nx.DiGraph()
        
        # Add nodes and edges
        for rel in relationships:
            G.add_node(rel.source_concept_id)
            G.add_node(rel.target_concept_id)
            G.add_edge(rel.source_concept_id, rel.target_concept_id, 
                      relationship=rel, weight=rel.confidence)
        
        # Filter out weak relationships in dense areas
        filtered_relationships = []
        
        for rel in relationships:
            # Check if relationship is supported by graph structure
            source_degree = G.degree(rel.source_concept_id)
            target_degree = G.degree(rel.target_concept_id)
            
            # Keep strong relationships regardless of structure
            if rel.confidence >= self.strength_thresholds[RelationshipStrength.STRONG]:
                filtered_relationships.append(rel)
                continue
            
            # For weaker relationships, require structural support
            if source_degree >= 2 and target_degree >= 2:
                # Check for common neighbors (triangular relationships)
                source_neighbors = set(G.neighbors(rel.source_concept_id))
                target_neighbors = set(G.neighbors(rel.target_concept_id))
                common_neighbors = source_neighbors & target_neighbors
                
                if common_neighbors or rel.confidence >= self.strength_thresholds[RelationshipStrength.MODERATE]:
                    filtered_relationships.append(rel)
            else:
                # Keep if moderate confidence
                if rel.confidence >= self.strength_thresholds[RelationshipStrength.MODERATE]:
                    filtered_relationships.append(rel)
        
        return filtered_relationships
    
    def analyze_relationship_patterns(self, relationships: List[Relationship]) -> Dict[str, Any]:
        """Analyze patterns in the relationship network."""
        
        # Create graph for analysis
        G = nx.DiGraph()
        
        for rel in relationships:
            G.add_edge(rel.source_concept_id, rel.target_concept_id, 
                      relationship_type=rel.relationship_type.value,
                      confidence=rel.confidence)
        
        # Calculate network metrics
        analysis = {
            'total_relationships': len(relationships),
            'total_concepts': len(G.nodes()),
            'avg_degree': sum(dict(G.degree()).values()) / len(G.nodes()) if G.nodes() else 0,
            'density': nx.density(G),
            'is_connected': nx.is_weakly_connected(G),
            'strongly_connected_components': len(list(nx.strongly_connected_components(G))),
            'relationship_types': Counter(rel.relationship_type.value for rel in relationships),
            'avg_confidence': sum(rel.confidence for rel in relationships) / len(relationships) if relationships else 0
        }
        
        # Find central concepts
        if G.nodes():
            centrality = nx.degree_centrality(G)
            analysis['most_central_concepts'] = sorted(centrality.items(), 
                                                     key=lambda x: x[1], reverse=True)[:10]
        
        return analysis


def get_relationship_mapper(settings: Settings, ontology: FinancialMathOntology) -> RelationshipMapper:
    """
    Factory function to create a relationship mapper.
    
    Args:
        settings: Application settings
        ontology: Ontology instance
        
    Returns:
        RelationshipMapper instance
    """
    return RelationshipMapper(settings, ontology)