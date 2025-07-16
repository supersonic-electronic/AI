"""
Unit tests for optimization components.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
import tempfile
import time

from src.optimization.batch_processor import BatchProcessor, ProgressTracker
from src.optimization.concept_deduplicator import ConceptDeduplicator, DocumentTypeAwareDedupicator
from src.knowledge.concept import Concept


class TestBatchProcessor:
    """Test cases for BatchProcessor."""
    
    @pytest.fixture
    def mock_ontology(self):
        """Create a mock ontology for testing."""
        ontology = Mock()
        ontology.extract_concepts.return_value = {"concepts": []}
        ontology.update_from_extraction = Mock()
        ontology.external_ontology_manager.enrich_concept = Mock(side_effect=lambda x: x)
        return ontology
    
    def test_initialization(self, mock_ontology):
        """Test BatchProcessor initialization."""
        config = {"max_workers": 2, "batch_size": 5}
        processor = BatchProcessor(mock_ontology, config)
        
        assert processor.ontology == mock_ontology
        assert processor.config == config
        assert processor.max_workers == 2
        assert processor.batch_size == 5
        assert processor.stats["total_documents"] == 0
    
    def test_collect_files(self, mock_ontology):
        """Test file collection from directory."""
        processor = BatchProcessor(mock_ontology)
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create test files
            test_files = [
                Path(tmp_dir) / "test1.pdf",
                Path(tmp_dir) / "test2.html",
                Path(tmp_dir) / "test3.txt",  # Should be ignored
                Path(tmp_dir) / "test4.docx",
            ]
            
            for file_path in test_files:
                file_path.write_text("test content")
            
            # Mock document detector
            with patch.object(processor.document_detector, 'get_supported_extensions') as mock_extensions:
                mock_extensions.return_value = [".pdf", ".html", ".docx"]
                
                files = processor._collect_files(Path(tmp_dir), recursive=False)
                
                # Should find PDF, HTML, and DOCX files, but not TXT
                assert len(files) == 3
                assert any(f.name == "test1.pdf" for f in files)
                assert any(f.name == "test2.html" for f in files)
                assert any(f.name == "test4.docx" for f in files)
                assert not any(f.name == "test3.txt" for f in files)
    
    def test_should_process_file_size_filter(self, mock_ontology):
        """Test file size filtering."""
        config = {"max_file_size_mb": 1}  # 1 MB limit
        processor = BatchProcessor(mock_ontology, config)
        
        with tempfile.NamedTemporaryFile() as tmp_file:
            file_path = Path(tmp_file.name)
            
            # Mock file size - under limit
            with patch.object(file_path, 'stat') as mock_stat:
                mock_stat.return_value = Mock(st_size=500 * 1024)  # 500 KB
                assert processor._should_process_file(file_path)
                
                # Mock file size - over limit
                mock_stat.return_value = Mock(st_size=2 * 1024 * 1024)  # 2 MB
                assert not processor._should_process_file(file_path)
    
    def test_should_process_file_ignore_patterns(self, mock_ontology):
        """Test file ignore patterns."""
        config = {"ignore_patterns": ["*temp*", ".*"]}
        processor = BatchProcessor(mock_ontology, config)
        
        # Should process normal files
        assert processor._should_process_file(Path("document.pdf"))
        
        # Should ignore files matching patterns
        assert not processor._should_process_file(Path("temp_file.pdf"))
        assert not processor._should_process_file(Path(".hidden_file.pdf"))
        assert not processor._should_process_file(Path("my_temp_document.pdf"))
    
    def test_process_single_file_success(self, mock_ontology):
        """Test successful single file processing."""
        processor = BatchProcessor(mock_ontology)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.pdf', delete=False) as tmp_file:
            tmp_file.write("test content")
            tmp_file.flush()
            
            file_path = Path(tmp_file.name)
            
            # Mock document detector and extractor
            mock_extractor = Mock()
            mock_extractor.extract_text.return_value = "extracted text"
            mock_extractor.extract_metadata.return_value = {"title": "test"}
            mock_extractor.extractor_name = "Test Extractor"
            
            with patch.object(processor.document_detector, 'detect_document_type') as mock_detect:
                mock_detect.return_value = mock_extractor
                
                result = processor._process_single_file(file_path)
                
                assert result["success"] == True
                assert result["file_path"] == str(file_path)
                assert result["extractor"] == "Test Extractor"
                assert "processing_time" in result
                assert "file_size" in result
            
            # Clean up
            file_path.unlink()
    
    def test_process_single_file_no_extractor(self, mock_ontology):
        """Test file processing when no extractor is found."""
        processor = BatchProcessor(mock_ontology)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.unknown', delete=False) as tmp_file:
            file_path = Path(tmp_file.name)
            
            # Mock document detector to return None
            with patch.object(processor.document_detector, 'detect_document_type') as mock_detect:
                mock_detect.return_value = None
                
                result = processor._process_single_file(file_path)
                
                assert result["success"] == False
                assert "No suitable extractor" in result["error"]
            
            # Clean up
            file_path.unlink()
    
    def test_process_single_file_extraction_error(self, mock_ontology):
        """Test file processing when extraction fails."""
        processor = BatchProcessor(mock_ontology)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.pdf', delete=False) as tmp_file:
            file_path = Path(tmp_file.name)
            
            # Mock extractor that raises exception
            mock_extractor = Mock()
            mock_extractor.extract_text.side_effect = Exception("Extraction failed")
            
            with patch.object(processor.document_detector, 'detect_document_type') as mock_detect:
                mock_detect.return_value = mock_extractor
                
                result = processor._process_single_file(file_path)
                
                assert result["success"] == False
                assert "Extraction failed" in result["error"]
            
            # Clean up
            file_path.unlink()
    
    @pytest.mark.asyncio
    async def test_process_files(self, mock_ontology):
        """Test processing a list of files."""
        processor = BatchProcessor(mock_ontology)
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create test files
            file_paths = []
            for i in range(3):
                file_path = Path(tmp_dir) / f"test{i}.pdf"
                file_path.write_text(f"test content {i}")
                file_paths.append(file_path)
            
            # Mock document detector and extractor
            mock_extractor = Mock()
            mock_extractor.extract_text.return_value = "extracted text"
            mock_extractor.extract_metadata.return_value = {"title": "test"}
            mock_extractor.extractor_name = "Test Extractor"
            
            with patch.object(processor.document_detector, 'detect_document_type') as mock_detect:
                mock_detect.return_value = mock_extractor
                
                results = await processor.process_files(file_paths)
                
                assert "summary" in results
                assert "successful_files" in results
                assert "failed_files" in results
                assert results["summary"]["total_files"] == 3
                assert results["summary"]["successful"] == 3
                assert results["summary"]["failed"] == 0
    
    def test_get_statistics(self, mock_ontology):
        """Test getting processing statistics."""
        processor = BatchProcessor(mock_ontology)
        
        stats = processor.get_statistics()
        
        assert "total_documents" in stats
        assert "processed_documents" in stats
        assert "failed_documents" in stats
        assert "total_processing_time" in stats
        assert "average_processing_time" in stats
        assert "throughput_docs_per_second" in stats
    
    def test_reset_statistics(self, mock_ontology):
        """Test resetting statistics."""
        processor = BatchProcessor(mock_ontology)
        
        # Modify some stats
        processor.stats["total_documents"] = 10
        processor.stats["processed_documents"] = 8
        
        # Reset
        processor.reset_statistics()
        
        assert processor.stats["total_documents"] == 0
        assert processor.stats["processed_documents"] == 0
    
    def test_shutdown(self, mock_ontology):
        """Test shutting down the processor."""
        processor = BatchProcessor(mock_ontology)
        
        # Should not raise any exceptions
        processor.shutdown()


class TestProgressTracker:
    """Test cases for ProgressTracker."""
    
    def test_initialization(self):
        """Test ProgressTracker initialization."""
        tracker = ProgressTracker(total_items=100, update_interval=0.5)
        
        assert tracker.total_items == 100
        assert tracker.update_interval == 0.5
        assert tracker.processed_items == 0
        assert not tracker.cancelled
        assert len(tracker.progress_callbacks) == 0
    
    def test_add_progress_callback(self):
        """Test adding progress callbacks."""
        tracker = ProgressTracker(100)
        callback = Mock()
        
        tracker.add_progress_callback(callback)
        
        assert len(tracker.progress_callbacks) == 1
        assert callback in tracker.progress_callbacks
    
    def test_update_progress(self):
        """Test updating progress."""
        tracker = ProgressTracker(100)
        callback = Mock()
        tracker.add_progress_callback(callback)
        
        # Update progress
        tracker.update(5)
        
        assert tracker.processed_items == 5
        callback.assert_called_once()
        
        # Get the call arguments
        call_args = callback.call_args[0][0]
        assert call_args["processed"] == 5
        assert call_args["total"] == 100
        assert call_args["progress_percent"] == 5.0
    
    def test_set_progress(self):
        """Test setting absolute progress."""
        tracker = ProgressTracker(100)
        callback = Mock()
        tracker.add_progress_callback(callback)
        
        # Set progress
        tracker.set_progress(25)
        
        assert tracker.processed_items == 25
        callback.assert_called_once()
    
    def test_set_progress_clamping(self):
        """Test progress clamping to total."""
        tracker = ProgressTracker(100)
        
        # Set progress beyond total
        tracker.set_progress(150)
        
        assert tracker.processed_items == 100  # Should be clamped
    
    def test_cancel(self):
        """Test cancelling progress."""
        tracker = ProgressTracker(100)
        callback = Mock()
        tracker.add_progress_callback(callback)
        
        tracker.cancel()
        
        assert tracker.cancelled
        assert tracker.is_cancelled()
        callback.assert_called_once()
    
    def test_is_complete(self):
        """Test completion detection."""
        tracker = ProgressTracker(100)
        
        assert not tracker.is_complete()
        
        tracker.set_progress(100)
        assert tracker.is_complete()
        
        tracker.set_progress(150)  # Beyond total
        assert tracker.is_complete()
    
    def test_get_progress_info_eta_calculation(self):
        """Test ETA calculation in progress info."""
        tracker = ProgressTracker(100)
        
        # Simulate some progress over time
        start_time = time.time() - 10  # 10 seconds ago
        tracker.start_time = start_time
        tracker.processed_items = 25
        
        progress_info = tracker.get_progress_info()
        
        assert progress_info["processed"] == 25
        assert progress_info["total"] == 100
        assert progress_info["progress_percent"] == 25.0
        assert progress_info["elapsed_time"] >= 10
        assert progress_info["eta_seconds"] > 0  # Should have ETA
        assert progress_info["rate_per_second"] > 0
    
    def test_get_progress_info_no_progress(self):
        """Test progress info when no progress made."""
        tracker = ProgressTracker(100)
        
        progress_info = tracker.get_progress_info()
        
        assert progress_info["processed"] == 0
        assert progress_info["total"] == 100
        assert progress_info["progress_percent"] == 0.0
        assert progress_info["eta_seconds"] == 0
        assert progress_info["rate_per_second"] == 0


class TestConceptDeduplicator:
    """Test cases for ConceptDeduplicator."""
    
    def test_initialization(self):
        """Test ConceptDeduplicator initialization."""
        config = {"similarity_threshold": 0.9, "ignore_case": False}
        deduplicator = ConceptDeduplicator(config)
        
        assert deduplicator.similarity_threshold == 0.9
        assert deduplicator.ignore_case == False
        assert deduplicator.stats["concepts_processed"] == 0
    
    def test_normalize_text(self):
        """Test text normalization."""
        config = {"ignore_case": True, "normalize_whitespace": True}
        deduplicator = ConceptDeduplicator(config)
        
        # Test case normalization
        normalized = deduplicator._normalize_text("Test STRING")
        assert normalized == "test string"
        
        # Test whitespace normalization
        normalized = deduplicator._normalize_text("  Multiple   spaces  ")
        assert normalized == "multiple spaces"
        
        # Test empty string
        normalized = deduplicator._normalize_text("")
        assert normalized == ""
    
    def test_calculate_text_similarity_identical(self):
        """Test text similarity for identical texts."""
        deduplicator = ConceptDeduplicator()
        
        similarity = deduplicator._calculate_text_similarity("test text", "test text")
        assert similarity == 1.0
    
    def test_calculate_text_similarity_different(self):
        """Test text similarity for different texts."""
        deduplicator = ConceptDeduplicator()
        
        similarity = deduplicator._calculate_text_similarity("completely different", "totally unrelated")
        assert similarity == 0.0
    
    def test_calculate_text_similarity_partial(self):
        """Test text similarity for partially similar texts."""
        deduplicator = ConceptDeduplicator()
        
        similarity = deduplicator._calculate_text_similarity("test document", "test file")
        assert 0.0 < similarity < 1.0
    
    def test_concept_completeness_score(self):
        """Test concept completeness scoring."""
        deduplicator = ConceptDeduplicator()
        
        # Create concepts with different levels of completeness
        minimal_concept = Concept(name="Test", concept_type="term")
        
        complete_concept = Concept(
            name="Complete Test",
            concept_type="formula",
            description="A comprehensive test concept with detailed information",
            definition="This is a detailed definition of the concept",
            symbol="CT",
            properties={"category": "test", "complexity": "high"},
            relationships=[{"type": "related_to", "target": "other_concept"}],
            examples=["Example 1", "Example 2"]
        )
        
        minimal_score = deduplicator._concept_completeness_score(minimal_concept)
        complete_score = deduplicator._concept_completeness_score(complete_concept)
        
        assert complete_score > minimal_score
    
    def test_merge_text_field(self):
        """Test merging text fields."""
        deduplicator = ConceptDeduplicator()
        
        # Test merging with duplicates
        values = ["short", "longer description", "short"]
        merged = deduplicator._merge_text_field(values)
        assert merged == "longer description"  # Should prefer longest
        
        # Test empty list
        merged = deduplicator._merge_text_field([])
        assert merged == ""
        
        # Test single value
        merged = deduplicator._merge_text_field(["single value"])
        assert merged == "single value"
    
    def test_merge_properties(self):
        """Test merging properties."""
        deduplicator = ConceptDeduplicator()
        
        property_lists = [
            {"category": "math", "level": "basic"},
            {"category": "finance", "type": "formula"},
            {"level": "advanced", "examples": ["a", "b"]}
        ]
        
        merged = deduplicator._merge_properties(property_lists)
        
        # Should have all unique keys
        assert "category" in merged
        assert "level" in merged
        assert "type" in merged
        assert "examples" in merged
        
        # Conflicting values should be stored as lists
        assert isinstance(merged["category"], list)
        assert "math" in merged["category"]
        assert "finance" in merged["category"]
    
    def test_merge_relationships(self):
        """Test merging relationships."""
        deduplicator = ConceptDeduplicator()
        
        relationship_lists = [
            [{"type": "related_to", "target": "concept1", "direction": "bidirectional"}],
            [{"type": "part_of", "target": "concept2", "direction": "forward"}],
            [{"type": "related_to", "target": "concept1", "direction": "bidirectional"}]  # Duplicate
        ]
        
        merged = deduplicator._merge_relationships(relationship_lists)
        
        # Should have 2 unique relationships
        assert len(merged) == 2
        
        # Verify relationships are preserved
        types = [rel["type"] for rel in merged]
        assert "related_to" in types
        assert "part_of" in types
    
    def test_merge_examples(self):
        """Test merging examples."""
        deduplicator = ConceptDeduplicator()
        
        example_lists = [
            ["Example 1", "Example 2"],
            ["Example 3", "Example 1"],  # Duplicate
            ["Example 4"]
        ]
        
        merged = deduplicator._merge_examples(example_lists)
        
        # Should have 4 unique examples
        assert len(merged) == 4
        assert "Example 1" in merged
        assert "Example 2" in merged
        assert "Example 3" in merged
        assert "Example 4" in merged
    
    def test_merge_concepts(self):
        """Test merging multiple concepts."""
        deduplicator = ConceptDeduplicator()
        
        concept1 = Concept(
            name="Test Concept",
            concept_type="term",
            description="First description",
            confidence=0.8
        )
        
        concept2 = Concept(
            name="Test Concept",
            concept_type="term",
            description="Second longer description with more details",
            symbol="TC",
            confidence=0.9
        )
        
        concepts = [concept1, concept2]
        merged = deduplicator._merge_concepts(concepts)
        
        assert merged.name == "Test Concept"
        assert merged.concept_type == "term"
        assert merged.description == "Second longer description with more details"  # Longer one
        assert merged.symbol == "TC"
        assert merged.confidence == 0.9  # Higher confidence
        assert hasattr(merged, 'merged_from')
        assert merged.merged_from == 2
    
    def test_deduplicate_concepts_no_duplicates(self):
        """Test deduplication with no duplicates."""
        deduplicator = ConceptDeduplicator()
        
        concepts = [
            Concept(name="Concept A", concept_type="term"),
            Concept(name="Concept B", concept_type="formula"),
            Concept(name="Concept C", concept_type="theorem")
        ]
        
        deduplicated = deduplicator.deduplicate_concepts(concepts)
        
        # Should return same number of concepts
        assert len(deduplicated) == 3
        assert deduplicator.stats["duplicates_found"] == 0
    
    def test_deduplicate_concepts_with_duplicates(self):
        """Test deduplication with duplicates."""
        config = {"similarity_threshold": 0.8}
        deduplicator = ConceptDeduplicator(config)
        
        concepts = [
            Concept(name="Test Concept", concept_type="term", description="First description"),
            Concept(name="Test Concept", concept_type="term", description="Second description"),  # Duplicate
            Concept(name="Different Concept", concept_type="formula")
        ]
        
        deduplicated = deduplicator.deduplicate_concepts(concepts)
        
        # Should merge the duplicates
        assert len(deduplicated) == 2
        assert deduplicator.stats["duplicates_found"] == 1
        assert deduplicator.stats["concepts_merged"] == 1
        assert deduplicator.stats["exact_matches"] == 1  # Same name
    
    def test_get_statistics(self):
        """Test getting deduplication statistics."""
        deduplicator = ConceptDeduplicator()
        
        stats = deduplicator.get_statistics()
        
        assert "concepts_processed" in stats
        assert "duplicates_found" in stats
        assert "concepts_merged" in stats
        assert "exact_matches" in stats
        assert "fuzzy_matches" in stats
    
    def test_reset_statistics(self):
        """Test resetting statistics."""
        deduplicator = ConceptDeduplicator()
        
        # Modify some stats
        deduplicator.stats["concepts_processed"] = 10
        deduplicator.stats["duplicates_found"] = 2
        
        # Reset
        deduplicator.reset_statistics()
        
        assert deduplicator.stats["concepts_processed"] == 0
        assert deduplicator.stats["duplicates_found"] == 0
    
    def test_clear_caches(self):
        """Test clearing caches."""
        deduplicator = ConceptDeduplicator()
        
        # Add some cache entries
        deduplicator.concept_hashes["test"] = "hash"
        deduplicator.similarity_cache["test"] = 0.5
        
        # Clear caches
        deduplicator.clear_caches()
        
        assert len(deduplicator.concept_hashes) == 0
        assert len(deduplicator.similarity_cache) == 0


class TestDocumentTypeAwareDedupicator:
    """Test cases for DocumentTypeAwareDedupicator."""
    
    def test_initialization(self):
        """Test DocumentTypeAwareDedupicator initialization."""
        config = {
            "type_specific_thresholds": {"pdf_html": 0.7},
            "type_priority": {"pdf": 1.0, "html": 0.8}
        }
        deduplicator = DocumentTypeAwareDedupicator(config)
        
        assert deduplicator.type_specific_thresholds["pdf_html"] == 0.7
        assert deduplicator.type_priority["pdf"] == 1.0
        assert deduplicator.type_priority["html"] == 0.8
    
    def test_get_concept_document_type(self):
        """Test getting document type from concept."""
        deduplicator = DocumentTypeAwareDedupicator()
        
        # Test with explicit document type
        concept = Concept(name="Test", concept_type="term")
        concept.source_document_type = "PDF"
        
        doc_type = deduplicator._get_concept_document_type(concept)
        assert doc_type == "pdf"
        
        # Test with source documents
        concept2 = Concept(name="Test2", concept_type="term")
        concept2.source_documents = ["document.html"]
        
        doc_type = deduplicator._get_concept_document_type(concept2)
        assert doc_type == "html"
        
        # Test with unknown type
        concept3 = Concept(name="Test3", concept_type="term")
        
        doc_type = deduplicator._get_concept_document_type(concept3)
        assert doc_type == "unknown"
    
    def test_compute_similarity_with_type_adjustment(self):
        """Test similarity computation with document type adjustment."""
        config = {"type_specific_thresholds": {"pdf_html": 0.7}}
        deduplicator = DocumentTypeAwareDedupicator(config)
        
        # Create concepts with different document types
        concept1 = Concept(name="Test Concept", concept_type="term")
        concept1.source_documents = ["doc.pdf"]
        
        concept2 = Concept(name="Test Concept", concept_type="term")
        concept2.source_documents = ["doc.html"]
        
        # Mock the base similarity calculation
        with patch.object(ConceptDeduplicator, '_compute_similarity') as mock_base:
            mock_base.return_value = 0.8
            
            similarity = deduplicator._compute_similarity(concept1, concept2)
            
            # Should apply document type penalty for different types
            assert similarity < 0.8  # Should be reduced
            mock_base.assert_called_once()
    
    def test_merge_concepts_with_priority(self):
        """Test concept merging with document type priority."""
        config = {"type_priority": {"pdf": 1.0, "html": 0.8, "docx": 0.6}}
        deduplicator = DocumentTypeAwareDedupicator(config)
        
        # Create concepts with different priorities
        concept1 = Concept(name="Test", concept_type="term", description="HTML description")
        concept1.source_documents = ["doc.html"]
        
        concept2 = Concept(name="Test", concept_type="term", description="PDF description")
        concept2.source_documents = ["doc.pdf"]
        
        concept3 = Concept(name="Test", concept_type="term", description="DOCX description")
        concept3.source_documents = ["doc.docx"]
        
        concepts = [concept1, concept2, concept3]
        merged = deduplicator._merge_concepts(concepts)
        
        # Should use PDF as base (highest priority)
        assert "PDF description" in merged.description
        assert hasattr(merged, 'primary_source_type')
        assert merged.primary_source_type == "pdf"
        assert hasattr(merged, 'source_types')
        assert "pdf" in merged.source_types
        assert "html" in merged.source_types
        assert "docx" in merged.source_types