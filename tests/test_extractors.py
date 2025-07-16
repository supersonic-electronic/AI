"""
Unit tests for document extractors.

This module tests all document extractors using fixtures and parametrized tests
following pytest best practices.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

from src.ingestion.extractors.html import HTMLExtractor
from src.ingestion.extractors.docx import DOCXExtractor
from src.ingestion.extractors.xml import XMLExtractor
from src.ingestion.extractors.latex import LaTeXExtractor
from src.ingestion.extractors.document_detector import DocumentDetector
from src.ingestion.extractors.base import BaseExtractor


@pytest.mark.unit
class TestExtractorBase:
    """Test base extractor functionality shared across all extractors."""
    
    @pytest.mark.parametrize("extractor_name,expected_extensions", [
        ("html", [".html", ".htm"]),
        ("docx", [".docx"]),
        ("xml", [".xml"]),
        ("latex", [".tex", ".latex"])
    ])
    def test_supported_extensions(self, sample_extractors, extractor_name, expected_extensions):
        """Test that extractors report correct supported extensions."""
        extractor = sample_extractors[extractor_name]
        extensions = extractor.supported_extensions
        
        for ext in expected_extensions:
            assert ext in extensions
        assert len(extensions) == len(expected_extensions)
    
    @pytest.mark.parametrize("extractor_name", ["html", "docx", "xml", "latex"])
    def test_extractor_name_property(self, sample_extractors, extractor_name):
        """Test that all extractors have a valid name property."""
        extractor = sample_extractors[extractor_name]
        name = extractor.extractor_name
        
        assert isinstance(name, str)
        assert len(name) > 0
        assert extractor_name.upper() in name.upper()
    
    @pytest.mark.parametrize("extractor_name", ["html", "docx", "xml", "latex"])
    def test_extractor_inheritance(self, sample_extractors, extractor_name):
        """Test that all extractors inherit from BaseExtractor."""
        extractor = sample_extractors[extractor_name]
        assert isinstance(extractor, BaseExtractor)


@pytest.mark.unit
class TestHTMLExtractor:
    """Test cases for HTML extractor."""
    
    @pytest.fixture
    def html_extractor(self):
        """Create HTML extractor instance."""
        return HTMLExtractor()
    
    def test_can_handle_html_files(self, html_extractor, sample_file_paths):
        """Test that HTMLExtractor can handle HTML files."""
        assert html_extractor.can_handle(sample_file_paths['html'])
        assert html_extractor.can_handle(sample_file_paths['htm'])
        assert not html_extractor.can_handle(sample_file_paths['pdf'])
        assert not html_extractor.can_handle(sample_file_paths['unknown'])
    
    def test_extractor_name(self, html_extractor):
        """Test extractor name property."""
        assert "HTML" in html_extractor.extractor_name
        assert "BeautifulSoup" in html_extractor.extractor_name
    
    def test_extract_text_basic(self, html_extractor, mock_html_content):
        """Test basic text extraction from HTML."""
        with patch("builtins.open", mock_open(read_data=mock_html_content)):
            with patch("src.ingestion.extractors.html.BeautifulSoup") as mock_bs:
                mock_soup = Mock()
                mock_soup.get_text.return_value = "Test Document Main Title This is a paragraph with some content. E(R) = w'μ Footer content"
                mock_bs.return_value = mock_soup
                
                text = html_extractor.extract_text(Path("test.html"), {})
                
                assert "Test Document" in text
                assert "Main Title" in text
                assert "E(R) = w'μ" in text
    
    def test_extract_metadata_basic(self, html_extractor, mock_html_content):
        """Test basic metadata extraction from HTML."""
        with patch("builtins.open", mock_open(read_data=mock_html_content)):
            with patch("src.ingestion.extractors.html.BeautifulSoup") as mock_bs:
                mock_soup = Mock()
                
                # Mock title element
                mock_title = Mock()
                mock_title.get_text.return_value = "Test Document"
                mock_soup.find.return_value = mock_title
                
                # Mock meta elements
                mock_meta_author = Mock()
                mock_meta_author.get.return_value = "Test Author"
                mock_meta_desc = Mock()
                mock_meta_desc.get.return_value = "Test Description"
                mock_soup.find_all.return_value = [mock_meta_author, mock_meta_desc]
                
                mock_bs.return_value = mock_soup
                html_extractor.soup = mock_soup
                
                metadata = html_extractor.extract_metadata(Path("test.html"), {})
                
                assert metadata["filename"] == "test.html"


@pytest.mark.unit
class TestDOCXExtractor:
    """Test cases for DOCX extractor."""
    
    @pytest.fixture
    def docx_extractor(self):
        """Create DOCX extractor instance."""
        return DOCXExtractor()
    
    def test_can_handle_docx_files(self, docx_extractor, sample_file_paths):
        """Test that DOCXExtractor can handle DOCX files."""
        assert docx_extractor.can_handle(sample_file_paths['docx'])
        assert not docx_extractor.can_handle(sample_file_paths['pdf'])
        assert not docx_extractor.can_handle(sample_file_paths['html'])
    
    def test_extractor_name(self, docx_extractor):
        """Test extractor name property."""
        assert "DOCX" in docx_extractor.extractor_name
        assert "python-docx" in docx_extractor.extractor_name
    
    def test_extract_text_basic(self, docx_extractor, mock_docx_content):
        """Test basic text extraction from DOCX."""
        with patch("src.ingestion.extractors.docx.Document") as mock_document_class:
            mock_document_class.return_value = mock_docx_content
            
            text = docx_extractor.extract_text(Path("test.docx"), {})
            
            assert "First paragraph content" in text
            assert "Second paragraph with formula: E(R) = w'μ" in text
            assert "Cell content" in text
    
    def test_extract_metadata_basic(self, docx_extractor, mock_docx_content):
        """Test basic metadata extraction from DOCX."""
        with patch("src.ingestion.extractors.docx.Document") as mock_document_class:
            mock_document_class.return_value = mock_docx_content
            docx_extractor.doc = mock_docx_content
            
            metadata = docx_extractor.extract_metadata(Path("test.docx"), {})
            
            assert metadata["title"] == "Test Document"
            assert metadata["author"] == "Test Author"
            assert metadata["subject"] == "Test Subject"
            assert metadata["keywords"] == "test, keywords"


class TestXMLExtractor:
    """Test cases for XML extractor."""
    
    def test_can_handle_xml_files(self):
        """Test that XMLExtractor can handle XML files."""
        extractor = XMLExtractor()
        
        assert extractor.can_handle(Path("test.xml"))
        assert not extractor.can_handle(Path("test.html"))
        assert not extractor.can_handle(Path("test.pdf"))
    
    def test_supported_extensions(self):
        """Test supported extensions property."""
        extractor = XMLExtractor()
        extensions = extractor.supported_extensions
        
        assert ".xml" in extensions
        assert len(extensions) == 1
    
    def test_extractor_name(self):
        """Test extractor name property."""
        extractor = XMLExtractor()
        assert "XML" in extractor.extractor_name
        assert "lxml" in extractor.extractor_name
    
    @patch("builtins.open", new_callable=mock_open, read_data="<?xml version='1.0'?><root><element>Test</element></root>")
    @patch("src.ingestion.extractors.xml.etree")
    def test_extract_text_basic(self, mock_etree, mock_file):
        """Test basic text extraction from XML."""
        mock_root = Mock()
        mock_root.itertext.return_value = ["Test"]
        mock_tree = Mock()
        mock_tree.getroot.return_value = mock_root
        mock_etree.parse.return_value = mock_tree
        
        extractor = XMLExtractor()
        config = {}
        
        text = extractor.extract_text(Path("test.xml"), config)
        
        assert "Test" in text
    
    @patch("builtins.open", new_callable=mock_open, read_data="<?xml version='1.0'?><root><title>Test Title</title></root>")
    @patch("src.ingestion.extractors.xml.etree")
    def test_extract_metadata_basic(self, mock_etree, mock_file):
        """Test basic metadata extraction from XML."""
        mock_root = Mock()
        mock_root.tag = "root"
        mock_tree = Mock()
        mock_tree.getroot.return_value = mock_root
        mock_tree.docinfo = Mock()
        mock_tree.docinfo.encoding = "utf-8"
        mock_etree.parse.return_value = mock_tree
        
        extractor = XMLExtractor()
        extractor.root = mock_root
        extractor.tree = mock_tree
        config = {}
        
        metadata = extractor.extract_metadata(Path("test.xml"), config)
        
        assert metadata["root_element"] == "root"
        assert metadata["encoding"] == "utf-8"


class TestLaTeXExtractor:
    """Test cases for LaTeX extractor."""
    
    def test_can_handle_latex_files(self):
        """Test that LaTeXExtractor can handle LaTeX files."""
        extractor = LaTeXExtractor()
        
        assert extractor.can_handle(Path("test.tex"))
        assert extractor.can_handle(Path("test.latex"))
        assert not extractor.can_handle(Path("test.pdf"))
        assert not extractor.can_handle(Path("test.txt"))
    
    def test_supported_extensions(self):
        """Test supported extensions property."""
        extractor = LaTeXExtractor()
        extensions = extractor.supported_extensions
        
        assert ".tex" in extensions
        assert ".latex" in extensions
        assert len(extensions) == 2
    
    def test_extractor_name(self):
        """Test extractor name property."""
        extractor = LaTeXExtractor()
        assert "LaTeX" in extractor.extractor_name
        assert "Regex" in extractor.extractor_name
    
    @patch("builtins.open", new_callable=mock_open, read_data="\\documentclass{article}\\title{Test}\\begin{document}Content\\end{document}")
    def test_extract_text_basic(self, mock_file):
        """Test basic text extraction from LaTeX."""
        extractor = LaTeXExtractor()
        config = {}
        
        text = extractor.extract_text(Path("test.tex"), config)
        
        assert "Content" in text
        assert "TITLE: Test" in text
    
    @patch("builtins.open", new_callable=mock_open, read_data="\\documentclass{article}\\title{Test Title}\\author{Test Author}\\begin{document}\\end{document}")
    def test_extract_metadata_basic(self, mock_file):
        """Test basic metadata extraction from LaTeX."""
        extractor = LaTeXExtractor()
        config = {}
        
        metadata = extractor.extract_metadata(Path("test.tex"), config)
        
        assert metadata["title"] == "Test Title"
        assert metadata["author"] == "Test Author"
        assert metadata["document_class"] == "article"


class TestDocumentDetector:
    """Test cases for document detector."""
    
    def test_initialization(self):
        """Test DocumentDetector initialization."""
        detector = DocumentDetector()
        
        assert len(detector.extractors) > 0
        assert len(detector.extension_map) > 0
        assert ".pdf" in detector.extension_map
        assert ".html" in detector.extension_map
        assert ".docx" in detector.extension_map
        assert ".xml" in detector.extension_map
        assert ".tex" in detector.extension_map
    
    def test_detect_by_extension(self):
        """Test detection by file extension."""
        detector = DocumentDetector()
        
        # Test PDF detection
        extractor = detector._detect_by_extension(Path("test.pdf"))
        assert extractor is not None
        assert "PDF" in extractor.extractor_name
        
        # Test HTML detection
        extractor = detector._detect_by_extension(Path("test.html"))
        assert extractor is not None
        assert "HTML" in extractor.extractor_name
        
        # Test unknown extension
        extractor = detector._detect_by_extension(Path("test.unknown"))
        assert extractor is None
    
    def test_get_supported_extensions(self):
        """Test getting supported extensions."""
        detector = DocumentDetector()
        extensions = detector.get_supported_extensions()
        
        assert ".pdf" in extensions
        assert ".html" in extensions
        assert ".htm" in extensions
        assert ".docx" in extensions
        assert ".xml" in extensions
        assert ".tex" in extensions
        assert ".latex" in extensions
    
    def test_get_extractor_for_extension(self):
        """Test getting extractors for specific extensions."""
        detector = DocumentDetector()
        
        extractors = detector.get_extractor_for_extension(".pdf")
        assert len(extractors) > 0
        assert "PDF" in extractors[0].extractor_name
        
        extractors = detector.get_extractor_for_extension("html")  # Without dot
        assert len(extractors) > 0
        assert "HTML" in extractors[0].extractor_name
        
        extractors = detector.get_extractor_for_extension(".unknown")
        assert len(extractors) == 0
    
    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.stat")
    def test_get_detection_info(self, mock_stat, mock_exists):
        """Test getting detection information."""
        mock_exists.return_value = True
        mock_stat.return_value = Mock(st_size=1000)
        
        detector = DocumentDetector()
        info = detector.get_detection_info(Path("test.pdf"))
        
        assert info["file_path"] == "test.pdf"
        assert info["extension"] == ".pdf"
        assert "detection_methods" in info
        assert "extension" in info["detection_methods"]
        assert "mime_type" in info["detection_methods"]
    
    def test_register_extractor(self):
        """Test registering a new extractor."""
        detector = DocumentDetector()
        initial_count = len(detector.extractors)
        
        # Create a mock extractor
        mock_extractor = Mock()
        mock_extractor.supported_extensions = [".test"]
        
        detector.register_extractor(mock_extractor)
        
        assert len(detector.extractors) == initial_count + 1
        assert ".test" in detector.extension_map
        assert mock_extractor in detector.extension_map[".test"]