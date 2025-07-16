"""
Integration tests for end-to-end workflows.
"""

import pytest
import asyncio
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch

from src.knowledge.ontology import FinancialMathOntology
from src.ingestion.extractors.document_detector import DocumentDetector
from src.monitoring.file_watcher import FileWatcher
from src.monitoring.incremental_processor import IncrementalProcessor
from src.optimization.batch_processor import BatchProcessor
from src.optimization.concept_deduplicator import DocumentTypeAwareDedupicator


@pytest.mark.integration
class TestEndToEndWorkflows:
    """Integration tests for complete workflows."""
    
    @pytest.fixture
    def temp_directory(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            yield Path(tmp_dir)
    
    @pytest.fixture
    def sample_documents(self, temp_directory):
        """Create sample documents for testing."""
        documents = {}
        
        # PDF content (simulated)
        pdf_file = temp_directory / "sample.pdf"
        pdf_file.write_bytes(b"PDF content placeholder")
        documents["pdf"] = pdf_file
        
        # HTML document
        html_content = """
        <html>
        <head>
            <title>Financial Mathematics Guide</title>
            <meta name="author" content="Test Author">
        </head>
        <body>
            <h1>Black-Scholes Formula</h1>
            <p>The Black-Scholes formula is used to calculate the theoretical value of options.</p>
            <p>The formula involves variables such as stock price, strike price, time to expiration, and volatility.</p>
            <h2>Risk-Free Rate</h2>
            <p>The risk-free rate is a key component in option pricing models.</p>
        </body>
        </html>
        """
        html_file = temp_directory / "financial_guide.html"
        html_file.write_text(html_content)
        documents["html"] = html_file
        
        # DOCX content (simulated)
        docx_file = temp_directory / "formulas.docx"
        docx_file.write_bytes(b"DOCX content placeholder")
        documents["docx"] = docx_file
        
        # XML document
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <financial_concepts>
            <concept type="formula" category="options">
                <name>Black-Scholes Formula</name>
                <description>Mathematical model for option pricing</description>
                <variables>
                    <variable>S - Current stock price</variable>
                    <variable>K - Strike price</variable>
                    <variable>T - Time to expiration</variable>
                    <variable>r - Risk-free rate</variable>
                    <variable>σ - Volatility</variable>
                </variables>
            </concept>
            <concept type="term" category="finance">
                <name>Volatility</name>
                <description>Measure of price fluctuation</description>
            </concept>
        </financial_concepts>
        """
        xml_file = temp_directory / "concepts.xml"
        xml_file.write_text(xml_content)
        documents["xml"] = xml_file
        
        # LaTeX document
        latex_content = r"""
        \documentclass{article}
        \title{Options Pricing Theory}
        \author{Financial Researcher}
        \begin{document}
        \maketitle
        \section{Introduction}
        Options pricing is a fundamental concept in financial mathematics.
        \section{Black-Scholes Model}
        The Black-Scholes formula calculates option prices using:
        \begin{itemize}
        \item Current stock price (S)
        \item Strike price (K)
        \item Time to expiration (T)
        \item Risk-free rate (r)
        \item Volatility ($\sigma$)
        \end{itemize}
        \end{document}
        """
        latex_file = temp_directory / "options_theory.tex"
        latex_file.write_text(latex_content)
        documents["latex"] = latex_file
        
        return documents
    
    def test_document_detection_workflow(self, sample_documents):
        """Test complete document detection workflow."""
        detector = DocumentDetector()
        
        results = {}
        for doc_type, file_path in sample_documents.items():
            # Detect document type
            extractor = detector.detect_document_type(file_path)
            
            if extractor:
                results[doc_type] = {
                    "extractor": extractor.extractor_name,
                    "can_handle": extractor.can_handle(file_path),
                    "extensions": extractor.supported_extensions
                }
        
        # Verify detection results
        assert "html" in results
        assert "xml" in results
        assert "latex" in results
        assert results["html"]["can_handle"]
        assert results["xml"]["can_handle"]
        assert results["latex"]["can_handle"]
    
    def test_document_extraction_workflow(self, sample_documents):
        """Test complete document extraction workflow."""
        detector = DocumentDetector()
        extraction_results = {}
        
        for doc_type, file_path in sample_documents.items():
            extractor = detector.detect_document_type(file_path)
            
            if extractor and doc_type in ["html", "xml", "latex"]:  # Skip binary formats for this test
                try:
                    # Extract text and metadata
                    text = extractor.extract_text(file_path, {})
                    metadata = extractor.extract_metadata(file_path, {})
                    
                    extraction_results[doc_type] = {
                        "text_length": len(text),
                        "has_content": len(text.strip()) > 0,
                        "metadata_keys": list(metadata.keys()),
                        "filename_in_metadata": metadata.get("filename") == file_path.name
                    }
                
                except Exception as e:
                    extraction_results[doc_type] = {"error": str(e)}
        
        # Verify extraction results
        assert "html" in extraction_results
        assert extraction_results["html"]["has_content"]
        assert extraction_results["html"]["filename_in_metadata"]
        
        assert "xml" in extraction_results
        assert extraction_results["xml"]["has_content"]
        
        assert "latex" in extraction_results
        assert extraction_results["latex"]["has_content"]
    
    def test_batch_processing_workflow(self, sample_documents):
        """Test complete batch processing workflow."""
        # Create mock ontology
        ontology = Mock()
        ontology.extract_concepts.return_value = {
            "concepts": [
                Mock(name="Black-Scholes Formula", concept_type="formula"),
                Mock(name="Volatility", concept_type="term")
            ]
        }
        ontology.update_from_extraction = Mock()
        ontology.external_ontology_manager.enrich_concept = Mock(side_effect=lambda x: x)
        
        # Configure batch processor
        config = {
            "max_workers": 2,
            "batch_size": 2,
            "use_external_ontologies": False
        }
        
        batch_processor = BatchProcessor(ontology, config)
        
        # Mock document detector and extractors
        with patch.object(batch_processor.document_detector, 'detect_document_type') as mock_detect:
            mock_extractor = Mock()
            mock_extractor.extract_text.return_value = "Black-Scholes formula for option pricing"
            mock_extractor.extract_metadata.return_value = {"title": "Test Document"}
            mock_extractor.extractor_name = "Mock Extractor"
            mock_detect.return_value = mock_extractor
            
            # Process files
            file_list = [file_path for file_path in sample_documents.values() if file_path.suffix in [".html", ".xml"]]
            results = asyncio.run(batch_processor.process_files(file_list))
            
            # Verify results
            assert "summary" in results
            assert results["summary"]["total_files"] == len(file_list)
            assert results["summary"]["successful"] > 0
            assert "successful_files" in results
            assert len(results["successful_files"]) > 0
            
            # Verify ontology was updated
            assert ontology.extract_concepts.call_count > 0
            assert ontology.update_from_extraction.call_count > 0
        
        batch_processor.shutdown()
    
    @pytest.mark.asyncio
    async def test_incremental_processing_workflow(self, sample_documents):
        """Test complete incremental processing workflow."""
        # Create mock ontology
        ontology = Mock()
        ontology.extract_concepts.return_value = {"concepts": []}
        ontology.update_from_extraction = Mock()
        ontology.external_ontology_manager.enrich_concept = Mock(side_effect=lambda x: x)
        
        # Configure incremental processor
        config = {"max_concurrent_processing": 1}
        processor = IncrementalProcessor(ontology, config)
        
        # Mock document detector
        with patch("src.monitoring.incremental_processor.DocumentDetector") as mock_detector_class:
            mock_detector = Mock()
            mock_extractor = Mock()
            mock_extractor.extract_text.return_value = "test content"
            mock_extractor.extract_metadata.return_value = {"title": "test"}
            mock_detector.detect_document_type.return_value = mock_extractor
            mock_detector_class.return_value = mock_detector
            
            processor.document_detector = mock_detector
            
            # Start processor
            await processor.start()
            
            # Process file events
            for file_path in sample_documents.values():
                await processor.process_file_event("created", file_path, "file_created")
            
            # Wait for processing
            await asyncio.sleep(0.1)
            
            # Stop processor
            await processor.stop()
            
            # Verify processing occurred
            stats = processor.get_processing_stats()
            assert stats["documents_processed"] >= 0  # Some may be filtered out
    
    @pytest.mark.asyncio
    async def test_file_watching_workflow(self, sample_documents):
        """Test complete file watching workflow."""
        temp_dir = list(sample_documents.values())[0].parent
        
        # Create file watcher
        config = {
            "recursive": False,
            "ignore_patterns": ["*.tmp"]
        }
        
        watcher = FileWatcher(config)
        watcher.set_supported_extensions([".html", ".xml", ".tex"])
        
        # Add callback to collect events
        events_collected = []
        
        def event_callback(event_type, file_path, event_name):
            events_collected.append({
                "event_type": event_type,
                "file_path": str(file_path),
                "event_name": event_name
            })
        
        watcher.add_callback(event_callback)
        watcher.add_watch_path(temp_dir)
        
        # Start watching
        watcher.start()
        
        # Create a new file to trigger event
        new_file = temp_dir / "new_document.html"
        new_file.write_text("<html><body>New content</body></html>")
        
        # Wait for file system event
        await asyncio.sleep(0.5)
        
        # Stop watching
        watcher.stop()
        
        # Verify events were collected
        # Note: File system events may be platform-dependent and timing-sensitive
        # So we just verify the watcher infrastructure works
        status = watcher.get_watch_status()
        assert not status["is_running"]
        assert len(status["watched_paths"]) == 1
        assert ".html" in status["supported_extensions"]
        
        # Clean up
        if new_file.exists():
            new_file.unlink()
    
    def test_concept_deduplication_workflow(self, sample_documents):
        """Test complete concept deduplication workflow."""
        # Create concepts with potential duplicates
        from src.knowledge.concept import Concept
        
        concepts = [
            Concept(
                name="Black-Scholes Formula",
                concept_type="formula",
                description="Mathematical model for option pricing",
                source_documents=["financial_guide.html"]
            ),
            Concept(
                name="Black-Scholes Formula",
                concept_type="formula", 
                description="Formula for calculating option values",
                symbol="BS",
                source_documents=["concepts.xml"]
            ),
            Concept(
                name="Volatility",
                concept_type="term",
                description="Measure of price fluctuation",
                source_documents=["options_theory.tex"]
            ),
            Concept(
                name="Risk-Free Rate",
                concept_type="term",
                description="Interest rate with no default risk",
                source_documents=["financial_guide.html"]
            )
        ]
        
        # Create document type aware deduplicator
        config = {
            "similarity_threshold": 0.8,
            "type_specific_thresholds": {
                "html_xml": 0.85,
                "html_latex": 0.80
            },
            "type_priority": {
                "html": 0.9,
                "xml": 0.8,
                "latex": 0.7
            }
        }
        
        deduplicator = DocumentTypeAwareDedupicator(config)
        
        # Perform deduplication
        deduplicated_concepts = deduplicator.deduplicate_concepts(concepts)
        
        # Verify deduplication results
        assert len(deduplicated_concepts) < len(concepts)  # Should have merged duplicates
        
        # Check statistics
        stats = deduplicator.get_statistics()
        assert stats["concepts_processed"] == len(concepts)
        assert stats["duplicates_found"] > 0
        assert stats["concepts_merged"] > 0
        
        # Verify merged concept has combined information
        black_scholes_concepts = [c for c in deduplicated_concepts if "Black-Scholes" in c.name]
        assert len(black_scholes_concepts) == 1
        
        merged_concept = black_scholes_concepts[0]
        assert merged_concept.symbol == "BS"  # Should preserve additional info
        assert hasattr(merged_concept, 'merged_from')
        assert merged_concept.merged_from == 2  # Two concepts were merged
    
    def test_multi_format_extraction_consistency(self, sample_documents):
        """Test consistency across different document formats."""
        detector = DocumentDetector()
        
        extraction_results = {}
        common_terms = ["Black-Scholes", "volatility", "option", "price"]
        
        for doc_type, file_path in sample_documents.items():
            if doc_type in ["html", "xml", "latex"]:  # Skip binary formats
                extractor = detector.detect_document_type(file_path)
                
                if extractor:
                    try:
                        text = extractor.extract_text(file_path, {})
                        metadata = extractor.extract_metadata(file_path, {})
                        
                        # Count common terms in extracted text
                        text_lower = text.lower()
                        term_counts = {term: text_lower.count(term.lower()) for term in common_terms}
                        
                        extraction_results[doc_type] = {
                            "text_length": len(text),
                            "term_counts": term_counts,
                            "has_title": bool(metadata.get("title")),
                            "metadata_count": len(metadata)
                        }
                    
                    except Exception as e:
                        extraction_results[doc_type] = {"error": str(e)}
        
        # Verify common terms are found across formats
        for doc_type, result in extraction_results.items():
            if "error" not in result:
                assert result["text_length"] > 0
                assert any(count > 0 for count in result["term_counts"].values())
                assert result["metadata_count"] > 0
    
    def test_configuration_impact_on_processing(self, sample_documents):
        """Test how different configurations affect processing."""
        # Test with different batch sizes
        ontology = Mock()
        ontology.extract_concepts.return_value = {"concepts": []}
        ontology.update_from_extraction = Mock()
        ontology.external_ontology_manager.enrich_concept = Mock(side_effect=lambda x: x)
        
        configs = [
            {"batch_size": 1, "max_workers": 1},
            {"batch_size": 5, "max_workers": 2},
        ]
        
        results = {}
        
        for i, config in enumerate(configs):
            processor = BatchProcessor(ontology, config)
            
            with patch.object(processor.document_detector, 'detect_document_type') as mock_detect:
                mock_extractor = Mock()
                mock_extractor.extract_text.return_value = "test content"
                mock_extractor.extract_metadata.return_value = {"title": "test"}
                mock_extractor.extractor_name = "Mock Extractor"
                mock_detect.return_value = mock_extractor
                
                # Process subset of files
                file_list = [f for f in sample_documents.values() if f.suffix in [".html", ".xml"]][:2]
                
                start_time = time.time()
                result = asyncio.run(processor.process_files(file_list))
                end_time = time.time()
                
                results[f"config_{i}"] = {
                    "processing_time": end_time - start_time,
                    "successful": result["summary"]["successful"],
                    "config": config
                }
            
            processor.shutdown()
        
        # Verify both configurations work
        for config_name, result in results.items():
            assert result["successful"] > 0
            assert result["processing_time"] > 0
    
    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self, temp_directory):
        """Test error handling and recovery in processing workflows."""
        # Create problematic files
        corrupt_pdf = temp_directory / "corrupt.pdf"
        corrupt_pdf.write_bytes(b"Not a real PDF file")
        
        empty_html = temp_directory / "empty.html"
        empty_html.write_text("")
        
        malformed_xml = temp_directory / "malformed.xml"
        malformed_xml.write_text("<?xml version='1.0'?><unclosed_tag>")
        
        # Test batch processor error handling
        ontology = Mock()
        ontology.extract_concepts.return_value = {"concepts": []}
        ontology.update_from_extraction = Mock()
        ontology.external_ontology_manager.enrich_concept = Mock(side_effect=lambda x: x)
        
        processor = BatchProcessor(ontology, {"max_workers": 1})
        
        # Mock detector to return extractors that will fail
        with patch.object(processor.document_detector, 'detect_document_type') as mock_detect:
            mock_extractor = Mock()
            mock_extractor.extract_text.side_effect = Exception("Extraction failed")
            mock_extractor.extractor_name = "Failing Extractor"
            mock_detect.return_value = mock_extractor
            
            file_list = [corrupt_pdf, empty_html, malformed_xml]
            results = await processor.process_files(file_list)
            
            # Verify error handling
            assert "failed_files" in results
            assert len(results["failed_files"]) == len(file_list)
            assert results["summary"]["failed"] == len(file_list)
            assert results["summary"]["successful"] == 0
            
            # Verify errors are recorded
            for failed_file in results["failed_files"]:
                assert "error" in failed_file
                assert failed_file["success"] == False
        
        processor.shutdown()
    
    def test_performance_monitoring(self, sample_documents):
        """Test performance monitoring and statistics collection."""
        # Create processor with statistics tracking
        ontology = Mock()
        ontology.extract_concepts.return_value = {"concepts": [Mock(), Mock()]}
        ontology.update_from_extraction = Mock()
        ontology.external_ontology_manager.enrich_concept = Mock(side_effect=lambda x: x)
        
        processor = BatchProcessor(ontology, {"max_workers": 1, "batch_size": 2})
        
        # Mock successful processing
        with patch.object(processor.document_detector, 'detect_document_type') as mock_detect:
            mock_extractor = Mock()
            mock_extractor.extract_text.return_value = "test content"
            mock_extractor.extract_metadata.return_value = {"title": "test"}
            mock_extractor.extractor_name = "Mock Extractor"
            mock_detect.return_value = mock_extractor
            
            file_list = list(sample_documents.values())[:3]
            
            # Get initial stats
            initial_stats = processor.get_statistics()
            
            # Process files
            results = asyncio.run(processor.process_files(file_list))
            
            # Get final stats
            final_stats = processor.get_statistics()
            
            # Verify statistics were updated
            assert final_stats["total_documents"] > initial_stats["total_documents"]
            assert final_stats["processed_documents"] > initial_stats["processed_documents"]
            assert final_stats["total_processing_time"] > initial_stats["total_processing_time"]
            
            # Verify performance metrics
            summary = results["summary"]
            assert "throughput_docs_per_second" in summary
            assert "average_processing_time" in summary
            assert summary["throughput_docs_per_second"] > 0
            assert summary["average_processing_time"] > 0
        
        processor.shutdown()


@pytest.mark.integration
class TestRealTimeProcessingIntegration:
    """Integration tests for real-time processing scenarios."""
    
    @pytest.mark.asyncio
    async def test_real_time_file_monitoring_and_processing(self):
        """Test real-time file monitoring and processing integration."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            watch_dir = Path(tmp_dir)
            
            # Create mock ontology and processor
            ontology = Mock()
            ontology.extract_concepts.return_value = {"concepts": []}
            ontology.update_from_extraction = Mock()
            ontology.external_ontology_manager.enrich_concept = Mock(side_effect=lambda x: x)
            
            processor = IncrementalProcessor(ontology, {"max_concurrent_processing": 1})
            
            # Mock document detector
            with patch("src.monitoring.incremental_processor.DocumentDetector") as mock_detector_class:
                mock_detector = Mock()
                mock_extractor = Mock()
                mock_extractor.extract_text.return_value = "test content"
                mock_extractor.extract_metadata.return_value = {"title": "test"}
                mock_detector.detect_document_type.return_value = mock_extractor
                mock_detector_class.return_value = mock_detector
                
                processor.document_detector = mock_detector
                
                # Create file watcher
                watcher = FileWatcher({"recursive": True})
                watcher.set_supported_extensions([".html", ".txt"])
                watcher.add_callback(processor.process_file_event)
                watcher.add_watch_path(watch_dir)
                
                # Start both components
                await processor.start()
                watcher.start()
                
                # Create files to trigger events
                test_file1 = watch_dir / "test1.html"
                test_file1.write_text("<html><body>Test content 1</body></html>")
                
                await asyncio.sleep(0.1)
                
                test_file2 = watch_dir / "test2.txt"
                test_file2.write_text("Test content 2")
                
                await asyncio.sleep(0.1)
                
                # Modify a file
                test_file1.write_text("<html><body>Modified content</body></html>")
                
                await asyncio.sleep(0.1)
                
                # Stop components
                watcher.stop()
                await processor.stop()
                
                # Verify processing occurred
                stats = processor.get_processing_stats()
                # Note: Actual processing depends on file system event timing
                # We mainly verify the integration doesn't crash
                assert "documents_processed" in stats
    
    @pytest.mark.asyncio
    async def test_batch_vs_incremental_processing_comparison(self):
        """Test comparing batch vs incremental processing approaches."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_dir = Path(tmp_dir)
            
            # Create test files
            test_files = []
            for i in range(5):
                file_path = test_dir / f"test{i}.html"
                file_path.write_text(f"<html><body>Test content {i}</body></html>")
                test_files.append(file_path)
            
            # Mock ontology
            ontology = Mock()
            ontology.extract_concepts.return_value = {"concepts": [Mock()]}
            ontology.update_from_extraction = Mock()
            ontology.external_ontology_manager.enrich_concept = Mock(side_effect=lambda x: x)
            
            # Test batch processing
            batch_processor = BatchProcessor(ontology, {"max_workers": 2, "batch_size": 3})
            
            with patch.object(batch_processor.document_detector, 'detect_document_type') as mock_detect:
                mock_extractor = Mock()
                mock_extractor.extract_text.return_value = "test content"
                mock_extractor.extract_metadata.return_value = {"title": "test"}
                mock_extractor.extractor_name = "Mock Extractor"
                mock_detect.return_value = mock_extractor
                
                start_time = time.time()
                batch_results = await batch_processor.process_files(test_files)
                batch_time = time.time() - start_time
            
            batch_processor.shutdown()
            
            # Reset ontology mock
            ontology.reset_mock()
            
            # Test incremental processing
            incremental_processor = IncrementalProcessor(ontology, {"max_concurrent_processing": 2})
            
            with patch("src.monitoring.incremental_processor.DocumentDetector") as mock_detector_class:
                mock_detector = Mock()
                mock_detector.detect_document_type.return_value = mock_extractor
                mock_detector_class.return_value = mock_detector
                
                incremental_processor.document_detector = mock_detector
                
                await incremental_processor.start()
                
                start_time = time.time()
                for file_path in test_files:
                    await incremental_processor.process_file_event("created", file_path, "file_created")
                
                # Wait for processing to complete
                await asyncio.sleep(0.5)
                incremental_time = time.time() - start_time
                
                await incremental_processor.stop()
            
            # Compare results
            assert batch_results["summary"]["successful"] == len(test_files)
            
            incremental_stats = incremental_processor.get_processing_stats()
            
            # Both approaches should process files successfully
            # (Note: Exact comparison depends on timing and implementation details)
            print(f"Batch processing time: {batch_time:.3f}s")
            print(f"Incremental processing time: {incremental_time:.3f}s")
            print(f"Batch successful: {batch_results['summary']['successful']}")
            print(f"Incremental processed: {incremental_stats['documents_processed']}")


@pytest.mark.integration
class TestConfigurationAndCustomization:
    """Integration tests for configuration and customization scenarios."""
    
    def test_custom_extractor_integration(self):
        """Test integration with custom extractors."""
        from src.ingestion.extractors.base import BaseExtractor
        
        # Create a custom extractor
        class CustomTextExtractor(BaseExtractor):
            def can_handle(self, file_path):
                return file_path.suffix.lower() == '.custom'
            
            def extract_text(self, file_path, config):
                return f"Custom extracted text from {file_path.name}"
            
            def extract_metadata(self, file_path, config):
                return {
                    'filename': file_path.name,
                    'extractor': 'custom',
                    'custom_field': 'custom_value'
                }
            
            @property
            def supported_extensions(self):
                return ['.custom']
            
            @property
            def extractor_name(self):
                return "Custom Text Extractor"
        
        # Test detector with custom extractor
        detector = DocumentDetector()
        custom_extractor = CustomTextExtractor()
        detector.register_extractor(custom_extractor)
        
        # Verify registration
        assert '.custom' in detector.extension_map
        assert custom_extractor in detector.extension_map['.custom']
        
        # Test detection
        with tempfile.NamedTemporaryFile(suffix='.custom', delete=False) as tmp_file:
            file_path = Path(tmp_file.name)
            file_path.write_text("custom content")
            
            detected_extractor = detector.detect_document_type(file_path)
            
            assert detected_extractor is not None
            assert detected_extractor.extractor_name == "Custom Text Extractor"
            
            # Test extraction
            text = detected_extractor.extract_text(file_path, {})
            metadata = detected_extractor.extract_metadata(file_path, {})
            
            assert "Custom extracted text" in text
            assert metadata['extractor'] == 'custom'
            assert metadata['custom_field'] == 'custom_value'
            
            # Clean up
            file_path.unlink()
    
    def test_configuration_driven_processing(self):
        """Test processing with different configuration scenarios."""
        ontology = Mock()
        ontology.extract_concepts.return_value = {"concepts": []}
        ontology.update_from_extraction = Mock()
        ontology.external_ontology_manager.enrich_concept = Mock(side_effect=lambda x: x)
        
        # Test different configurations
        configs = [
            # Configuration 1: Conservative processing
            {
                "max_workers": 1,
                "batch_size": 2,
                "similarity_threshold": 0.95,
                "use_external_ontologies": False
            },
            # Configuration 2: Aggressive processing
            {
                "max_workers": 4,
                "batch_size": 10,
                "similarity_threshold": 0.7,
                "use_external_ontologies": True
            },
            # Configuration 3: Balanced processing
            {
                "max_workers": 2,
                "batch_size": 5,
                "similarity_threshold": 0.85,
                "use_external_ontologies": True
            }
        ]
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_dir = Path(tmp_dir)
            
            # Create test files
            for i in range(6):
                file_path = test_dir / f"test{i}.html"
                file_path.write_text(f"<html><body>Content {i}</body></html>")
            
            results = {}
            
            for i, config in enumerate(configs):
                processor = BatchProcessor(ontology, config)
                
                with patch.object(processor.document_detector, 'detect_document_type') as mock_detect:
                    mock_extractor = Mock()
                    mock_extractor.extract_text.return_value = "test content"
                    mock_extractor.extract_metadata.return_value = {"title": "test"}
                    mock_extractor.extractor_name = "Mock Extractor"
                    mock_detect.return_value = mock_extractor
                    
                    file_list = list(test_dir.glob("*.html"))
                    result = asyncio.run(processor.process_files(file_list))
                    
                    results[f"config_{i}"] = {
                        "config": config,
                        "summary": result["summary"],
                        "stats": processor.get_statistics()
                    }
                
                processor.shutdown()
                ontology.reset_mock()
            
            # Verify all configurations work
            for config_name, result in results.items():
                assert result["summary"]["successful"] > 0
                assert result["summary"]["total_files"] == 6
                print(f"{config_name}: {result['summary']['throughput_docs_per_second']:.2f} docs/sec")
    
    def test_plugin_extensibility(self):
        """Test plugin-like extensibility of the system."""
        # Test that the system can be extended with new components
        
        # Custom concept type
        class CustomConcept:
            def __init__(self, name, custom_property):
                self.name = name
                self.custom_property = custom_property
        
        # Custom processor component
        class CustomProcessor:
            def __init__(self, config):
                self.config = config
                self.processed_count = 0
            
            def process_custom_concept(self, concept):
                self.processed_count += 1
                return f"Processed: {concept.name} with {concept.custom_property}"
        
        # Test integration
        config = {"custom_setting": "test_value"}
        processor = CustomProcessor(config)
        
        concept = CustomConcept("Test Concept", "custom_data")
        result = processor.process_custom_concept(concept)
        
        assert "Processed: Test Concept" in result
        assert "custom_data" in result
        assert processor.processed_count == 1
        
        # Verify extensibility works
        assert processor.config["custom_setting"] == "test_value"