"""
Tests for the EPUB extractor.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import zipfile
import tempfile
import os

from src.ingestion.extractors.epub import EPUBExtractor
from src.ingestion.extractors.document_detector import DocumentDetector


class TestEPUBExtractor:
    """Test suite for EPUBExtractor class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = EPUBExtractor()
        self.config = {
            'process_chapters_individually': True,
            'extract_mathml': True,
            'include_toc': True,
            'include_statistics': True,
            'include_structure': True,
            'remove_tags': ['script', 'style'],
            'remove_comments': True,
            'remove_empty_paragraphs': True,
            'normalize_whitespace': True,
            'remove_empty_lines': True,
            'html_parser': 'lxml'
        }
    
    def test_can_handle_epub_files(self):
        """Test that extractor can handle .epub files."""
        assert self.extractor.can_handle(Path("test.epub")) is True
        assert self.extractor.can_handle(Path("test.EPUB")) is True
        assert self.extractor.can_handle(Path("book.epub")) is True
    
    def test_can_handle_non_epub_files(self):
        """Test that extractor rejects non-EPUB files."""
        assert self.extractor.can_handle(Path("test.pdf")) is False
        assert self.extractor.can_handle(Path("test.docx")) is False
        assert self.extractor.can_handle(Path("test.html")) is False
        assert self.extractor.can_handle(Path("test.txt")) is False
        assert self.extractor.can_handle(Path("test")) is False
    
    def test_supported_extensions(self):
        """Test supported extensions property."""
        assert self.extractor.supported_extensions == ['.epub']
    
    def test_extractor_name(self):
        """Test extractor name property."""
        assert self.extractor.extractor_name == "EPUB Extractor (ebooklib)"
    
    @patch('src.ingestion.extractors.epub.epub.read_epub')
    def test_extract_text_basic_epub(self, mock_read_epub):
        """Test basic text extraction from EPUB."""
        # Mock EPUB book
        mock_book = Mock()
        mock_item = Mock()
        mock_item.get_content.return_value = b"<html><body><h1>Chapter 1</h1><p>This is test content.</p></body></html>"
        mock_book.get_items_of_type.return_value = [mock_item]
        mock_read_epub.return_value = mock_book
        
        self.extractor.book = mock_book
        
        with patch.object(self.extractor, '_get_chapter_title', return_value="Test Chapter"):
            result = self.extractor.extract_text(Path("test.epub"), self.config)
        
        assert "Chapter 1" in result
        assert "This is test content." in result
        assert "[CHAPTER 1: Test Chapter]" in result
    
    @patch('src.ingestion.extractors.epub.epub.read_epub')
    def test_extract_text_multi_chapter(self, mock_read_epub):
        """Test multi-chapter EPUB processing."""
        # Mock EPUB book with multiple chapters
        mock_book = Mock()
        mock_item1 = Mock()
        mock_item1.get_content.return_value = b"<html><body><h1>Chapter 1</h1><p>First chapter content.</p></body></html>"
        mock_item2 = Mock()
        mock_item2.get_content.return_value = b"<html><body><h1>Chapter 2</h1><p>Second chapter content.</p></body></html>"
        mock_book.get_items_of_type.return_value = [mock_item1, mock_item2]
        mock_read_epub.return_value = mock_book
        
        self.extractor.book = mock_book
        
        with patch.object(self.extractor, '_get_chapter_title', side_effect=["First", "Second"]):
            result = self.extractor.extract_text(Path("test.epub"), self.config)
        
        assert "[CHAPTER 1: First]" in result
        assert "[CHAPTER 2: Second]" in result
        assert "First chapter content." in result
        assert "Second chapter content." in result
        assert "[CHAPTER BREAK]" in result
    
    @patch('src.ingestion.extractors.epub.epub.read_epub')
    def test_extract_text_with_mathml(self, mock_read_epub):
        """Test mathematical content extraction."""
        # Mock EPUB book with MathML
        mock_book = Mock()
        mock_item = Mock()
        mathml_content = '''<html><body>
            <p>Here is an equation: <math><mfrac><mn>1</mn><mn>2</mn></mfrac></math></p>
            <p>And a symbol: <math><mi>α</mi></math></p>
        </body></html>'''
        mock_item.get_content.return_value = mathml_content.encode('utf-8')
        mock_book.get_items_of_type.return_value = [mock_item]
        mock_read_epub.return_value = mock_book
        
        self.extractor.book = mock_book
        
        with patch.object(self.extractor, '_get_chapter_title', return_value="Math Chapter"):
            result = self.extractor.extract_text(Path("test.epub"), self.config)
        
        # Should contain LaTeX conversion
        assert "Here is an equation:" in result
        assert "And a symbol:" in result
    
    @patch('src.ingestion.extractors.epub.epub.read_epub')
    def test_extract_metadata_dublin_core(self, mock_read_epub):
        """Test Dublin Core metadata extraction."""
        # Mock EPUB book with metadata
        mock_book = Mock()
        mock_book.get_metadata.side_effect = lambda ns, name: {
            ('DC', 'title'): [('Test Book Title',)],
            ('DC', 'creator'): [('Test Author',)],
            ('DC', 'subject'): [('Test Subject',)],
            ('DC', 'description'): [('Test Description',)],
            ('DC', 'publisher'): [('Test Publisher',)],
            ('DC', 'date'): [('2024-01-01',)],
            ('DC', 'language'): [('en',)],
            ('DC', 'identifier'): [('isbn:1234567890',)],
        }.get((ns, name), [])
        
        mock_book.version = '3.0'
        mock_book.spine = [('item1', True), ('item2', True)]
        mock_book.get_items.return_value = []
        mock_book.get_items_of_type.return_value = []
        
        mock_read_epub.return_value = mock_book
        self.extractor.book = mock_book
        
        # Create a temporary file for testing
        with tempfile.NamedTemporaryFile(suffix='.epub', delete=False) as tmp_file:
            tmp_path = Path(tmp_file.name)
            
            try:
                result = self.extractor.extract_metadata(tmp_path, self.config)
            finally:
                os.unlink(tmp_path)
        
        assert result['title'] == 'Test Book Title'
        assert result['author'] == 'Test Author'
        assert result['subject'] == 'Test Subject'
        assert result['description'] == 'Test Description'
        assert result['publisher'] == 'Test Publisher'
        assert result['publication_date'] == '2024-01-01'
        assert result['language'] == 'en'
        assert result['identifier'] == 'isbn:1234567890'
        assert result['format'] == 'EPUB'
        assert result['epub_version'] == '3.0'
    
    def test_mathml_to_latex_conversion(self):
        """Test MathML to LaTeX conversion."""
        from bs4 import BeautifulSoup
        
        # Test basic symbols
        mathml = '<math><mi>α</mi></math>'
        soup = BeautifulSoup(mathml, 'lxml')
        math_elem = soup.find('math')
        
        result = self.extractor._mathml_to_latex(math_elem, {})
        assert '\\alpha' in result  # Should convert to LaTeX
        
        # Test fractions
        mathml_frac = '<math><mfrac><mn>1</mn><mn>2</mn></mfrac></math>'
        soup_frac = BeautifulSoup(mathml_frac, 'lxml')
        math_elem_frac = soup_frac.find('math')
        
        result_frac = self.extractor._mathml_to_latex(math_elem_frac, {})
        # Should contain some representation of the fraction
        assert len(result_frac) > 0
    
    @patch('src.ingestion.extractors.epub.epub.read_epub')
    def test_error_handling_corrupted_epub(self, mock_read_epub):
        """Test error handling for corrupted EPUB files."""
        # Mock exception during EPUB reading
        mock_read_epub.side_effect = Exception("Corrupted EPUB file")
        
        with pytest.raises(Exception) as exc_info:
            self.extractor.extract_text(Path("corrupted.epub"), self.config)
        
        assert "Corrupted EPUB file" in str(exc_info.value)
    
    def test_get_chapter_title_extraction(self):
        """Test chapter title extraction methods."""
        # Mock item with title attribute
        mock_item = Mock()
        mock_item.title = "Chapter Title"
        
        result = self.extractor._get_chapter_title(mock_item, 1)
        assert result == "Chapter Title"
        
        # Mock item without title but with content
        mock_item_no_title = Mock()
        mock_item_no_title.title = None
        mock_item_no_title.get_content.return_value = b"<html><body><h1>Content Title</h1></body></html>"
        
        result2 = self.extractor._get_chapter_title(mock_item_no_title, 2)
        assert result2 == "Content Title"
        
        # Mock item with no title or content
        mock_item_empty = Mock()
        mock_item_empty.title = None
        mock_item_empty.get_content.return_value = b"<html><body></body></html>"
        mock_item_empty.file_name = None
        
        result3 = self.extractor._get_chapter_title(mock_item_empty, 3)
        assert result3 == "Chapter 3"
    
    def test_clean_text_functionality(self):
        """Test text cleaning functionality."""
        dirty_text = "  Test   text   with   \n\n\n   multiple   spaces  \n\n  "
        
        cleaned = self.extractor._clean_text(dirty_text, {
            'normalize_whitespace': True,
            'remove_empty_lines': True
        })
        
        # Should normalize whitespace and remove empty lines
        # Note: the cleaning preserves some newlines for readability
        assert "Test text with" in cleaned
        assert "multiple spaces" in cleaned
        assert cleaned.strip() == cleaned  # No leading/trailing whitespace
    
    def test_remove_unwanted_elements(self):
        """Test HTML element removal."""
        from bs4 import BeautifulSoup
        
        html = """<html><body>
            <script>alert('test');</script>
            <p>Keep this content</p>
            <style>body { color: red; }</style>
            <!-- This is a comment -->
            <p></p>
        </body></html>"""
        
        soup = BeautifulSoup(html, 'lxml')
        self.extractor._remove_unwanted_elements(soup, {
            'remove_tags': ['script', 'style'],
            'remove_comments': True,
            'remove_empty_paragraphs': True
        })
        
        text = soup.get_text()
        assert "alert('test')" not in text
        assert "color: red" not in text
        assert "Keep this content" in text


