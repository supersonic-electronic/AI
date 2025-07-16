"""
Unit tests for monitoring and real-time processing components.
"""

import asyncio
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import tempfile
import time

from src.monitoring.file_watcher import FileWatcher, BatchFileWatcher, DocumentFileHandler
from src.monitoring.incremental_processor import IncrementalProcessor, DocumentChangeTracker


class TestDocumentFileHandler:
    """Test cases for DocumentFileHandler."""
    
    def test_initialization(self):
        """Test DocumentFileHandler initialization."""
        callback = Mock()
        supported_extensions = {".pdf", ".html"}
        config = {"min_processing_interval": 1.0}
        
        handler = DocumentFileHandler(callback, supported_extensions, config)
        
        assert handler.callback == callback
        assert handler.supported_extensions == supported_extensions
        assert handler.config == config
        assert handler.min_interval == 1.0
    
    def test_is_supported_file(self):
        """Test file support checking."""
        callback = Mock()
        supported_extensions = {".pdf", ".html"}
        handler = DocumentFileHandler(callback, supported_extensions, {})
        
        assert handler._is_supported_file(Path("test.pdf"))
        assert handler._is_supported_file(Path("test.html"))
        assert not handler._is_supported_file(Path("test.txt"))
        assert not handler._is_supported_file(Path("test.docx"))
    
    def test_should_process_file_rate_limiting(self):
        """Test rate limiting functionality."""
        callback = Mock()
        supported_extensions = {".pdf"}
        config = {"min_processing_interval": 1.0}
        handler = DocumentFileHandler(callback, supported_extensions, config)
        
        file_path = Path("test.pdf")
        
        # First call should return True
        assert handler._should_process_file(file_path, "created")
        
        # Immediate second call should return False due to rate limiting
        assert not handler._should_process_file(file_path, "modified")
        
        # After updating timestamp, should return True again
        handler.last_processed[str(file_path)] = time.time() - 2.0
        assert handler._should_process_file(file_path, "modified")
    
    @patch("pathlib.Path.stat")
    def test_is_file_complete(self, mock_stat):
        """Test file completion detection."""
        callback = Mock()
        supported_extensions = {".pdf"}
        handler = DocumentFileHandler(callback, supported_extensions, {})
        
        file_path = Path("test.pdf")
        
        # Mock file size
        mock_stat.return_value = Mock(st_size=1000)
        
        # First call should return False (no previous size)
        assert not handler._is_file_complete(file_path)
        
        # Second call with same size should return True
        assert handler._is_file_complete(file_path)
        
        # Call with different size should return False
        mock_stat.return_value = Mock(st_size=1500)
        assert not handler._is_file_complete(file_path)


class TestFileWatcher:
    """Test cases for FileWatcher."""
    
    def test_initialization(self):
        """Test FileWatcher initialization."""
        config = {"recursive": True, "ignore_patterns": ["*.tmp"]}
        watcher = FileWatcher(config)
        
        assert watcher.config == config
        assert watcher.recursive == True
        assert "*.tmp" in watcher.ignore_patterns
        assert not watcher.is_running
        assert len(watcher.callbacks) == 0
    
    def test_add_callback(self):
        """Test adding callbacks."""
        watcher = FileWatcher()
        callback = Mock()
        
        watcher.add_callback(callback)
        
        assert len(watcher.callbacks) == 1
        assert callback in watcher.callbacks
    
    def test_set_supported_extensions(self):
        """Test setting supported extensions."""
        watcher = FileWatcher()
        extensions = [".pdf", ".html", ".docx"]
        
        watcher.set_supported_extensions(extensions)
        
        assert watcher.supported_extensions == {".pdf", ".html", ".docx"}
    
    def test_add_watch_path_nonexistent(self):
        """Test adding non-existent watch path."""
        watcher = FileWatcher()
        
        with pytest.raises(FileNotFoundError):
            watcher.add_watch_path(Path("/nonexistent/path"))
    
    def test_add_watch_path_file(self):
        """Test adding file as watch path."""
        watcher = FileWatcher()
        
        with tempfile.NamedTemporaryFile() as tmp_file:
            with pytest.raises(ValueError):
                watcher.add_watch_path(Path(tmp_file.name))
    
    def test_add_watch_path_success(self):
        """Test successfully adding watch path."""
        watcher = FileWatcher()
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            watch_path = Path(tmp_dir)
            watcher.add_watch_path(watch_path)
            
            assert str(watch_path) in watcher.watched_paths
            assert watcher.watched_paths[str(watch_path)]["path"] == watch_path
    
    def test_get_watch_status(self):
        """Test getting watch status."""
        config = {"recursive": True}
        watcher = FileWatcher(config)
        watcher.set_supported_extensions([".pdf", ".html"])
        watcher.add_callback(Mock())
        
        status = watcher.get_watch_status()
        
        assert "is_running" in status
        assert "watched_paths" in status
        assert "supported_extensions" in status
        assert "callback_count" in status
        assert status["callback_count"] == 1
        assert ".pdf" in status["supported_extensions"]
        assert ".html" in status["supported_extensions"]


