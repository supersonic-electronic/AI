"""
File system watcher for real-time document processing.
"""

import asyncio
import logging
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer


class DocumentFileHandler(FileSystemEventHandler):
    """
    File system event handler for document processing.
    
    Handles file creation, modification, and deletion events
    for supported document types.
    """
    
    def __init__(
        self,
        callback: Callable[[str, Path, str], None],
        supported_extensions: Set[str],
        config: Dict[str, Any] = None
    ):
        """
        Initialize the file handler.
        
        Args:
            callback: Function to call when events occur (event_type, file_path, event_name)
            supported_extensions: Set of file extensions to monitor
            config: Configuration dictionary
        """
        self.callback = callback
        self.supported_extensions = supported_extensions
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Rate limiting to prevent excessive processing
        self.last_processed = {}
        self.min_interval = self.config.get('min_processing_interval', 1.0)  # seconds
        
        # File size tracking for completion detection
        self.file_sizes = {}
        self.size_check_delay = self.config.get('size_check_delay', 2.0)  # seconds
    
    def on_created(self, event: FileSystemEvent) -> None:
        """Handle file creation events."""
        if not event.is_directory:
            self._handle_file_event('created', Path(event.src_path))
    
    def on_modified(self, event: FileSystemEvent) -> None:
        """Handle file modification events."""
        if not event.is_directory:
            self._handle_file_event('modified', Path(event.src_path))
    
    def on_deleted(self, event: FileSystemEvent) -> None:
        """Handle file deletion events."""
        if not event.is_directory:
            self._handle_file_event('deleted', Path(event.src_path))
    
    def on_moved(self, event: FileSystemEvent) -> None:
        """Handle file move/rename events."""
        if not event.is_directory:
            # Handle as deletion of old path and creation of new path
            self._handle_file_event('deleted', Path(event.src_path))
            self._handle_file_event('moved', Path(event.dest_path))
    
    def _handle_file_event(self, event_type: str, file_path: Path) -> None:
        """
        Handle a file system event.
        
        Args:
            event_type: Type of event (created, modified, deleted, moved)
            file_path: Path to the affected file
        """
        try:
            # Check if file extension is supported
            if not self._is_supported_file(file_path):
                return
            
            # Rate limiting check
            if not self._should_process_file(file_path, event_type):
                return
            
            # For creation and modification, check if file is complete
            if event_type in ['created', 'modified'] and file_path.exists():
                if not self._is_file_complete(file_path):
                    # Schedule a delayed check
                    asyncio.create_task(self._delayed_file_check(file_path, event_type))
                    return
            
            # Process the event
            self._process_file_event(event_type, file_path)
            
        except Exception as e:
            self.logger.error(f"Error handling file event for {file_path}: {e}")
    
    def _is_supported_file(self, file_path: Path) -> bool:
        """
        Check if the file is a supported document type.
        
        Args:
            file_path: Path to check
            
        Returns:
            True if file is supported, False otherwise
        """
        extension = file_path.suffix.lower()
        return extension in self.supported_extensions
    
    def _should_process_file(self, file_path: Path, event_type: str) -> bool:
        """
        Check if the file should be processed based on rate limiting.
        
        Args:
            file_path: Path to check
            event_type: Type of event
            
        Returns:
            True if file should be processed, False otherwise
        """
        current_time = time.time()
        file_key = str(file_path)
        
        # Check if enough time has passed since last processing
        if file_key in self.last_processed:
            time_diff = current_time - self.last_processed[file_key]
            if time_diff < self.min_interval:
                self.logger.debug(f"Rate limiting: skipping {file_path} (too soon)")
                return False
        
        # Update last processed time
        self.last_processed[file_key] = current_time
        return True
    
    def _is_file_complete(self, file_path: Path) -> bool:
        """
        Check if a file has finished being written.
        
        Args:
            file_path: Path to check
            
        Returns:
            True if file is complete, False otherwise
        """
        try:
            current_size = file_path.stat().st_size
            file_key = str(file_path)
            
            # Check if size has changed since last check
            if file_key in self.file_sizes:
                if self.file_sizes[file_key] == current_size:
                    # Size hasn't changed, likely complete
                    return True
            
            # Update stored size
            self.file_sizes[file_key] = current_size
            return False
            
        except (OSError, FileNotFoundError):
            # File doesn't exist or can't be accessed
            return False
    
    async def _delayed_file_check(self, file_path: Path, event_type: str) -> None:
        """
        Perform a delayed check to see if file is complete.
        
        Args:
            file_path: Path to check
            event_type: Type of event
        """
        await asyncio.sleep(self.size_check_delay)
        
        try:
            if file_path.exists() and self._is_file_complete(file_path):
                self._process_file_event(event_type, file_path)
        except Exception as e:
            self.logger.error(f"Error in delayed file check for {file_path}: {e}")
    
    def _process_file_event(self, event_type: str, file_path: Path) -> None:
        """
        Process a file event by calling the callback.
        
        Args:
            event_type: Type of event
            file_path: Path to the file
        """
        try:
            self.callback(event_type, file_path, f"file_{event_type}")
            self.logger.info(f"Processed {event_type} event for {file_path}")
        except Exception as e:
            self.logger.error(f"Error processing {event_type} event for {file_path}: {e}")


