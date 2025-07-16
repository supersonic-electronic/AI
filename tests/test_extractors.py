"""
Unit tests for document extractors.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

from src.ingestion.extractors.html import HTMLExtractor
from src.ingestion.extractors.docx import DOCXExtractor
from src.ingestion.extractors.xml import XMLExtractor
from src.ingestion.extractors.latex import LaTeXExtractor
from src.ingestion.extractors.document_detector import DocumentDetector


class TestHTMLExtractor:
    """Test cases for HTML extractor."""
    
    def test_can_handle_html_files(self):
        """Test that HTMLExtractor can handle HTML files."""
        extractor = HTMLExtractor()
        
        assert extractor.can_handle(Path("test.html"))
        assert extractor.can_handle(Path("test.htm"))
        assert not extractor.can_handle(Path("test.pdf"))
        assert not extractor.can_handle(Path("test.txt"))
    
    def test_supported_extensions(self):
        """Test supported extensions property."""
        extractor = HTMLExtractor()
        extensions = extractor.supported_extensions
        
        assert ".html" in extensions
        assert ".htm" in extensions
        assert len(extensions) == 2
    
    def test_extractor_name(self):
        """Test extractor name property."""
        extractor = HTMLExtractor()
        assert "HTML" in extractor.extractor_name
        assert "BeautifulSoup" in extractor.extractor_name
    
    @patch("builtins.open", new_callable=mock_open, read_data="<html><body><h1>Test</h1><p>Content</p></body></html>")
    @patch("src.ingestion.extractors.html.BeautifulSoup")
    def test_extract_text_basic(self, mock_bs, mock_file):
        """Test basic text extraction from HTML."""
        mock_soup = Mock()
        mock_soup.get_text.return_value = "Test Content"
        mock_bs.return_value = mock_soup
        
        extractor = HTMLExtractor()
        config = {}
        
        text = extractor.extract_text(Path("test.html"), config)
        
        assert text == "Test Content"
        mock_file.assert_called_once()
    
    @patch("builtins.open", new_callable=mock_open, read_data="<html><head><title>Test Title</title></head></html>")
    @patch("src.ingestion.extractors.html.BeautifulSoup")
    def test_extract_metadata_basic(self, mock_bs, mock_file):
        """Test basic metadata extraction from HTML."""
        mock_soup = Mock()
        mock_title = Mock()
        mock_title.get_text.return_value = "Test Title"
        mock_soup.find.return_value = mock_title
        mock_soup.find_all.return_value = []
        
        extractor = HTMLExtractor()
        extractor.soup = mock_soup
        config = {}
        
        metadata = extractor.extract_metadata(Path("test.html"), config)
        
        assert "filename" in metadata
        assert metadata["filename"] == "test.html"


class TestDOCXExtractor:
    """Test cases for DOCX extractor."""
    
    def test_can_handle_docx_files(self):
        """Test that DOCXExtractor can handle DOCX files."""
        extractor = DOCXExtractor()
        
        assert extractor.can_handle(Path("test.docx"))
        assert not extractor.can_handle(Path("test.doc"))
        assert not extractor.can_handle(Path("test.pdf"))
    
    def test_supported_extensions(self):
        """Test supported extensions property."""
        extractor = DOCXExtractor()
        extensions = extractor.supported_extensions
        
        assert ".docx" in extensions
        assert len(extensions) == 1
    
    def test_extractor_name(self):
        """Test extractor name property."""
        extractor = DOCXExtractor()
        assert "DOCX" in extractor.extractor_name
        assert "python-docx" in extractor.extractor_name
    
    @patch("src.ingestion.extractors.docx.Document")
    def test_extract_text_basic(self, mock_document_class):
        """Test basic text extraction from DOCX."""
        mock_doc = Mock()
        mock_paragraph = Mock()
        mock_paragraph.text = "Test paragraph"
        mock_doc.paragraphs = [mock_paragraph]
        mock_doc.tables = []
        mock_document_class.return_value = mock_doc
        
        extractor = DOCXExtractor()
        config = {}
        
        text = extractor.extract_text(Path("test.docx"), config)
        
        assert "Test paragraph" in text
    
    @patch("src.ingestion.extractors.docx.Document")
    def test_extract_metadata_basic(self, mock_document_class):
        """Test basic metadata extraction from DOCX."""
        mock_doc = Mock()
        mock_props = Mock()
        mock_props.title = "Test Title"
        mock_props.author = "Test Author"
        mock_doc.core_properties = mock_props
        mock_doc.paragraphs = []
        mock_doc.tables = []
        mock_doc.sections = []
        mock_document_class.return_value = mock_doc
        
        extractor = DOCXExtractor()
        config = {}
        
        metadata = extractor.extract_metadata(Path("test.docx"), config)
        
        assert metadata["title"] == "Test Title"
        assert metadata["author"] == "Test Author"


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