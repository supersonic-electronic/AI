"""
Batch processing optimization for efficient document processing.
"""

import asyncio
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Callable

from ..ingestion.extractors.document_detector import DocumentDetector
from ..knowledge.ontology import FinancialMathOntology


class BatchProcessor:
    """
    Batch processor for efficient multi-document processing.
    
    Optimizes processing by batching operations, parallel execution,
    and resource management for better throughput.
    """
    
    def __init__(self, ontology: FinancialMathOntology, config: Dict[str, Any] = None):
        """
        Initialize the batch processor.
        
        Args:
            ontology: FinancialMathOntology instance
            config: Configuration dictionary
        """
        self.ontology = ontology
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Processing configuration
        self.max_workers = self.config.get('max_workers', 4)
        self.batch_size = self.config.get('batch_size', 10)
        self.memory_limit_mb = self.config.get('memory_limit_mb', 1024)
        self.timeout_per_document = self.config.get('timeout_per_document', 30.0)
        
        # Components
        self.document_detector = DocumentDetector()
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
        
        # Statistics
        self.stats = {
            'total_documents': 0,
            'processed_documents': 0,
            'failed_documents': 0,
            'total_processing_time': 0.0,
            'average_processing_time': 0.0,
            'throughput_docs_per_second': 0.0,
            'memory_usage_mb': 0.0,
            'batches_processed': 0,
        }
    
    async def process_directory(
        self,
        directory: Path,
        recursive: bool = True,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Dict[str, Any]:
        """
        Process all documents in a directory using batch optimization.
        
        Args:
            directory: Directory to process
            recursive: Whether to process subdirectories
            progress_callback: Optional callback for progress updates (current, total)
            
        Returns:
            Processing results dictionary
        """
        if not directory.exists() or not directory.is_dir():
            raise ValueError(f"Invalid directory: {directory}")
        
        start_time = time.time()
        self.logger.info(f"Starting batch processing of directory: {directory}")
        
        # Collect all files to process
        files = self._collect_files(directory, recursive)
        self.stats['total_documents'] = len(files)
        
        if not files:
            self.logger.warning("No supported files found for processing")
            return self._create_results_summary(start_time, [])
        
        # Process files in batches
        results = []
        processed_count = 0
        
        for batch_start in range(0, len(files), self.batch_size):
            batch_end = min(batch_start + self.batch_size, len(files))
            batch_files = files[batch_start:batch_end]
            
            self.logger.info(f"Processing batch {batch_start // self.batch_size + 1}: "
                           f"files {batch_start + 1}-{batch_end} of {len(files)}")
            
            # Process batch
            batch_results = await self._process_batch(batch_files)
            results.extend(batch_results)
            
            # Update progress
            processed_count += len(batch_files)
            if progress_callback:
                progress_callback(processed_count, len(files))
            
            # Update statistics
            self.stats['batches_processed'] += 1
            self._update_memory_usage()
            
            # Garbage collection between batches
            import gc
            gc.collect()
        
        # Finalize results
        final_results = self._create_results_summary(start_time, results)
        self.logger.info(f"Batch processing completed: {final_results['summary']}")
        
        return final_results
    
    async def process_files(
        self,
        file_paths: List[Path],
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Dict[str, Any]:
        """
        Process a specific list of files using batch optimization.
        
        Args:
            file_paths: List of file paths to process
            progress_callback: Optional callback for progress updates
            
        Returns:
            Processing results dictionary
        """
        start_time = time.time()
        self.stats['total_documents'] = len(file_paths)
        
        # Filter supported files
        supported_files = []
        for file_path in file_paths:
            if self.document_detector.detect_document_type(file_path, self.config):
                supported_files.append(file_path)
        
        if not supported_files:
            self.logger.warning("No supported files found for processing")
            return self._create_results_summary(start_time, [])
        
        # Process in batches
        results = []
        processed_count = 0
        
        for batch_start in range(0, len(supported_files), self.batch_size):
            batch_end = min(batch_start + self.batch_size, len(supported_files))
            batch_files = supported_files[batch_start:batch_end]
            
            # Process batch
            batch_results = await self._process_batch(batch_files)
            results.extend(batch_results)
            
            # Update progress
            processed_count += len(batch_files)
            if progress_callback:
                progress_callback(processed_count, len(supported_files))
            
            self.stats['batches_processed'] += 1
        
        return self._create_results_summary(start_time, results)
    
    def _collect_files(self, directory: Path, recursive: bool) -> List[Path]:
        """
        Collect all supported files from a directory.
        
        Args:
            directory: Directory to scan
            recursive: Whether to scan subdirectories
            
        Returns:
            List of supported file paths
        """
        pattern = "**/*" if recursive else "*"
        supported_extensions = self.document_detector.get_supported_extensions()
        
        files = []
        for file_path in directory.glob(pattern):
            if (file_path.is_file() and 
                file_path.suffix.lower() in supported_extensions and
                self._should_process_file(file_path)):
                files.append(file_path)
        
        self.logger.info(f"Found {len(files)} supported files to process")
        return files
    
    def _should_process_file(self, file_path: Path) -> bool:
        """
        Check if a file should be processed based on filters.
        
        Args:
            file_path: Path to check
            
        Returns:
            True if file should be processed
        """
        # Size filter
        max_size_mb = self.config.get('max_file_size_mb', 100)
        if file_path.stat().st_size > max_size_mb * 1024 * 1024:
            self.logger.warning(f"Skipping large file: {file_path} "
                              f"({file_path.stat().st_size / 1024 / 1024:.1f} MB)")
            return False
        
        # Pattern filters
        ignore_patterns = self.config.get('ignore_patterns', [])
        for pattern in ignore_patterns:
            if file_path.match(pattern):
                self.logger.debug(f"Skipping file matching ignore pattern: {file_path}")
                return False
        
        return True
    
    async def _process_batch(self, file_paths: List[Path]) -> List[Dict[str, Any]]:
        """
        Process a batch of files in parallel.
        
        Args:
            file_paths: List of file paths to process
            
        Returns:
            List of processing results
        """
        # Submit all files to thread pool
        futures = []
        for file_path in file_paths:
            future = self.executor.submit(self._process_single_file, file_path)
            futures.append((file_path, future))
        
        # Collect results with timeout
        results = []
        for file_path, future in futures:
            try:
                result = await asyncio.wait_for(
                    asyncio.wrap_future(future),
                    timeout=self.timeout_per_document
                )
                results.append(result)
                
                if result['success']:
                    self.stats['processed_documents'] += 1
                else:
                    self.stats['failed_documents'] += 1
                    
            except asyncio.TimeoutError:
                self.logger.error(f"Processing timeout for {file_path}")
                results.append({
                    'file_path': str(file_path),
                    'success': False,
                    'error': 'Processing timeout',
                    'processing_time': self.timeout_per_document
                })
                self.stats['failed_documents'] += 1
                
            except Exception as e:
                self.logger.error(f"Processing error for {file_path}: {e}")
                results.append({
                    'file_path': str(file_path),
                    'success': False,
                    'error': str(e),
                    'processing_time': 0.0
                })
                self.stats['failed_documents'] += 1
        
        return results
    
    def _process_single_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Process a single file (runs in thread pool).
        
        Args:
            file_path: Path to process
            
        Returns:
            Processing result dictionary
        """
        start_time = time.time()
        
        try:
            # Detect document type
            extractor = self.document_detector.detect_document_type(file_path, self.config)
            
            if not extractor:
                return {
                    'file_path': str(file_path),
                    'success': False,
                    'error': 'No suitable extractor found',
                    'processing_time': time.time() - start_time
                }
            
            # Extract content and metadata
            text_content = extractor.extract_text(file_path, self.config)
            metadata = extractor.extract_metadata(file_path, self.config)
            
            # Process with ontology
            extracted_data = self.ontology.extract_concepts(text_content)
            
            # Add document metadata
            document_id = str(file_path)
            extracted_data['metadata'] = {
                **metadata,
                'file_path': str(file_path),
                'processing_time': time.time() - start_time,
                'extractor': extractor.extractor_name,
            }
            
            # Update ontology
            self.ontology.update_from_extraction(extracted_data, document_id)
            
            # Apply external enrichment if configured
            if self.config.get('use_external_ontologies', True):
                enriched_concepts = []
                for concept in extracted_data.get('concepts', []):
                    enriched_concept = self.ontology.external_ontology_manager.enrich_concept(concept)
                    enriched_concepts.append(enriched_concept)
                    if enriched_concept != concept:
                        self.ontology.update_concept(enriched_concept)
            
            processing_time = time.time() - start_time
            self.stats['total_processing_time'] += processing_time
            
            return {
                'file_path': str(file_path),
                'success': True,
                'extractor': extractor.extractor_name,
                'concepts_extracted': len(extracted_data.get('concepts', [])),
                'processing_time': processing_time,
                'file_size': file_path.stat().st_size,
                'metadata': extracted_data['metadata']
            }
            
        except Exception as e:
            processing_time = time.time() - start_time
            self.logger.error(f"Error processing {file_path}: {e}")
            
            return {
                'file_path': str(file_path),
                'success': False,
                'error': str(e),
                'processing_time': processing_time
            }
    
    def _update_memory_usage(self) -> None:
        """Update memory usage statistics."""
        try:
            import psutil
            process = psutil.Process()
            self.stats['memory_usage_mb'] = process.memory_info().rss / 1024 / 1024
        except ImportError:
            # psutil not available, estimate based on other factors
            pass
    
    def _create_results_summary(self, start_time: float, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create a summary of processing results.
        
        Args:
            start_time: Processing start time
            results: List of individual processing results
            
        Returns:
            Results summary dictionary
        """
        total_time = time.time() - start_time
        
        successful_results = [r for r in results if r['success']]
        failed_results = [r for r in results if not r['success']]
        
        # Calculate statistics
        if successful_results:
            avg_processing_time = sum(r['processing_time'] for r in successful_results) / len(successful_results)
            total_concepts = sum(r.get('concepts_extracted', 0) for r in successful_results)
            total_file_size = sum(r.get('file_size', 0) for r in successful_results)
        else:
            avg_processing_time = 0.0
            total_concepts = 0
            total_file_size = 0
        
        throughput = len(successful_results) / total_time if total_time > 0 else 0.0
        
        # Update global stats
        self.stats['average_processing_time'] = avg_processing_time
        self.stats['throughput_docs_per_second'] = throughput
        
        summary = {
            'total_files': len(results),
            'successful': len(successful_results),
            'failed': len(failed_results),
            'total_processing_time': total_time,
            'average_processing_time': avg_processing_time,
            'throughput_docs_per_second': throughput,
            'total_concepts_extracted': total_concepts,
            'total_file_size_mb': total_file_size / 1024 / 1024,
            'memory_usage_mb': self.stats['memory_usage_mb'],
        }
        
        return {
            'summary': summary,
            'successful_files': successful_results,
            'failed_files': failed_results,
            'stats': self.stats.copy()
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get current processing statistics.
        
        Returns:
            Statistics dictionary
        """
        return self.stats.copy()
    
    def reset_statistics(self) -> None:
        """Reset processing statistics."""
        self.stats = {
            'total_documents': 0,
            'processed_documents': 0,
            'failed_documents': 0,
            'total_processing_time': 0.0,
            'average_processing_time': 0.0,
            'throughput_docs_per_second': 0.0,
            'memory_usage_mb': 0.0,
            'batches_processed': 0,
        }
    
    def shutdown(self) -> None:
        """Shutdown the batch processor and cleanup resources."""
        self.executor.shutdown(wait=True)
        self.logger.info("Batch processor shutdown complete")


class ProgressTracker:
    """
    Progress tracker for long-running batch operations.
    
    Provides progress reporting, ETA calculation, and cancellation support.
    """
    
    def __init__(self, total_items: int, update_interval: float = 1.0):
        """
        Initialize the progress tracker.
        
        Args:
            total_items: Total number of items to process
            update_interval: Minimum interval between progress updates (seconds)
        """
        self.total_items = total_items
        self.update_interval = update_interval
        self.logger = logging.getLogger(__name__)
        
        # Progress tracking
        self.processed_items = 0
        self.start_time = time.time()
        self.last_update_time = 0.0
        self.cancelled = False
        
        # Callbacks
        self.progress_callbacks = []
    
    def add_progress_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Add a progress callback function.
        
        Args:
            callback: Function to call with progress information
        """
        self.progress_callbacks.append(callback)
    
    def update(self, increment: int = 1) -> None:
        """
        Update progress by specified increment.
        
        Args:
            increment: Number of items processed
        """
        self.processed_items += increment
        current_time = time.time()
        
        # Check if we should send an update
        if current_time - self.last_update_time >= self.update_interval:
            self._send_progress_update()
            self.last_update_time = current_time
    
    def set_progress(self, processed: int) -> None:
        """
        Set absolute progress value.
        
        Args:
            processed: Number of items processed
        """
        self.processed_items = min(processed, self.total_items)
        self._send_progress_update()
    
    def cancel(self) -> None:
        """Cancel the operation."""
        self.cancelled = True
        self._send_progress_update()
    
    def is_cancelled(self) -> bool:
        """Check if operation was cancelled."""
        return self.cancelled
    
    def is_complete(self) -> bool:
        """Check if operation is complete."""
        return self.processed_items >= self.total_items
    
    def _send_progress_update(self) -> None:
        """Send progress update to all callbacks."""
        progress_info = self.get_progress_info()
        
        for callback in self.progress_callbacks:
            try:
                callback(progress_info)
            except Exception as e:
                self.logger.error(f"Error in progress callback: {e}")
    
    def get_progress_info(self) -> Dict[str, Any]:
        """
        Get current progress information.
        
        Returns:
            Progress information dictionary
        """
        elapsed_time = time.time() - self.start_time
        progress_percent = (self.processed_items / self.total_items * 100) if self.total_items > 0 else 0
        
        # Calculate ETA
        if self.processed_items > 0 and not self.is_complete():
            rate = self.processed_items / elapsed_time
            remaining_items = self.total_items - self.processed_items
            eta_seconds = remaining_items / rate if rate > 0 else 0
        else:
            eta_seconds = 0
        
        return {
            'processed': self.processed_items,
            'total': self.total_items,
            'progress_percent': progress_percent,
            'elapsed_time': elapsed_time,
            'eta_seconds': eta_seconds,
            'rate_per_second': self.processed_items / elapsed_time if elapsed_time > 0 else 0,
            'is_cancelled': self.cancelled,
            'is_complete': self.is_complete(),
        }