class FileWatcher:
    """
    File system watcher for monitoring document changes.
    
    Monitors specified directories for document file changes and
    triggers processing callbacks for real-time updates.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the file watcher.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        self.observer = Observer()
        self.watched_paths = {}
        self.callbacks = []
        self.supported_extensions = set()
        self.is_running = False
        
        # Default configuration
        self.recursive = self.config.get('recursive', True)
        self.ignore_patterns = self.config.get('ignore_patterns', [
            '.*',  # Hidden files
            '*~',  # Backup files
            '*.tmp',  # Temporary files
            '*.swp',  # Vim swap files
            '__pycache__',  # Python cache
            '.git',  # Git directory
        ])
    
    def add_callback(self, callback: Callable[[str, Path, str], None]) -> None:
        """
        Add a callback function for file events.
        
        Args:
            callback: Function to call when events occur
        """
        self.callbacks.append(callback)
    
    def set_supported_extensions(self, extensions: List[str]) -> None:
        """
        Set the file extensions to monitor.
        
        Args:
            extensions: List of file extensions (with dots)
        """
        self.supported_extensions = set(ext.lower() for ext in extensions)
        self.logger.info(f"Monitoring extensions: {self.supported_extensions}")
    
    def add_watch_path(self, path: Path, recursive: bool = None) -> None:
        """
        Add a directory path to watch.
        
        Args:
            path: Directory path to watch
            recursive: Whether to watch subdirectories (uses default if None)
        """
        if not path.exists():
            raise FileNotFoundError(f"Watch path does not exist: {path}")
        
        if not path.is_dir():
            raise ValueError(f"Watch path is not a directory: {path}")
        
        watch_recursive = recursive if recursive is not None else self.recursive
        
        # Create event handler
        handler = DocumentFileHandler(
            callback=self._handle_file_event,
            supported_extensions=self.supported_extensions,
            config=self.config
        )
        
        # Add to observer
        watch = self.observer.schedule(handler, str(path), recursive=watch_recursive)
        self.watched_paths[str(path)] = {
            'path': path,
            'handler': handler,
            'watch': watch,
            'recursive': watch_recursive
        }
        
        self.logger.info(f"Added watch path: {path} (recursive={watch_recursive})")
    
    def remove_watch_path(self, path: Path) -> None:
        """
        Remove a directory path from watching.
        
        Args:
            path: Directory path to stop watching
        """
        path_str = str(path)
        if path_str in self.watched_paths:
            watch_info = self.watched_paths[path_str]
            self.observer.unschedule(watch_info['watch'])
            del self.watched_paths[path_str]
            self.logger.info(f"Removed watch path: {path}")
        else:
            self.logger.warning(f"Watch path not found: {path}")
    
    def start(self) -> None:
        """Start the file watcher."""
        if self.is_running:
            self.logger.warning("File watcher is already running")
            return
        
        if not self.watched_paths:
            self.logger.warning("No watch paths configured")
            return
        
        if not self.supported_extensions:
            self.logger.warning("No supported extensions configured")
            return
        
        self.observer.start()
        self.is_running = True
        self.logger.info("File watcher started")
    
    def stop(self) -> None:
        """Stop the file watcher."""
        if not self.is_running:
            return
        
        self.observer.stop()
        self.observer.join()
        self.is_running = False
        self.logger.info("File watcher stopped")
    
    def _handle_file_event(self, event_type: str, file_path: Path, event_name: str) -> None:
        """
        Handle file events by calling all registered callbacks.
        
        Args:
            event_type: Type of event
            file_path: Path to the file
            event_name: Name of the event
        """
        # Filter out ignored patterns
        if self._is_ignored_file(file_path):
            return
        
        # Call all registered callbacks
        for callback in self.callbacks:
            try:
                callback(event_type, file_path, event_name)
            except Exception as e:
                self.logger.error(f"Error in callback for {file_path}: {e}")
    
    def _is_ignored_file(self, file_path: Path) -> bool:
        """
        Check if a file should be ignored based on ignore patterns.
        
        Args:
            file_path: Path to check
            
        Returns:
            True if file should be ignored, False otherwise
        """
        import fnmatch
        
        file_name = file_path.name
        file_path_str = str(file_path)
        
        for pattern in self.ignore_patterns:
            if fnmatch.fnmatch(file_name, pattern) or fnmatch.fnmatch(file_path_str, pattern):
                return True
        
        return False
    
    def get_watch_status(self) -> Dict[str, Any]:
        """
        Get the current status of the file watcher.
        
        Returns:
            Dictionary with status information
        """
        return {
            'is_running': self.is_running,
            'watched_paths': [
                {
                    'path': str(info['path']),
                    'recursive': info['recursive']
                }
                for info in self.watched_paths.values()
            ],
            'supported_extensions': list(self.supported_extensions),
            'callback_count': len(self.callbacks),
            'ignore_patterns': self.ignore_patterns,
        }
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()


class BatchFileWatcher:
    """
    Batched file watcher that groups file events for batch processing.
    
    Collects file events over a time window and processes them in batches
    to improve efficiency for high-volume scenarios.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the batch file watcher.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.file_watcher = FileWatcher(config)
        self.logger = logging.getLogger(__name__)
        
        # Batch configuration
        self.batch_size = self.config.get('batch_size', 10)
        self.batch_timeout = self.config.get('batch_timeout', 5.0)  # seconds
        
        # Event batching
        self.pending_events = []
        self.batch_timer = None
        self.batch_callbacks = []
    
    def add_batch_callback(self, callback: Callable[[List[Dict[str, Any]]], None]) -> None:
        """
        Add a callback function for batched file events.
        
        Args:
            callback: Function to call with batch of events
        """
        self.batch_callbacks.append(callback)
    
    def set_supported_extensions(self, extensions: List[str]) -> None:
        """Set the file extensions to monitor."""
        self.file_watcher.set_supported_extensions(extensions)
    
    def add_watch_path(self, path: Path, recursive: bool = None) -> None:
        """Add a directory path to watch."""
        self.file_watcher.add_watch_path(path, recursive)
    
    def remove_watch_path(self, path: Path) -> None:
        """Remove a directory path from watching."""
        self.file_watcher.remove_watch_path(path)
    
    def start(self) -> None:
        """Start the batch file watcher."""
        # Set up file watcher callback
        self.file_watcher.add_callback(self._handle_file_event)
        self.file_watcher.start()
        self.logger.info("Batch file watcher started")
    
    def stop(self) -> None:
        """Stop the batch file watcher."""
        # Process any remaining events
        if self.pending_events:
            self._process_batch()
        
        # Cancel timer
        if self.batch_timer:
            self.batch_timer.cancel()
        
        self.file_watcher.stop()
        self.logger.info("Batch file watcher stopped")
    
    def _handle_file_event(self, event_type: str, file_path: Path, event_name: str) -> None:
        """
        Handle individual file events by adding to batch.
        
        Args:
            event_type: Type of event
            file_path: Path to the file
            event_name: Name of the event
        """
        event = {
            'event_type': event_type,
            'file_path': file_path,
            'event_name': event_name,
            'timestamp': time.time(),
        }
        
        self.pending_events.append(event)
        
        # Check if batch is full
        if len(self.pending_events) >= self.batch_size:
            self._process_batch()
        else:
            # Set timer for batch timeout
            self._reset_batch_timer()
    
    def _reset_batch_timer(self) -> None:
        """Reset the batch processing timer."""
        if self.batch_timer:
            self.batch_timer.cancel()
        
        self.batch_timer = asyncio.create_task(self._batch_timeout())
    
    async def _batch_timeout(self) -> None:
        """Handle batch timeout."""
        await asyncio.sleep(self.batch_timeout)
        if self.pending_events:
            self._process_batch()
    
    def _process_batch(self) -> None:
        """Process the current batch of events."""
        if not self.pending_events:
            return
        
        batch = self.pending_events.copy()
        self.pending_events.clear()
        
        # Cancel timer
        if self.batch_timer:
            self.batch_timer.cancel()
            self.batch_timer = None
        
        # Call batch callbacks
        for callback in self.batch_callbacks:
            try:
                callback(batch)
            except Exception as e:
                self.logger.error(f"Error in batch callback: {e}")
        
        self.logger.info(f"Processed batch of {len(batch)} file events")
    
    def get_watch_status(self) -> Dict[str, Any]:
        """Get the current status of the batch file watcher."""
        status = self.file_watcher.get_watch_status()
        status.update({
            'batch_size': self.batch_size,
            'batch_timeout': self.batch_timeout,
            'pending_events': len(self.pending_events),
            'batch_callback_count': len(self.batch_callbacks),
        })
        return status
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()