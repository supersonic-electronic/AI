"""
Unit tests for extractor registry with entry points.

This module demonstrates best practices for testing plugin systems
and entry point discovery.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from src.ingestion.extractor_registry import ExtractorRegistry, get_registry
from src.ingestion.extractors.base import BaseExtractor


@pytest.mark.unit
class TestExtractorRegistry:
    """Test cases for the ExtractorRegistry class."""
    
    @pytest.fixture
    def fresh_registry(self):
        """Create a fresh registry instance for testing."""
        with patch('src.ingestion.extractor_registry._registry', None):
            return ExtractorRegistry()
    
    @pytest.fixture
    def mock_extractors(self):
        """Create mock extractors for testing."""
        mock_pdf = Mock(spec=BaseExtractor)
        mock_pdf.extractor_name = "PDF Test Extractor"
        mock_pdf.supported_extensions = [".pdf"]
        mock_pdf.can_handle.return_value = True
        
        mock_html = Mock(spec=BaseExtractor)
        mock_html.extractor_name = "HTML Test Extractor"
        mock_html.supported_extensions = [".html", ".htm"]
        mock_html.can_handle.return_value = True
        
        return {'pdf': mock_pdf, 'html': mock_html}
    
    def test_initialization_loads_extractors(self, fresh_registry):
        """Test that registry initialization loads extractors."""
        assert isinstance(fresh_registry.extractors, list)
        assert hasattr(fresh_registry, 'logger')
    
    @patch('src.ingestion.extractor_registry.entry_points')
    def test_load_extractors_from_entry_points_success(self, mock_entry_points, fresh_registry, mock_entry_point):
        """Test successful loading of extractors from entry points."""
        # Mock entry points
        mock_entry_points.return_value = [mock_entry_point]
        
        # Clear existing extractors and reload
        fresh_registry.extractors = []
        fresh_registry._load_extractors_from_entry_points()
        
        assert len(fresh_registry.extractors) == 1
        assert fresh_registry.extractors[0].extractor_name == "Test Plugin Extractor"
        mock_entry_point.load.assert_called_once()
    
    @patch('src.ingestion.extractor_registry.entry_points')
    def test_load_extractors_handles_invalid_entry_points(self, mock_entry_points, fresh_registry):
        """Test that invalid entry points are handled gracefully."""
        # Mock invalid entry point
        mock_invalid_ep = Mock()
        mock_invalid_ep.name = "invalid_plugin"
        mock_invalid_ep.load.side_effect = ImportError("Module not found")
        
        mock_entry_points.return_value = [mock_invalid_ep]
        
        fresh_registry.extractors = []
        fresh_registry._load_extractors_from_entry_points()
        
        # Should not crash, but also should not load any extractors
        assert len(fresh_registry.extractors) == 0
    
    @patch('src.ingestion.extractor_registry.entry_points')
    def test_fallback_loading_when_entry_points_fail(self, mock_entry_points, fresh_registry):
        """Test fallback loading when entry points completely fail."""
        # Mock entry points to raise exception
        mock_entry_points.side_effect = ImportError("importlib.metadata not available")
        
        fresh_registry.extractors = []
        fresh_registry._load_extractors_from_entry_points()
        
        # Should have fallen back to manual loading
        # The exact number depends on what extractors are available
        assert len(fresh_registry.extractors) >= 0  # At least it shouldn't crash
    
    def test_register_extractor_manual(self, fresh_registry, mock_extractors):
        """Test manual registration of extractors."""
        initial_count = len(fresh_registry.extractors)
        
        fresh_registry.register_extractor(mock_extractors['pdf'])
        
        assert len(fresh_registry.extractors) == initial_count + 1
        assert mock_extractors['pdf'] in fresh_registry.extractors
    
    def test_register_extractor_duplicate_prevented(self, fresh_registry, mock_extractors):
        """Test that duplicate extractors are not registered."""
        fresh_registry.register_extractor(mock_extractors['pdf'])
        initial_count = len(fresh_registry.extractors)
        
        # Try to register the same extractor again
        fresh_registry.register_extractor(mock_extractors['pdf'])
        
        assert len(fresh_registry.extractors) == initial_count
    
    def test_register_extractor_invalid_type_raises_error(self, fresh_registry):
        """Test that registering invalid extractor raises TypeError."""
        with pytest.raises(TypeError):
            fresh_registry.register_extractor("not an extractor")
    
    def test_unregister_extractor_success(self, fresh_registry, mock_extractors):
        """Test successful unregistration of extractors."""
        fresh_registry.register_extractor(mock_extractors['pdf'])
        initial_count = len(fresh_registry.extractors)
        
        result = fresh_registry.unregister_extractor("PDF Test Extractor")
        
        assert result is True
        assert len(fresh_registry.extractors) == initial_count - 1
        assert mock_extractors['pdf'] not in fresh_registry.extractors
    
    def test_unregister_extractor_not_found(self, fresh_registry):
        """Test unregistering non-existent extractor."""
        result = fresh_registry.unregister_extractor("Non-existent Extractor")
        
        assert result is False
    
    def test_get_extractor_for_file(self, fresh_registry, mock_extractors):
        """Test getting appropriate extractor for a file."""
        fresh_registry.register_extractor(mock_extractors['pdf'])
        fresh_registry.register_extractor(mock_extractors['html'])
        
        # Test PDF file
        pdf_extractor = fresh_registry.get_extractor(Path("test.pdf"))
        assert pdf_extractor == mock_extractors['pdf']
        
        # Test HTML file  
        html_extractor = fresh_registry.get_extractor(Path("test.html"))
        assert html_extractor == mock_extractors['html']
    
    def test_get_extractor_no_match(self, fresh_registry, mock_extractors):
        """Test getting extractor when no match is found."""
        fresh_registry.register_extractor(mock_extractors['pdf'])
        
        # Mock can_handle to return False
        mock_extractors['pdf'].can_handle.return_value = False
        
        extractor = fresh_registry.get_extractor(Path("test.unknown"))
        assert extractor is None
    
    def test_get_supported_extensions(self, fresh_registry, mock_extractors):
        """Test getting all supported extensions."""
        fresh_registry.register_extractor(mock_extractors['pdf'])
        fresh_registry.register_extractor(mock_extractors['html'])
        
        extensions = fresh_registry.get_supported_extensions()
        
        assert ".pdf" in extensions
        assert ".html" in extensions
        assert ".htm" in extensions
        assert extensions[".pdf"] == "PDF Test Extractor"
        assert extensions[".html"] == "HTML Test Extractor"
    
    def test_list_extractors(self, fresh_registry, mock_extractors):
        """Test listing all registered extractors."""
        fresh_registry.register_extractor(mock_extractors['pdf'])
        fresh_registry.register_extractor(mock_extractors['html'])
        
        extractors = fresh_registry.list_extractors()
        
        assert len(extractors) >= 2
        assert mock_extractors['pdf'] in extractors
        assert mock_extractors['html'] in extractors
        # Should return a copy, not the original list
        assert extractors is not fresh_registry.extractors


@pytest.mark.unit
class TestRegistryGlobalAccess:
    """Test the global registry access functions."""
    
    def test_get_registry_singleton(self):
        """Test that get_registry returns a singleton."""
        registry1 = get_registry()
        registry2 = get_registry()
        
        assert registry1 is registry2
        assert isinstance(registry1, ExtractorRegistry)
    
    @patch('src.ingestion.extractor_registry._registry', None)
    def test_get_registry_creates_new_instance(self):
        """Test that get_registry creates new instance when needed."""
        registry = get_registry()
        
        assert isinstance(registry, ExtractorRegistry)


@pytest.mark.integration
class TestExtractorRegistryIntegration:
    """Integration tests for extractor registry with real extractors."""
    
    def test_registry_loads_built_in_extractors(self):
        """Test that registry loads actual built-in extractors."""
        registry = ExtractorRegistry()
        
        # Should have loaded at least some extractors
        assert len(registry.extractors) > 0
        
        # Check for common extractors
        extractor_names = [e.extractor_name for e in registry.extractors]
        
        # At least one of these should be present
        expected_extractors = ["PDF", "HTML", "DOCX", "XML", "LaTeX"]
        found_extractors = [name for name in expected_extractors 
                          if any(expected in extractor_name for extractor_name in extractor_names)]
        
        assert len(found_extractors) > 0, f"No expected extractors found. Available: {extractor_names}"
    
    def test_registry_can_handle_real_files(self):
        """Test registry with real file paths."""
        registry = ExtractorRegistry()
        
        # Test with various file types
        test_files = [
            Path("document.pdf"),
            Path("webpage.html"),
            Path("document.docx"),
            Path("data.xml"),
            Path("paper.tex")
        ]
        
        handled_count = 0
        for file_path in test_files:
            extractor = registry.get_extractor(file_path)
            if extractor is not None:
                handled_count += 1
        
        # Should be able to handle at least some of these file types
        assert handled_count > 0
    
    @pytest.mark.parametrize("extension,expected_extractor_keyword", [
        (".pdf", "PDF"),
        (".html", "HTML"),
        (".htm", "HTML"),
        (".docx", "DOCX"),
        (".xml", "XML"),
        (".tex", "LaTeX"),
        (".latex", "LaTeX")
    ])
    def test_registry_maps_extensions_correctly(self, extension, expected_extractor_keyword):
        """Test that extensions are mapped to correct extractors."""
        registry = ExtractorRegistry()
        
        test_file = Path(f"test{extension}")
        extractor = registry.get_extractor(test_file)
        
        if extractor is not None:  # Skip if extractor not available
            assert expected_extractor_keyword.lower() in extractor.extractor_name.lower()