class TestBatchFileWatcher:
    """Test cases for BatchFileWatcher."""
    
    def test_initialization(self):
        """Test BatchFileWatcher initialization."""
        config = {"batch_size": 5, "batch_timeout": 3.0}
        watcher = BatchFileWatcher(config)
        
        assert watcher.batch_size == 5
        assert watcher.batch_timeout == 3.0
        assert len(watcher.pending_events) == 0
        assert len(watcher.batch_callbacks) == 0
    
    def test_add_batch_callback(self):
        """Test adding batch callbacks."""
        watcher = BatchFileWatcher()
        callback = Mock()
        
        watcher.add_batch_callback(callback)
        
        assert len(watcher.batch_callbacks) == 1
        assert callback in watcher.batch_callbacks
    
    def test_handle_file_event_batching(self):
        """Test file event batching."""
        config = {"batch_size": 2}
        watcher = BatchFileWatcher(config)
        callback = Mock()
        watcher.add_batch_callback(callback)
        
        # Add first event
        watcher._handle_file_event("created", Path("test1.pdf"), "file_created")
        assert len(watcher.pending_events) == 1
        callback.assert_not_called()
        
        # Add second event - should trigger batch processing
        watcher._handle_file_event("created", Path("test2.pdf"), "file_created")
        callback.assert_called_once()
        
        # Verify batch was processed
        assert len(watcher.pending_events) == 0
    
    def test_get_watch_status_batch(self):
        """Test getting batch watch status."""
        config = {"batch_size": 10, "batch_timeout": 5.0}
        watcher = BatchFileWatcher(config)
        watcher.add_batch_callback(Mock())
        
        status = watcher.get_watch_status()
        
        assert "batch_size" in status
        assert "batch_timeout" in status
        assert "pending_events" in status
        assert "batch_callback_count" in status
        assert status["batch_size"] == 10
        assert status["batch_timeout"] == 5.0
        assert status["batch_callback_count"] == 1