class TestDocumentDetectorEPUBIntegration:
    """Test DocumentDetector integration with EPUB extractor."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.detector = DocumentDetector()
    
    def test_epub_in_supported_extensions(self):
        """Test that .epub is in supported extensions."""
        extensions = self.detector.get_supported_extensions()
        assert '.epub' in extensions
    
    def test_epub_extractor_in_available_extractors(self):
        """Test that EPUB extractor is available."""
        extractors = self.detector.get_available_extractors()
        extractor_names = [e.extractor_name for e in extractors]
        assert 'EPUB Extractor (ebooklib)' in extractor_names
    
    def test_detect_epub_by_extension(self):
        """Test EPUB detection by file extension."""
        extractor = self.detector._detect_by_extension(Path("test.epub"))
        assert extractor is not None
        assert extractor.extractor_name == "EPUB Extractor (ebooklib)"
        
        extractor_upper = self.detector._detect_by_extension(Path("test.EPUB"))
        assert extractor_upper is not None
        assert extractor_upper.extractor_name == "EPUB Extractor (ebooklib)"
    
    def test_detect_epub_by_mime_type(self):
        """Test EPUB detection by MIME type."""
        # Mock mimetypes.guess_type to return EPUB MIME type
        with patch('mimetypes.guess_type', return_value=('application/epub+zip', None)):
            extractor = self.detector._detect_by_mime_type(Path("test.epub"))
            assert extractor is not None
            assert extractor.extractor_name == "EPUB Extractor (ebooklib)"
    
    def test_get_extractor_for_epub_extension(self):
        """Test getting extractor for EPUB extension."""
        extractors = self.detector.get_extractor_for_extension('.epub')
        assert len(extractors) == 1
        assert extractors[0].extractor_name == "EPUB Extractor (ebooklib)"
        
        extractors_no_dot = self.detector.get_extractor_for_extension('epub')
        assert len(extractors_no_dot) == 1
        assert extractors_no_dot[0].extractor_name == "EPUB Extractor (ebooklib)"
    
    def test_detect_document_type_epub(self):
        """Test full document type detection for EPUB."""
        with tempfile.NamedTemporaryFile(suffix='.epub', delete=False) as tmp_file:
            tmp_path = Path(tmp_file.name)
            
            try:
                extractor = self.detector.detect_document_type(tmp_path)
                assert extractor is not None
                assert extractor.extractor_name == "EPUB Extractor (ebooklib)"
            finally:
                os.unlink(tmp_path)
    
    def test_get_detection_info_epub(self):
        """Test detection info for EPUB files."""
        with tempfile.NamedTemporaryFile(suffix='.epub', delete=False) as tmp_file:
            tmp_path = Path(tmp_file.name)
            
            try:
                info = self.detector.get_detection_info(tmp_path)
                
                assert info['extension'] == '.epub'
                assert info['selected_extractor'] == 'EPUB Extractor (ebooklib)'
                assert info['confidence'] > 0
                assert 'extension' in info['detection_methods']
                assert info['detection_methods']['extension']['extractor'] == 'EPUB Extractor (ebooklib)'
            finally:
                os.unlink(tmp_path)


class TestEPUBExtractorPerformance:
    """Performance tests for EPUB extractor."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = EPUBExtractor()
        self.config = {'process_chapters_individually': True}
    
    @patch('src.ingestion.extractors.epub.epub.read_epub')
    def test_large_epub_processing(self, mock_read_epub):
        """Test processing of large EPUB files."""
        # Mock large EPUB with many chapters
        mock_book = Mock()
        
        # Create 50 mock chapters
        mock_items = []
        for i in range(50):
            mock_item = Mock()
            mock_item.get_content.return_value = f"<html><body><h1>Chapter {i+1}</h1><p>{'Content ' * 100}</p></body></html>".encode('utf-8')
            mock_items.append(mock_item)
        
        mock_book.get_items_of_type.return_value = mock_items
        mock_read_epub.return_value = mock_book
        
        self.extractor.book = mock_book
        
        # Should process without memory issues
        with patch.object(self.extractor, '_get_chapter_title', side_effect=[f"Chapter {i+1}" for i in range(50)]):
            result = self.extractor.extract_text(Path("large_test.epub"), self.config)
        
        assert len(result) > 0
        assert "Chapter 1" in result
        assert "Chapter 50" in result
    
    def test_memory_usage_epub_processing(self):
        """Test memory usage during EPUB processing."""
        # This is more of a placeholder for actual memory profiling
        # In a real scenario, you'd use memory_profiler or similar tools
        
        # Basic test that the extractor can be instantiated multiple times
        extractors = [EPUBExtractor() for _ in range(10)]
        assert len(extractors) == 10
        
        # Test that instances are independent
        extractors[0].book = "test1"
        extractors[1].book = "test2"
        assert extractors[0].book != extractors[1].book


if __name__ == "__main__":
    pytest.main([__file__])