"""
Cache validation and repair mechanisms for enrichment consistency.

This module provides functionality to detect and repair inconsistent
enrichment data in the concept cache, ensuring consistent behavior
across the knowledge graph system.
"""

import logging
import time
from typing import Dict, List, Set, Tuple, Optional, Any
from collections import defaultdict
import json

from .concept_cache import ConceptCache
from .external_ontologies import ExternalConceptData
from .utils import normalize_concept_name, get_concept_variants, generate_cache_key


logger = logging.getLogger(__name__)


class CacheValidator:
    """Validates and repairs concept cache for consistency."""
    
    def __init__(self, cache: ConceptCache):
        """
        Initialize cache validator.
        
        Args:
            cache: ConceptCache instance to validate
        """
        self.cache = cache
        self.validation_results = {}
        
    def validate_cache_consistency(self) -> Dict[str, Any]:
        """
        Validate cache consistency and return detailed results.
        
        Returns:
            Dictionary with validation results including:
            - orphaned_variants: Concept variants that should share cache entries
            - invalid_entries: Cache entries with invalid data
            - normalization_issues: Entries that don't follow normalization rules
            - duplicate_concepts: Concepts cached under multiple keys
        """
        logger.info("Starting cache consistency validation...")
        
        results = {
            'orphaned_variants': [],
            'invalid_entries': [],
            'normalization_issues': [],
            'duplicate_concepts': [],
            'total_entries': 0,
            'issues_found': 0
        }
        
        # Get all cache entries
        all_entries = self._get_all_cache_entries()
        results['total_entries'] = len(all_entries)
        
        # Group entries by concept to find variants
        concept_groups = self._group_entries_by_concept(all_entries)
        
        # Check for orphaned variants
        orphaned = self._find_orphaned_variants(concept_groups)
        results['orphaned_variants'] = orphaned
        
        # Check for invalid entries
        invalid = self._find_invalid_entries(all_entries)
        results['invalid_entries'] = invalid
        
        # Check for normalization issues
        normalization = self._find_normalization_issues(all_entries)
        results['normalization_issues'] = normalization
        
        # Check for duplicate concepts
        duplicates = self._find_duplicate_concepts(concept_groups)
        results['duplicate_concepts'] = duplicates
        
        results['issues_found'] = (
            len(orphaned) + len(invalid) + 
            len(normalization) + len(duplicates)
        )
        
        self.validation_results = results
        
        logger.info(f"Cache validation complete. Found {results['issues_found']} issues "
                   f"in {results['total_entries']} cache entries.")
        
        return results
    
    def repair_inconsistent_entries(self, dry_run: bool = False) -> Dict[str, Any]:
        """
        Repair inconsistent cache entries.
        
        Args:
            dry_run: If True, only simulate repairs without making changes
            
        Returns:
            Dictionary with repair results
        """
        if not self.validation_results:
            self.validate_cache_consistency()
        
        logger.info(f"Starting cache repair {'(dry run)' if dry_run else ''}...")
        
        repair_results = {
            'orphaned_repaired': 0,
            'invalid_removed': 0,
            'normalization_fixed': 0,
            'duplicates_merged': 0,
            'actions_taken': []
        }
        
        # Repair orphaned variants
        orphaned_count = self._repair_orphaned_variants(dry_run)
        repair_results['orphaned_repaired'] = orphaned_count
        
        # Remove invalid entries
        invalid_count = self._remove_invalid_entries(dry_run)
        repair_results['invalid_removed'] = invalid_count
        
        # Fix normalization issues
        norm_count = self._fix_normalization_issues(dry_run)
        repair_results['normalization_fixed'] = norm_count
        
        # Merge duplicate concepts
        dup_count = self._merge_duplicate_concepts(dry_run)
        repair_results['duplicates_merged'] = dup_count
        
        total_fixes = sum([orphaned_count, invalid_count, norm_count, dup_count])
        
        logger.info(f"Cache repair complete {'(dry run)' if dry_run else ''}. "
                   f"Applied {total_fixes} fixes.")
        
        return repair_results
    
    def _get_all_cache_entries(self) -> Dict[str, Any]:
        """Get all entries from the cache."""
        try:
            # This will depend on the cache implementation
            # For now, we'll implement a basic version
            return {}  # TODO: Implement based on ConceptCache interface
        except Exception as e:
            logger.error(f"Error getting cache entries: {e}")
            return {}
    
    def _group_entries_by_concept(self, entries: Dict[str, Any]) -> Dict[str, List[str]]:
        """Group cache entries by the concept they represent."""
        concept_groups = defaultdict(list)
        
        for cache_key, data in entries.items():
            # Extract concept name from cache key
            if '_' in cache_key:
                parts = cache_key.split('_', 1)
                if len(parts) == 2:
                    connector_name, concept_name = parts
                    normalized_concept = normalize_concept_name(concept_name)
                    concept_groups[normalized_concept].append(cache_key)
        
        return dict(concept_groups)
    
    def _find_orphaned_variants(self, concept_groups: Dict[str, List[str]]) -> List[Dict[str, Any]]:
        """Find concept variants that should share cache entries but don't."""
        orphaned = []
        
        for normalized_concept, cache_keys in concept_groups.items():
            if len(cache_keys) > 1:
                # Check if these are actually variants of the same concept
                variants = get_concept_variants(normalized_concept)
                
                # Extract original concept names from cache keys
                original_names = []
                for cache_key in cache_keys:
                    if '_' in cache_key:
                        parts = cache_key.split('_', 1)
                        if len(parts) == 2:
                            original_names.append(parts[1])
                
                # Check if original names are variants
                normalized_originals = {normalize_concept_name(name) for name in original_names}
                if len(normalized_originals) == 1:  # Same concept, different representations
                    orphaned.append({
                        'concept': normalized_concept,
                        'cache_keys': cache_keys,
                        'original_names': original_names,
                        'issue': 'Multiple cache entries for same concept'
                    })
        
        return orphaned
    
    def _find_invalid_entries(self, entries: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find cache entries with invalid data."""
        invalid = []
        
        for cache_key, data in entries.items():
            try:
                # Check if data can be deserialized as ExternalConceptData
                if not isinstance(data, ExternalConceptData):
                    if isinstance(data, dict):
                        # Try to convert from dict
                        ExternalConceptData(**data)
                    else:
                        invalid.append({
                            'cache_key': cache_key,
                            'issue': f'Invalid data type: {type(data)}',
                            'data': str(data)[:100]  # First 100 chars for debugging
                        })
            except Exception as e:
                invalid.append({
                    'cache_key': cache_key,
                    'issue': f'Deserialization error: {e}',
                    'data': str(data)[:100]
                })
        
        return invalid
    
    def _find_normalization_issues(self, entries: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find cache entries that don't follow normalization rules."""
        normalization = []
        
        for cache_key, data in entries.items():
            if '_' in cache_key:
                parts = cache_key.split('_', 1)
                if len(parts) == 2:
                    connector_name, concept_name = parts
                    
                    # Check if the cache key should be normalized
                    expected_key = generate_cache_key(connector_name, concept_name)
                    if cache_key != expected_key:
                        normalization.append({
                            'current_key': cache_key,
                            'expected_key': expected_key,
                            'concept_name': concept_name,
                            'issue': 'Cache key not normalized'
                        })
        
        return normalization
    
    def _find_duplicate_concepts(self, concept_groups: Dict[str, List[str]]) -> List[Dict[str, Any]]:
        """Find concepts that appear to be duplicated across different cache keys."""
        duplicates = []
        
        # This is covered by orphaned variants for now
        # Could be extended to check for semantic duplicates
        
        return duplicates
    
    def _repair_orphaned_variants(self, dry_run: bool) -> int:
        """Repair orphaned concept variants."""
        if not self.validation_results.get('orphaned_variants'):
            return 0
        
        repaired = 0
        for orphan in self.validation_results['orphaned_variants']:
            cache_keys = orphan['cache_keys']
            
            if not dry_run:
                # Keep the entry with the highest quality data
                # For now, keep the first one and remove others
                # TODO: Implement data quality comparison
                primary_key = cache_keys[0]
                for key_to_remove in cache_keys[1:]:
                    try:
                        self.cache.delete(key_to_remove)
                        logger.debug(f"Removed orphaned cache entry: {key_to_remove}")
                    except Exception as e:
                        logger.error(f"Error removing orphaned entry {key_to_remove}: {e}")
            
            repaired += len(cache_keys) - 1
        
        return repaired
    
    def _remove_invalid_entries(self, dry_run: bool) -> int:
        """Remove invalid cache entries."""
        if not self.validation_results.get('invalid_entries'):
            return 0
        
        removed = 0
        for invalid in self.validation_results['invalid_entries']:
            cache_key = invalid['cache_key']
            
            if not dry_run:
                try:
                    self.cache.delete(cache_key)
                    logger.debug(f"Removed invalid cache entry: {cache_key}")
                    removed += 1
                except Exception as e:
                    logger.error(f"Error removing invalid entry {cache_key}: {e}")
            else:
                removed += 1
        
        return removed
    
    def _fix_normalization_issues(self, dry_run: bool) -> int:
        """Fix cache entries with normalization issues."""
        if not self.validation_results.get('normalization_issues'):
            return 0
        
        fixed = 0
        for issue in self.validation_results['normalization_issues']:
            current_key = issue['current_key']
            expected_key = issue['expected_key']
            
            if not dry_run:
                try:
                    # Get the data from old key
                    data = self.cache.get(current_key)
                    if data:
                        # Store under normalized key
                        self.cache.set(expected_key, data)
                        # Remove old key
                        self.cache.delete(current_key)
                        logger.debug(f"Normalized cache key: {current_key} -> {expected_key}")
                        fixed += 1
                except Exception as e:
                    logger.error(f"Error normalizing cache key {current_key}: {e}")
            else:
                fixed += 1
        
        return fixed
    
    def _merge_duplicate_concepts(self, dry_run: bool) -> int:
        """Merge duplicate concept entries."""
        # For now, this is handled by orphaned variants
        return 0


def validate_and_repair_cache(cache: ConceptCache, 
                             auto_repair: bool = False,
                             dry_run: bool = False) -> Dict[str, Any]:
    """
    Convenience function to validate and optionally repair cache.
    
    Args:
        cache: ConceptCache instance to validate
        auto_repair: If True, automatically repair found issues
        dry_run: If True, only simulate repairs
        
    Returns:
        Combined validation and repair results
    """
    validator = CacheValidator(cache)
    
    # Always run validation
    validation_results = validator.validate_cache_consistency()
    
    repair_results = {}
    if auto_repair and validation_results['issues_found'] > 0:
        repair_results = validator.repair_inconsistent_entries(dry_run)
    
    return {
        'validation': validation_results,
        'repair': repair_results,
        'timestamp': time.time()
    }


# Export main functions
__all__ = [
    'CacheValidator',
    'validate_and_repair_cache'
]