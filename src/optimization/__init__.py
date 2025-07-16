"""
Optimization module for performance enhancements.

This module provides batch processing, concept deduplication, and performance optimization
features for efficient document processing.
"""

from .batch_processor import BatchProcessor, ProgressTracker
from .concept_deduplicator import ConceptDeduplicator, DocumentTypeAwareDedupicator

__all__ = [
    'BatchProcessor',
    'ProgressTracker',
    'ConceptDeduplicator',
    'DocumentTypeAwareDedupicator',
]