class TestDocumentChangeTracker:
    """Test cases for DocumentChangeTracker."""
    
    def test_initialization(self):
        """Test DocumentChangeTracker initialization."""
        config = {"hash_algorithm": "md5", "track_metadata": False}
        tracker = DocumentChangeTracker(config)
        
        assert tracker.hash_algorithm == "md5"
        assert tracker.track_metadata == False
        assert len(tracker.document_hashes) == 0
        assert len(tracker.document_metadata) == 0
    
    def test_calculate_file_hash(self):
        """Test file hash calculation."""
        tracker = DocumentChangeTracker()
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp_file:
            tmp_file.write("test content")
            tmp_file.flush()
            
            file_path = Path(tmp_file.name)
            hash1 = tracker.calculate_file_hash(file_path)
            hash2 = tracker.calculate_file_hash(file_path)
            
            # Same file should produce same hash
            assert hash1 == hash2
            assert len(hash1) > 0
            
            # Clean up
            file_path.unlink()
    
    def test_has_changed_new_file(self):
        """Test change detection for new file."""
        tracker = DocumentChangeTracker()
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp_file:
            tmp_file.write("test content")
            tmp_file.flush()
            
            file_path = Path(tmp_file.name)
            has_changed, change_type = tracker.has_changed(file_path)
            
            assert has_changed == True
            assert change_type == "created"
            
            # Clean up
            file_path.unlink()
    
    def test_has_changed_no_change(self):
        """Test change detection for unchanged file."""
        tracker = DocumentChangeTracker()
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp_file:
            tmp_file.write("test content")
            tmp_file.flush()
            
            file_path = Path(tmp_file.name)
            
            # First check - should be new
            has_changed, change_type = tracker.has_changed(file_path)
            assert has_changed == True
            assert change_type == "created"
            
            # Update tracking
            tracker.update_document_info(file_path)
            
            # Second check - should be unchanged
            has_changed, change_type = tracker.has_changed(file_path)
            assert has_changed == False
            assert change_type == "none"
            
            # Clean up
            file_path.unlink()
    
    def test_has_changed_modified_file(self):
        """Test change detection for modified file."""
        tracker = DocumentChangeTracker()
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp_file:
            tmp_file.write("original content")
            tmp_file.flush()
            
            file_path = Path(tmp_file.name)
            
            # Initial tracking
            tracker.update_document_info(file_path)
            
            # Modify file
            with open(file_path, 'w') as f:
                f.write("modified content")
            
            # Check for changes
            has_changed, change_type = tracker.has_changed(file_path)
            assert has_changed == True
            assert change_type == "modified"
            
            # Clean up
            file_path.unlink()
    
    def test_has_changed_deleted_file(self):
        """Test change detection for deleted file."""
        tracker = DocumentChangeTracker()
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp_file:
            tmp_file.write("test content")
            tmp_file.flush()
            
            file_path = Path(tmp_file.name)
            
            # Initial tracking
            tracker.update_document_info(file_path)
            
            # Delete file
            file_path.unlink()
            
            # Check for changes
            has_changed, change_type = tracker.has_changed(file_path)
            assert has_changed == True
            assert change_type == "deleted"
    
    def test_update_document_info_with_metadata(self):
        """Test updating document info with metadata."""
        config = {"track_metadata": True}
        tracker = DocumentChangeTracker(config)
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp_file:
            tmp_file.write("test content")
            tmp_file.flush()
            
            file_path = Path(tmp_file.name)
            metadata = {"title": "Test Document", "author": "Test Author"}
            
            tracker.update_document_info(file_path, metadata)
            
            file_key = str(file_path)
            assert file_key in tracker.document_hashes
            assert file_key in tracker.document_metadata
            assert tracker.document_metadata[file_key]["title"] == "Test Document"
            assert tracker.document_metadata[file_key]["author"] == "Test Author"
            
            # Clean up
            file_path.unlink()
    
    def test_get_document_info(self):
        """Test getting document information."""
        tracker = DocumentChangeTracker()
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp_file:
            file_path = Path(tmp_file.name)
            metadata = {"title": "Test Document"}
            
            tracker.update_document_info(file_path, metadata)
            retrieved_info = tracker.get_document_info(file_path)
            
            assert "title" in retrieved_info
            assert retrieved_info["title"] == "Test Document"
            
            # Clean up
            file_path.unlink()
    
    def test_cleanup_deleted_files(self):
        """Test cleanup of deleted files."""
        tracker = DocumentChangeTracker()
        
        # Create and track some files
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp_file1:
            file_path1 = Path(tmp_file1.name)
            tracker.update_document_info(file_path1)
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp_file2:
            file_path2 = Path(tmp_file2.name)
            tracker.update_document_info(file_path2)
        
        # Delete one file
        file_path1.unlink()
        
        # Cleanup should remove deleted file from tracking
        existing_files = {file_path2}
        deleted_files = tracker.cleanup_deleted_files(existing_files)
        
        assert len(deleted_files) == 1
        assert str(file_path1) in deleted_files
        assert str(file_path1) not in tracker.document_hashes
        assert str(file_path2) in tracker.document_hashes
        
        # Clean up
        file_path2.unlink()


