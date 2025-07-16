"""
Concept deduplication for handling duplicate concepts across document types.
"""

import hashlib
import logging
from collections import defaultdict
from typing import Any, Dict, List, Optional, Set, Tuple

from ..knowledge.concept import Concept


class ConceptDeduplicator:
    """
    Deduplicates concepts across different document types.
    
    Uses various similarity metrics and heuristics to identify and merge
    duplicate concepts that may appear across different document formats.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the concept deduplicator.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Deduplication configuration
        self.similarity_threshold = self.config.get('similarity_threshold', 0.85)
        self.exact_match_fields = self.config.get('exact_match_fields', ['name', 'symbol'])
        self.fuzzy_match_fields = self.config.get('fuzzy_match_fields', ['description', 'definition'])
        self.ignore_case = self.config.get('ignore_case', True)
        self.normalize_whitespace = self.config.get('normalize_whitespace', True)
        
        # Caching for performance
        self.concept_hashes = {}
        self.similarity_cache = {}
        
        # Statistics
        self.stats = {
            'concepts_processed': 0,
            'duplicates_found': 0,
            'concepts_merged': 0,
            'exact_matches': 0,
            'fuzzy_matches': 0,
        }
    
    def deduplicate_concepts(self, concepts: List[Concept]) -> List[Concept]:
        """
        Deduplicate a list of concepts.
        
        Args:
            concepts: List of concepts to deduplicate
            
        Returns:
            List of deduplicated concepts
        """
        if not concepts:
            return []
        
        self.logger.info(f"Starting deduplication of {len(concepts)} concepts")
        start_count = len(concepts)
        
        # Group concepts by potential duplicates
        duplicate_groups = self._find_duplicate_groups(concepts)
        
        # Merge duplicate groups
        deduplicated_concepts = []
        for group in duplicate_groups:
            if len(group) > 1:
                merged_concept = self._merge_concepts(group)
                deduplicated_concepts.append(merged_concept)
                self.stats['concepts_merged'] += len(group) - 1
            else:
                deduplicated_concepts.append(group[0])
        
        self.stats['concepts_processed'] += start_count
        self.stats['duplicates_found'] += start_count - len(deduplicated_concepts)
        
        self.logger.info(f"Deduplication complete: {start_count} -> {len(deduplicated_concepts)} concepts")
        return deduplicated_concepts
    
    def _find_duplicate_groups(self, concepts: List[Concept]) -> List[List[Concept]]:
        """
        Find groups of duplicate concepts.
        
        Args:
            concepts: List of concepts to analyze
            
        Returns:
            List of concept groups (each group contains duplicates)
        """
        # Build similarity graph
        similarity_graph = defaultdict(set)
        
        for i, concept1 in enumerate(concepts):
            for j, concept2 in enumerate(concepts[i + 1:], i + 1):
                similarity = self._calculate_similarity(concept1, concept2)
                if similarity >= self.similarity_threshold:
                    similarity_graph[i].add(j)
                    similarity_graph[j].add(i)
        
        # Find connected components (groups of similar concepts)
        visited = set()
        groups = []
        
        for i in range(len(concepts)):
            if i not in visited:
                group = []
                self._dfs_collect_group(i, similarity_graph, visited, group)
                groups.append([concepts[idx] for idx in group])
        
        return groups
    
    def _dfs_collect_group(self, node: int, graph: Dict[int, Set[int]], visited: Set[int], group: List[int]) -> None:
        """
        Collect a group using depth-first search.
        
        Args:
            node: Current node index
            graph: Similarity graph
            visited: Set of visited nodes
            group: Current group being built
        """
        visited.add(node)
        group.append(node)
        
        for neighbor in graph[node]:
            if neighbor not in visited:
                self._dfs_collect_group(neighbor, graph, visited, group)
    
    def _calculate_similarity(self, concept1: Concept, concept2: Concept) -> float:
        """
        Calculate similarity between two concepts.
        
        Args:
            concept1: First concept
            concept2: Second concept
            
        Returns:
            Similarity score (0.0 to 1.0)
        """
        # Check cache first
        cache_key = self._get_similarity_cache_key(concept1, concept2)
        if cache_key in self.similarity_cache:
            return self.similarity_cache[cache_key]
        
        # Calculate similarity
        similarity = self._compute_similarity(concept1, concept2)
        
        # Cache result
        self.similarity_cache[cache_key] = similarity
        
        return similarity
    
    def _compute_similarity(self, concept1: Concept, concept2: Concept) -> float:
        """
        Compute similarity between two concepts.
        
        Args:
            concept1: First concept
            concept2: Second concept
            
        Returns:
            Similarity score (0.0 to 1.0)
        """
        # Check for exact matches first
        for field in self.exact_match_fields:
            value1 = getattr(concept1, field, None)
            value2 = getattr(concept2, field, None)
            
            if value1 and value2:
                if self._normalize_text(value1) == self._normalize_text(value2):
                    self.stats['exact_matches'] += 1
                    return 1.0
        
        # Calculate weighted similarity across different fields
        field_weights = {
            'name': 0.4,
            'symbol': 0.3,
            'description': 0.2,
            'definition': 0.1,
        }
        
        total_weight = 0
        weighted_similarity = 0
        
        for field, weight in field_weights.items():
            value1 = getattr(concept1, field, None)
            value2 = getattr(concept2, field, None)
            
            if value1 and value2:
                field_similarity = self._calculate_text_similarity(value1, value2)
                weighted_similarity += field_similarity * weight
                total_weight += weight
        
        # Normalize by actual weight used
        if total_weight > 0:
            final_similarity = weighted_similarity / total_weight
            if final_similarity >= self.similarity_threshold:
                self.stats['fuzzy_matches'] += 1
            return final_similarity
        
        return 0.0
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity between two text strings.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score (0.0 to 1.0)
        """
        # Normalize texts
        norm_text1 = self._normalize_text(text1)
        norm_text2 = self._normalize_text(text2)
        
        if norm_text1 == norm_text2:
            return 1.0
        
        # Use Jaccard similarity on word sets
        words1 = set(norm_text1.split())
        words2 = set(norm_text2.split())
        
        if not words1 and not words2:
            return 1.0
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    def _normalize_text(self, text: str) -> str:
        """
        Normalize text for comparison.
        
        Args:
            text: Text to normalize
            
        Returns:
            Normalized text
        """
        if not text:
            return ""
        
        normalized = text
        
        if self.ignore_case:
            normalized = normalized.lower()
        
        if self.normalize_whitespace:
            import re
            normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    def _merge_concepts(self, concepts: List[Concept]) -> Concept:
        """
        Merge a group of duplicate concepts into a single concept.
        
        Args:
            concepts: List of concepts to merge
            
        Returns:
            Merged concept
        """
        if len(concepts) == 1:
            return concepts[0]
        
        # Use the concept with the most complete information as base
        base_concept = max(concepts, key=self._concept_completeness_score)
        
        # Merge information from other concepts
        merged_concept = Concept(
            name=base_concept.name,
            concept_type=base_concept.concept_type,
            description=self._merge_text_field([c.description for c in concepts if c.description]),
            definition=self._merge_text_field([c.definition for c in concepts if c.definition]),
            symbol=base_concept.symbol or next((c.symbol for c in concepts if c.symbol), None),
            properties=self._merge_properties([c.properties for c in concepts if c.properties]),
            relationships=self._merge_relationships([c.relationships for c in concepts if c.relationships]),
            examples=self._merge_examples([c.examples for c in concepts if c.examples]),
            confidence=max(c.confidence for c in concepts if hasattr(c, 'confidence')),
        )
        
        # Add source tracking
        sources = []
        for concept in concepts:
            if hasattr(concept, 'source_documents'):
                sources.extend(concept.source_documents)
            elif hasattr(concept, 'source'):
                sources.append(concept.source)
        
        if sources:
            merged_concept.source_documents = list(set(sources))
        
        # Add merge metadata
        merged_concept.merged_from = len(concepts)
        merged_concept.merge_confidence = min(c.confidence for c in concepts if hasattr(c, 'confidence'))
        
        return merged_concept
    
    def _concept_completeness_score(self, concept: Concept) -> int:
        """
        Calculate a completeness score for a concept.
        
        Args:
            concept: Concept to score
            
        Returns:
            Completeness score (higher is more complete)
        """
        score = 0
        
        if concept.name:
            score += 2
        if concept.description:
            score += len(concept.description.split()) // 5  # Longer descriptions are better
        if concept.definition:
            score += len(concept.definition.split()) // 3
        if concept.symbol:
            score += 1
        if concept.properties:
            score += len(concept.properties)
        if concept.relationships:
            score += len(concept.relationships)
        if concept.examples:
            score += len(concept.examples)
        
        return score
    
    def _merge_text_field(self, values: List[str]) -> str:
        """
        Merge multiple text values, preferring the longest.
        
        Args:
            values: List of text values
            
        Returns:
            Merged text value
        """
        if not values:
            return ""
        
        # Remove duplicates while preserving order
        unique_values = []
        seen = set()
        
        for value in values:
            normalized = self._normalize_text(value)
            if normalized not in seen:
                unique_values.append(value)
                seen.add(normalized)
        
        # Return the longest unique value
        return max(unique_values, key=len) if unique_values else ""
    
    def _merge_properties(self, property_lists: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Merge multiple property dictionaries.
        
        Args:
            property_lists: List of property dictionaries
            
        Returns:
            Merged properties dictionary
        """
        merged = {}
        
        for properties in property_lists:
            if properties:
                for key, value in properties.items():
                    if key not in merged:
                        merged[key] = value
                    elif isinstance(value, list) and isinstance(merged[key], list):
                        # Merge lists and remove duplicates
                        merged[key] = list(set(merged[key] + value))
                    elif value != merged[key]:
                        # Different values, store as list
                        if not isinstance(merged[key], list):
                            merged[key] = [merged[key]]
                        if value not in merged[key]:
                            merged[key].append(value)
        
        return merged
    
    def _merge_relationships(self, relationship_lists: List[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """
        Merge multiple relationship lists.
        
        Args:
            relationship_lists: List of relationship lists
            
        Returns:
            Merged relationships list
        """
        merged = []
        seen_relationships = set()
        
        for relationships in relationship_lists:
            if relationships:
                for relationship in relationships:
                    # Create a normalized key for deduplication
                    rel_key = (
                        relationship.get('type', ''),
                        relationship.get('target', ''),
                        relationship.get('direction', '')
                    )
                    
                    if rel_key not in seen_relationships:
                        merged.append(relationship)
                        seen_relationships.add(rel_key)
        
        return merged
    
    def _merge_examples(self, example_lists: List[List[str]]) -> List[str]:
        """
        Merge multiple example lists.
        
        Args:
            example_lists: List of example lists
            
        Returns:
            Merged examples list
        """
        merged = []
        seen_examples = set()
        
        for examples in example_lists:
            if examples:
                for example in examples:
                    normalized = self._normalize_text(example)
                    if normalized not in seen_examples:
                        merged.append(example)
                        seen_examples.add(normalized)
        
        return merged
    
    def _get_similarity_cache_key(self, concept1: Concept, concept2: Concept) -> str:
        """
        Generate a cache key for concept similarity.
        
        Args:
            concept1: First concept
            concept2: Second concept
            
        Returns:
            Cache key string
        """
        # Create deterministic hash based on concept content
        content1 = f"{concept1.name}|{concept1.symbol}|{concept1.description}"
        content2 = f"{concept2.name}|{concept2.symbol}|{concept2.description}"
        
        # Sort to ensure same key regardless of order
        contents = sorted([content1, content2])
        combined = "|".join(contents)
        
        return hashlib.md5(combined.encode()).hexdigest()
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get deduplication statistics.
        
        Returns:
            Statistics dictionary
        """
        return self.stats.copy()
    
    def reset_statistics(self) -> None:
        """Reset deduplication statistics."""
        self.stats = {
            'concepts_processed': 0,
            'duplicates_found': 0,
            'concepts_merged': 0,
            'exact_matches': 0,
            'fuzzy_matches': 0,
        }
    
    def clear_caches(self) -> None:
        """Clear internal caches."""
        self.concept_hashes.clear()
        self.similarity_cache.clear()


class DocumentTypeAwareDedupicator(ConceptDeduplicator):
    """
    Enhanced deduplicator that considers document types in deduplication logic.
    
    Provides different deduplication strategies based on the source document types.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the document type aware deduplicator."""
        super().__init__(config)
        
        # Document type specific configuration
        self.type_specific_thresholds = self.config.get('type_specific_thresholds', {
            'pdf_pdf': 0.9,      # Same format, higher threshold
            'pdf_html': 0.8,     # Different formats, lower threshold
            'latex_pdf': 0.85,   # Related formats, medium threshold
            'docx_html': 0.75,   # Very different formats, lower threshold
        })
        
        self.type_priority = self.config.get('type_priority', {
            'pdf': 1.0,
            'latex': 0.9,
            'docx': 0.8,
            'html': 0.7,
            'xml': 0.6,
        })
    
    def _compute_similarity(self, concept1: Concept, concept2: Concept) -> float:
        """
        Compute similarity with document type awareness.
        
        Args:
            concept1: First concept
            concept2: Second concept
            
        Returns:
            Similarity score adjusted for document types
        """
        # Get base similarity
        base_similarity = super()._compute_similarity(concept1, concept2)
        
        # Get document types
        type1 = self._get_concept_document_type(concept1)
        type2 = self._get_concept_document_type(concept2)
        
        # Adjust threshold based on document types
        type_pair_key = f"{type1}_{type2}" if type1 <= type2 else f"{type2}_{type1}"
        adjusted_threshold = self.type_specific_thresholds.get(
            type_pair_key, 
            self.similarity_threshold
        )
        
        # Apply document type penalty/bonus
        if type1 == type2:
            # Same document type, small bonus
            base_similarity *= 1.05
        else:
            # Different document types, small penalty
            base_similarity *= 0.95
        
        return base_similarity
    
    def _get_concept_document_type(self, concept: Concept) -> str:
        """
        Get the document type for a concept.
        
        Args:
            concept: Concept to check
            
        Returns:
            Document type string
        """
        if hasattr(concept, 'source_document_type'):
            return concept.source_document_type.lower()
        
        if hasattr(concept, 'source_documents') and concept.source_documents:
            # Infer from file extension
            source = concept.source_documents[0]
            if isinstance(source, str):
                extension = source.split('.')[-1].lower()
                type_mapping = {
                    'pdf': 'pdf',
                    'html': 'html',
                    'htm': 'html',
                    'docx': 'docx',
                    'tex': 'latex',
                    'latex': 'latex',
                    'xml': 'xml',
                }
                return type_mapping.get(extension, 'unknown')
        
        return 'unknown'
    
    def _merge_concepts(self, concepts: List[Concept]) -> Concept:
        """
        Merge concepts with document type priority.
        
        Args:
            concepts: List of concepts to merge
            
        Returns:
            Merged concept
        """
        # Sort concepts by document type priority
        prioritized_concepts = sorted(
            concepts,
            key=lambda c: (
                self.type_priority.get(self._get_concept_document_type(c), 0),
                self._concept_completeness_score(c)
            ),
            reverse=True
        )
        
        # Use the highest priority concept as base
        base_concept = prioritized_concepts[0]
        
        # Perform standard merge
        merged_concept = super()._merge_concepts(concepts)
        
        # Preserve priority information
        merged_concept.primary_source_type = self._get_concept_document_type(base_concept)
        merged_concept.source_types = list(set(
            self._get_concept_document_type(c) for c in concepts
        ))
        
        return merged_concept