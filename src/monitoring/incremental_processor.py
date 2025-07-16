"""
Incremental graph update processor for real-time document changes.
"""

import asyncio
import hashlib
import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from ..ingestion.extractors.document_detector import DocumentDetector
from ..knowledge.ontology import FinancialMathOntology


class DocumentChangeTracker:
    """
    Tracks document changes for incremental processing.
    
    Maintains document hashes and modification times to detect
    what has actually changed and needs reprocessing.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the document change tracker.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Document tracking
        self.document_hashes = {}  # file_path -> hash
        self.document_metadata = {}  # file_path -> metadata
        self.processing_queue = asyncio.Queue()
        
        # Configuration
        self.hash_algorithm = self.config.get('hash_algorithm', 'sha256')
        self.track_metadata = self.config.get('track_metadata', True)
        self.cache_file = self.config.get('cache_file', '.document_cache.json')
        
        # Load existing cache
        self._load_cache()
    
    def _load_cache(self) -> None:
        """Load document cache from file."""
        try:
            if Path(self.cache_file).exists():
                with open(self.cache_file, 'r') as f:
                    cache_data = json.load(f)
                    self.document_hashes = cache_data.get('hashes', {})
                    self.document_metadata = cache_data.get('metadata', {})
                self.logger.info(f"Loaded cache for {len(self.document_hashes)} documents")
        except Exception as e:
            self.logger.warning(f"Could not load document cache: {e}")
    
    def _save_cache(self) -> None:
        """Save document cache to file."""
        try:
            cache_data = {
                'hashes': self.document_hashes,
                'metadata': self.document_metadata,
                'last_updated': time.time()
            }
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
            self.logger.debug("Saved document cache")
        except Exception as e:
            self.logger.error(f"Could not save document cache: {e}")
    
    def calculate_file_hash(self, file_path: Path) -> str:
        """
        Calculate hash of a file's content.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Hash string
        """
        hash_obj = hashlib.new(self.hash_algorithm)
        
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    hash_obj.update(chunk)
            return hash_obj.hexdigest()
        except Exception as e:
            self.logger.error(f"Error calculating hash for {file_path}: {e}")
            return ""
    
    def has_changed(self, file_path: Path) -> Tuple[bool, str]:
        """
        Check if a document has changed since last processing.
        
        Args:
            file_path: Path to the document
            
        Returns:
            Tuple of (has_changed, change_type)
        """
        file_key = str(file_path)
        
        if not file_path.exists():
            if file_key in self.document_hashes:
                # File was deleted
                return True, 'deleted'
            else:
                # File never existed
                return False, 'none'
        
        current_hash = self.calculate_file_hash(file_path)
        
        if file_key not in self.document_hashes:
            # New file
            return True, 'created'
        
        if self.document_hashes[file_key] != current_hash:
            # File modified
            return True, 'modified'
        
        # No change
        return False, 'none'
    
    def update_document_info(self, file_path: Path, metadata: Dict[str, Any] = None) -> None:
        """
        Update document information after processing.
        
        Args:
            file_path: Path to the document
            metadata: Optional metadata to store
        """
        file_key = str(file_path)
        
        if file_path.exists():
            self.document_hashes[file_key] = self.calculate_file_hash(file_path)
            
            if self.track_metadata and metadata:
                self.document_metadata[file_key] = {
                    'last_processed': time.time(),
                    'size': file_path.stat().st_size,
                    'mtime': file_path.stat().st_mtime,
                    **metadata
                }
        else:
            # File was deleted, remove from tracking
            self.document_hashes.pop(file_key, None)
            self.document_metadata.pop(file_key, None)
        
        # Save cache periodically
        if len(self.document_hashes) % 10 == 0:
            self._save_cache()
    
    def get_document_info(self, file_path: Path) -> Dict[str, Any]:
        """
        Get stored information about a document.
        
        Args:
            file_path: Path to the document
            
        Returns:
            Document information dictionary
        """
        file_key = str(file_path)
        return self.document_metadata.get(file_key, {})
    
    def cleanup_deleted_files(self, existing_files: Set[Path]) -> List[str]:
        """
        Clean up tracking for files that no longer exist.
        
        Args:
            existing_files: Set of files that currently exist
            
        Returns:
            List of deleted file paths
        """
        existing_keys = {str(f) for f in existing_files}
        tracked_keys = set(self.document_hashes.keys())
        deleted_keys = tracked_keys - existing_keys
        
        for deleted_key in deleted_keys:
            self.document_hashes.pop(deleted_key, None)
            self.document_metadata.pop(deleted_key, None)
        
        if deleted_keys:
            self._save_cache()
        
        return list(deleted_keys)


class IncrementalProcessor:
    """
    Incremental processor for real-time graph updates.
    
    Processes document changes incrementally to maintain an up-to-date
    knowledge graph without full reprocessing.
    """
    
    def __init__(self, ontology: FinancialMathOntology, config: Dict[str, Any] = None):
        """
        Initialize the incremental processor.
        
        Args:
            ontology: FinancialMathOntology instance
            config: Configuration dictionary
        """
        self.ontology = ontology
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Components
        self.change_tracker = DocumentChangeTracker(config)
        self.document_detector = DocumentDetector()
        
        # Processing configuration
        self.max_concurrent = self.config.get('max_concurrent_processing', 3)
        self.processing_semaphore = asyncio.Semaphore(self.max_concurrent)
        self.processing_queue = asyncio.Queue()
        
        # Statistics
        self.stats = {
            'documents_processed': 0,
            'documents_created': 0,
            'documents_modified': 0,
            'documents_deleted': 0,
            'processing_errors': 0,
            'last_processing_time': None,
        }
        
        # Background processing
        self.processing_task = None
        self.is_running = False
    
    async def start(self) -> None:
        """Start the incremental processor."""
        if self.is_running:
            return
        
        self.is_running = True
        self.processing_task = asyncio.create_task(self._processing_loop())
        self.logger.info("Incremental processor started")
    
    async def stop(self) -> None:
        """Stop the incremental processor."""
        if not self.is_running:
            return
        
        self.is_running = False
        
        if self.processing_task:
            self.processing_task.cancel()
            try:
                await self.processing_task
            except asyncio.CancelledError:
                pass
        
        # Save final state
        self.change_tracker._save_cache()
        self.logger.info("Incremental processor stopped")
    
    async def process_file_event(self, event_type: str, file_path: Path, event_name: str) -> None:
        """
        Process a file system event.
        
        Args:
            event_type: Type of event (created, modified, deleted, moved)
            file_path: Path to the affected file
            event_name: Name of the event
        """
        try:
            # Add to processing queue
            await self.processing_queue.put({
                'event_type': event_type,
                'file_path': file_path,
                'event_name': event_name,
                'timestamp': time.time()
            })
            
            self.logger.debug(f"Queued {event_type} event for {file_path}")
            
        except Exception as e:
            self.logger.error(f"Error queuing file event for {file_path}: {e}")
    
    async def process_batch_events(self, events: List[Dict[str, Any]]) -> None:
        """
        Process a batch of file events.
        
        Args:
            events: List of file event dictionaries
        """
        for event in events:
            await self.process_file_event(
                event['event_type'],
                event['file_path'],
                event['event_name']
            )
    
    async def _processing_loop(self) -> None:
        """Main processing loop for handling queued events."""
        while self.is_running:
            try:
                # Get event from queue with timeout
                try:
                    event = await asyncio.wait_for(
                        self.processing_queue.get(),
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                # Process the event
                await self._process_single_event(event)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in processing loop: {e}")
                await asyncio.sleep(1.0)  # Prevent tight loop on errors
    
    async def _process_single_event(self, event: Dict[str, Any]) -> None:
        """
        Process a single file event.
        
        Args:
            event: Event dictionary
        """
        async with self.processing_semaphore:
            event_type = event['event_type']
            file_path = event['file_path']
            
            try:
                self.logger.info(f"Processing {event_type} event for {file_path}")
                
                if event_type == 'deleted':
                    await self._handle_file_deletion(file_path)
                elif event_type in ['created', 'modified', 'moved']:
                    await self._handle_file_change(file_path, event_type)
                
                self.stats['documents_processed'] += 1
                self.stats['last_processing_time'] = time.time()
                
            except Exception as e:
                self.logger.error(f"Error processing {event_type} event for {file_path}: {e}")
                self.stats['processing_errors'] += 1
    
    async def _handle_file_deletion(self, file_path: Path) -> None:
        """
        Handle file deletion event.
        
        Args:
            file_path: Path to the deleted file
        """
        # Remove from ontology if it was previously processed
        document_info = self.change_tracker.get_document_info(file_path)
        
        if document_info:
            # Remove concepts associated with this document
            await self._remove_document_concepts(file_path, document_info)
        
        # Update tracking
        self.change_tracker.update_document_info(file_path)
        self.stats['documents_deleted'] += 1
        
        self.logger.info(f"Removed document: {file_path}")
    
    async def _handle_file_change(self, file_path: Path, event_type: str) -> None:
        """
        Handle file creation or modification event.
        
        Args:
            file_path: Path to the changed file
            event_type: Type of change event
        """
        # Check if file actually changed
        has_changed, change_type = self.change_tracker.has_changed(file_path)
        
        if not has_changed and change_type == 'none':
            self.logger.debug(f"File {file_path} has not actually changed, skipping")
            return
        
        # Detect document type
        extractor = self.document_detector.detect_document_type(file_path, self.config)
        
        if not extractor:
            self.logger.debug(f"No suitable extractor for {file_path}, skipping")
            return
        
        # Extract document content and metadata
        try:
            text_content = extractor.extract_text(file_path, self.config)
            metadata = extractor.extract_metadata(file_path, self.config)
            
            # Process with ontology
            await self._update_document_concepts(file_path, text_content, metadata, change_type)
            
            # Update tracking
            self.change_tracker.update_document_info(file_path, metadata)
            
            if change_type == 'created':
                self.stats['documents_created'] += 1
            else:
                self.stats['documents_modified'] += 1
            
            self.logger.info(f"Processed {change_type} document: {file_path}")
            
        except Exception as e:
            self.logger.error(f"Error processing document {file_path}: {e}")
            raise
    
    async def _update_document_concepts(
        self,
        file_path: Path,
        content: str,
        metadata: Dict[str, Any],
        change_type: str
    ) -> None:
        """
        Update concepts in the ontology for a document.
        
        Args:
            file_path: Path to the document
            content: Extracted text content
            metadata: Document metadata
            change_type: Type of change (created, modified)
        """
        # If this is a modification, first remove old concepts
        if change_type == 'modified':
            old_metadata = self.change_tracker.get_document_info(file_path)
            if old_metadata:
                await self._remove_document_concepts(file_path, old_metadata)
        
        # Extract concepts from content
        extracted_data = self.ontology.extract_concepts(content)
        
        # Add document metadata
        document_id = str(file_path)
        extracted_data['metadata'] = {
            **metadata,
            'file_path': str(file_path),
            'processing_time': time.time(),
            'change_type': change_type,
        }
        
        # Update ontology
        self.ontology.update_from_extraction(extracted_data, document_id)
        
        # Apply external ontology enrichment if configured
        if self.config.get('use_external_ontologies', True):
            for concept in extracted_data.get('concepts', []):
                enriched_concept = self.ontology.external_ontology_manager.enrich_concept(concept)
                if enriched_concept != concept:
                    # Update with enriched data
                    self.ontology.update_concept(enriched_concept)
    
    async def _remove_document_concepts(self, file_path: Path, metadata: Dict[str, Any]) -> None:
        """
        Remove concepts associated with a document from the ontology.
        
        Args:
            file_path: Path to the document
            metadata: Document metadata
        """
        document_id = str(file_path)
        
        # Find and remove concepts associated with this document
        # This would depend on how the ontology tracks document associations
        try:
            self.ontology.remove_document_concepts(document_id)
        except AttributeError:
            # Method doesn't exist, log a warning
            self.logger.warning(f"Cannot remove document concepts for {file_path}: method not implemented")
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """
        Get processing statistics.
        
        Returns:
            Dictionary with processing statistics
        """
        return {
            **self.stats,
            'queue_size': self.processing_queue.qsize(),
            'is_running': self.is_running,
            'max_concurrent': self.max_concurrent,
            'tracked_documents': len(self.change_tracker.document_hashes),
        }
    
    def force_reprocess_all(self, directory: Path) -> None:
        """
        Force reprocessing of all documents in a directory.
        
        Args:
            directory: Directory to reprocess
        """
        if not directory.exists() or not directory.is_dir():
            raise ValueError(f"Invalid directory: {directory}")
        
        # Clear tracking for files in this directory
        files_to_clear = []
        for file_key in self.change_tracker.document_hashes:
            if Path(file_key).parent == directory:
                files_to_clear.append(file_key)
        
        for file_key in files_to_clear:
            self.change_tracker.document_hashes.pop(file_key, None)
            self.change_tracker.document_metadata.pop(file_key, None)
        
        self.change_tracker._save_cache()
        self.logger.info(f"Cleared tracking for {len(files_to_clear)} files in {directory}")
    
    async def sync_directory(self, directory: Path, recursive: bool = True) -> Dict[str, Any]:
        """
        Synchronize a directory with the knowledge graph.
        
        Args:
            directory: Directory to synchronize
            recursive: Whether to process subdirectories
            
        Returns:
            Synchronization results
        """
        if not directory.exists() or not directory.is_dir():
            raise ValueError(f"Invalid directory: {directory}")
        
        results = {
            'processed': 0,
            'skipped': 0,
            'errors': 0,
            'files': []
        }
        
        # Find all supported files
        pattern = "**/*" if recursive else "*"
        supported_extensions = self.document_detector.get_supported_extensions()
        
        for file_path in directory.glob(pattern):
            if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                try:
                    # Check if processing is needed
                    has_changed, change_type = self.change_tracker.has_changed(file_path)
                    
                    if has_changed or change_type != 'none':
                        await self._handle_file_change(file_path, change_type or 'modified')
                        results['processed'] += 1
                        results['files'].append({
                            'path': str(file_path),
                            'action': 'processed',
                            'change_type': change_type
                        })
                    else:
                        results['skipped'] += 1
                        results['files'].append({
                            'path': str(file_path),
                            'action': 'skipped',
                            'reason': 'no_changes'
                        })
                
                except Exception as e:
                    results['errors'] += 1
                    results['files'].append({
                        'path': str(file_path),
                        'action': 'error',
                        'error': str(e)
                    })
                    self.logger.error(f"Error processing {file_path}: {e}")
        
        # Clean up tracking for deleted files
        existing_files = {
            file_path for file_path in directory.glob(pattern)
            if file_path.is_file() and file_path.suffix.lower() in supported_extensions
        }
        
        deleted_files = self.change_tracker.cleanup_deleted_files(existing_files)
        for deleted_file in deleted_files:
            results['files'].append({
                'path': deleted_file,
                'action': 'deleted',
                'change_type': 'deleted'
            })
        
        self.logger.info(f"Directory sync completed: {results}")
        return results