class TestIncrementalProcessor:
    """Test cases for IncrementalProcessor."""
    
    @pytest.fixture
    def mock_ontology(self):
        """Create a mock ontology for testing."""
        ontology = Mock()
        ontology.extract_concepts.return_value = {"concepts": []}
        ontology.update_from_extraction = Mock()
        ontology.external_ontology_manager.enrich_concept = Mock(side_effect=lambda x: x)
        return ontology
    
    def test_initialization(self, mock_ontology):
        """Test IncrementalProcessor initialization."""
        config = {"max_concurrent_processing": 2}
        processor = IncrementalProcessor(mock_ontology, config)
        
        assert processor.ontology == mock_ontology
        assert processor.config == config
        assert processor.max_concurrent == 2
        assert not processor.is_running
        assert processor.stats["documents_processed"] == 0
    
    @pytest.mark.asyncio
    async def test_start_stop(self, mock_ontology):
        """Test starting and stopping the processor."""
        processor = IncrementalProcessor(mock_ontology)
        
        # Start processor
        await processor.start()
        assert processor.is_running
        assert processor.processing_task is not None
        
        # Stop processor
        await processor.stop()
        assert not processor.is_running
    
    @pytest.mark.asyncio
    async def test_process_file_event(self, mock_ontology):
        """Test processing file events."""
        processor = IncrementalProcessor(mock_ontology)
        
        await processor.start()
        
        # Process a file event
        await processor.process_file_event("created", Path("test.pdf"), "file_created")
        
        # Verify event was queued
        assert processor.processing_queue.qsize() > 0
        
        await processor.stop()
    
    @pytest.mark.asyncio
    async def test_process_batch_events(self, mock_ontology):
        """Test processing batch events."""
        processor = IncrementalProcessor(mock_ontology)
        
        events = [
            {"event_type": "created", "file_path": Path("test1.pdf"), "event_name": "file_created"},
            {"event_type": "modified", "file_path": Path("test2.pdf"), "event_name": "file_modified"},
        ]
        
        await processor.start()
        await processor.process_batch_events(events)
        
        # Verify events were queued
        assert processor.processing_queue.qsize() >= len(events)
        
        await processor.stop()
    
    def test_get_processing_stats(self, mock_ontology):
        """Test getting processing statistics."""
        processor = IncrementalProcessor(mock_ontology)
        
        stats = processor.get_processing_stats()
        
        assert "documents_processed" in stats
        assert "documents_created" in stats
        assert "documents_modified" in stats
        assert "documents_deleted" in stats
        assert "processing_errors" in stats
        assert "queue_size" in stats
        assert "is_running" in stats
        assert "max_concurrent" in stats
        assert "tracked_documents" in stats
    
    @pytest.mark.asyncio
    async def test_sync_directory(self, mock_ontology):
        """Test directory synchronization."""
        processor = IncrementalProcessor(mock_ontology)
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create some test files
            test_file1 = Path(tmp_dir) / "test1.pdf"
            test_file2 = Path(tmp_dir) / "test2.html"
            
            test_file1.write_text("test content 1")
            test_file2.write_text("<html><body>test content 2</body></html>")
            
            # Mock document detector
            with patch("src.monitoring.incremental_processor.DocumentDetector") as mock_detector_class:
                mock_detector = Mock()
                mock_detector.get_supported_extensions.return_value = [".pdf", ".html"]
                mock_detector.detect_document_type.return_value = Mock(
                    extract_text=Mock(return_value="test content"),
                    extract_metadata=Mock(return_value={"title": "test"})
                )
                mock_detector_class.return_value = mock_detector
                
                processor.document_detector = mock_detector
                
                # Synchronize directory
                results = await processor.sync_directory(Path(tmp_dir))
                
                assert "processed" in results
                assert "skipped" in results
                assert "errors" in results
                assert "files" in results