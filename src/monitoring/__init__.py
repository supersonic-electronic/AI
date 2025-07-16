"""
Monitoring module for real-time document processing.

This module provides file system monitoring and incremental processing
capabilities for maintaining up-to-date knowledge graphs.
"""

from .file_watcher import FileWatcher, BatchFileWatcher
from .incremental_processor import IncrementalProcessor, DocumentChangeTracker

__all__ = [
    'FileWatcher',
    'BatchFileWatcher', 
    'IncrementalProcessor',
    'DocumentChangeTracker',
]