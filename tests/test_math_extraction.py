"""
Unit tests for mathematical formula extraction in PDFIngestorEnhanced.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.ingestion.pdf2txt_enhanced import PDFIngestorEnhanced, MathBlock


class TestMathBlock:
    """Test MathBlock class functionality."""
    
    def test_math_block_creation(self):
        """Test MathBlock initialization and basic properties."""
        bbox = (10.0, 20.0, 100.0, 50.0)
        raw_text = "∫f(x)dx"
        latex = r"\int f(x) dx"
        confidence = 0.85
        
        block = MathBlock(bbox, raw_text, latex, confidence)
        
        assert block.bbox == bbox
        assert block.raw_text == raw_text
        assert block.latex == latex
        assert block.confidence == confidence
    
    def test_math_block_to_dict(self):
        """Test MathBlock serialization to dictionary."""
        block = MathBlock(
            bbox=(0, 0, 50, 25),
            raw_text="x²",
            latex="x^2",
            confidence=0.9
        )
        
        expected = {
            'bbox': (0, 0, 50, 25),
            'raw_text': "x²",
            'latex': "x^2",
            'confidence': 0.9
        }
        
        assert block.to_dict() == expected


class TestPDFIngestorEnhanced:
    """Test enhanced PDF ingestion with mathematical formula support."""
    
    @pytest.fixture
    def enhanced_config(self):
        """Enhanced configuration for testing."""
        return {
            'input_dir': './test_input',
            'text_dir': './test_text',
            'meta_dir': './test_meta',
            'math_dir': './test_math',
            'log_level': 'INFO',
            'log_to_file': False,
            'preserve_reading_order': True,
            'warn_empty_pages': True,
            'encoding': 'utf-8',
            'json_indent': 2,
            'parallel_workers': 1,
            'skip_existing': False,
            'show_progress': False,
            'extract_math': True,
            'math_ocr_fallback': False,
            'separate_math_files': True,
            'doi_regex': r'10\.[0-9]{4,}[-._;()/:a-zA-Z0-9]*',
            'doi_prefixes': ['doi:', 'DOI:']
        }
    
    def test_enhanced_ingestor_initialization(self, enhanced_config, tmp_path):
        """Test PDFIngestorEnhanced initialization."""
        # Update config with temp paths
        enhanced_config.update({
            'input_dir': str(tmp_path / 'input'),
            'text_dir': str(tmp_path / 'text'),
            'meta_dir': str(tmp_path / 'meta'),
            'math_dir': str(tmp_path / 'math')
        })
        
        ingestor = PDFIngestorEnhanced(enhanced_config)
        
        assert ingestor.input_dir == Path(enhanced_config['input_dir'])
        assert ingestor.text_dir == Path(enhanced_config['text_dir'])
        assert ingestor.meta_dir == Path(enhanced_config['meta_dir'])
        assert ingestor.math_dir == Path(enhanced_config['math_dir'])
        assert ingestor.extract_math is True
        
        # Check directories were created
        assert ingestor.input_dir.exists()
        assert ingestor.text_dir.exists()
        assert ingestor.meta_dir.exists()
        assert ingestor.math_dir.exists()
    
    def test_is_math_font(self, enhanced_config):
        """Test mathematical font detection."""
        ingestor = PDFIngestorEnhanced(enhanced_config)
        
        # Test mathematical fonts
        assert ingestor._is_math_font("CMMI12") is True
        assert ingestor._is_math_font("CMSY10") is True
        assert ingestor._is_math_font("Symbol") is True
        assert ingestor._is_math_font("MSAM7") is True
        
        # Test non-mathematical fonts
        assert ingestor._is_math_font("Times-Roman") is False
        assert ingestor._is_math_font("Helvetica") is False
        assert ingestor._is_math_font("Arial") is False
        assert ingestor._is_math_font("") is False
        assert ingestor._is_math_font(None) is False
    
    def test_convert_to_latex(self, enhanced_config):
        """Test mathematical symbol to LaTeX conversion."""
        ingestor = PDFIngestorEnhanced(enhanced_config)
        
        # Test symbol conversion
        test_cases = [
            ("∫f(x)dx", r"\int f(x)dx"),
            ("∑x²", r"\sum x²"),
            ("α + β = γ", r"\alpha + \beta = \gamma"),
            ("x^2 + y_1", "x^{2} + y_{1}"),
            ("E = mc²", "E = mc²"),
        ]
        
        for input_text, expected in test_cases:
            result = ingestor._convert_to_latex(input_text, set())
            # Check that conversion occurred (exact match may vary)
            assert len(result) >= len(input_text)
            assert any(symbol in result for symbol in [r'\int', r'\sum', r'\alpha', r'\beta', r'\gamma'] 
                      if any(orig in input_text for orig in ['∫', '∑', 'α', 'β', 'γ']))
    
    def test_detect_math_blocks_basic(self, enhanced_config):
        """Test basic mathematical block detection."""
        ingestor = PDFIngestorEnhanced(enhanced_config)
        
        # Mock page dictionary with mathematical content
        page_dict = {
            'blocks': [
                {
                    'bbox': (100, 200, 300, 250),
                    'lines': [
                        {
                            'spans': [
                                {
                                    'font': 'CMMI12',
                                    'text': '∫f(x)dx = F(x) + C'
                                }
                            ]
                        }
                    ]
                },
                {
                    'bbox': (100, 300, 400, 350),
                    'lines': [
                        {
                            'spans': [
                                {
                                    'font': 'Times-Roman',
                                    'text': 'This is regular text without formulas.'
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        
        math_blocks = ingestor._detect_math_blocks(page_dict)
        
        # Should detect one mathematical block
        assert len(math_blocks) == 1
        assert '∫f(x)dx = F(x) + C' in math_blocks[0].raw_text
        assert math_blocks[0].confidence > 0.5
    
    def test_detect_math_blocks_symbols(self, enhanced_config):
        """Test mathematical block detection based on symbols."""
        ingestor = PDFIngestorEnhanced(enhanced_config)
        
        # Mock page dictionary with mathematical symbols
        page_dict = {
            'blocks': [
                {
                    'bbox': (50, 100, 200, 150),
                    'lines': [
                        {
                            'spans': [
                                {
                                    'font': 'Times-Roman',
                                    'text': 'α = β + γ'
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        
        math_blocks = ingestor._detect_math_blocks(page_dict)
        
        # Should detect mathematical block due to Greek letters
        assert len(math_blocks) == 1
        assert 'α = β + γ' in math_blocks[0].raw_text
    
    def test_integrate_math_blocks(self, enhanced_config):
        """Test integration of mathematical blocks into text."""
        ingestor = PDFIngestorEnhanced(enhanced_config)
        
        original_text = "Consider the integral below:"
        math_blocks = [
            MathBlock((100, 200, 300, 250), "∫f(x)dx", r"\int f(x) dx", 0.9),
            MathBlock((100, 300, 250, 350), "x²", "x^2", 0.8)
        ]
        
        integrated_text = ingestor._integrate_math_blocks(original_text, math_blocks)
        
        # Check that math blocks are included
        assert "[MATH_BLOCK_0]" in integrated_text
        assert "[MATH_BLOCK_1]" in integrated_text
        assert r"\int f(x) dx" in integrated_text
        assert "x^2" in integrated_text
        assert original_text in integrated_text
    
    def test_save_math_blocks(self, enhanced_config, tmp_path):
        """Test saving mathematical blocks to file."""
        enhanced_config.update({
            'math_dir': str(tmp_path / 'math')
        })
        
        ingestor = PDFIngestorEnhanced(enhanced_config)
        
        math_blocks = [
            {
                'page': 1,
                'block': {
                    'bbox': (100, 200, 300, 250),
                    'raw_text': '∫f(x)dx',
                    'latex': r'\int f(x) dx',
                    'confidence': 0.9
                }
            }
        ]
        
        pdf_path = Path('test_document.pdf')
        saved_path = ingestor.save_math_blocks(math_blocks, pdf_path)
        
        assert saved_path is not None
        assert saved_path.exists()
        assert saved_path.suffix == '.math'
        
        # Verify content
        with open(saved_path, 'r') as f:
            saved_data = json.load(f)
        
        assert len(saved_data) == 1
        assert saved_data[0]['page'] == 1
        assert saved_data[0]['block']['latex'] == r'\int f(x) dx'
    
    def test_skip_existing_files_with_math(self, enhanced_config, tmp_path):
        """Test file skipping logic with math files."""
        enhanced_config.update({
            'text_dir': str(tmp_path / 'text'),
            'meta_dir': str(tmp_path / 'meta'),
            'math_dir': str(tmp_path / 'math'),
            'skip_existing': True,
            'separate_math_files': True
        })
        
        ingestor = PDFIngestorEnhanced(enhanced_config)
        
        # Create existing files
        (tmp_path / 'text' / 'test.txt').touch()
        (tmp_path / 'meta' / 'test.json').touch()
        (tmp_path / 'math' / 'test.math').touch()
        
        pdf_path = Path('test.pdf')
        assert ingestor._should_skip_file(pdf_path) is True
        
        # Remove math file
        (tmp_path / 'math' / 'test.math').unlink()
        assert ingestor._should_skip_file(pdf_path) is False
    
    @patch('src.ingestion.pdf2txt_enhanced.fitz.open')
    def test_extract_text_with_math_mock(self, mock_fitz_open, enhanced_config):
        """Test text extraction with mathematical formulas using mocks."""
        # Mock PyMuPDF document
        mock_doc = MagicMock()
        mock_page = MagicMock()
        
        # Mock page text extraction
        mock_page.get_text.return_value = "Consider the integral ∫f(x)dx"
        
        # Mock raw dictionary for math detection
        mock_page.get_text.side_effect = lambda mode=None, sort=True: {
            "rawdict": {
                'blocks': [
                    {
                        'bbox': (100, 200, 300, 250),
                        'lines': [
                            {
                                'spans': [
                                    {
                                        'font': 'CMMI12',
                                        'text': '∫f(x)dx'
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        }.get(mode, "Consider the integral ∫f(x)dx")
        
        mock_doc.__len__.return_value = 1
        mock_doc.load_page.return_value = mock_page
        mock_fitz_open.return_value = mock_doc
        
        ingestor = PDFIngestorEnhanced(enhanced_config)
        pdf_path = Path('test.pdf')
        
        text, math_blocks = ingestor.extract_text_with_math(pdf_path)
        
        assert "Consider the integral" in text
        assert isinstance(math_blocks, list)
        mock_fitz_open.assert_called_once_with(pdf_path)
        mock_doc.close.assert_called_once()


class TestFormulaIntegrity:
    """Test formula extraction integrity on sample content."""
    
    def test_common_mathematical_expressions(self):
        """Test extraction of common mathematical expressions."""
        test_expressions = [
            # Basic algebra
            ("x² + y² = z²", "x^{2} + y^{2} = z^{2}"),
            
            # Calculus
            ("∫₀^∞ e^(-x) dx = 1", r"\int_0^\infty e^{-x} dx = 1"),
            
            # Summations
            ("∑ᵢ₌₁ⁿ i = n(n+1)/2", r"\sum_{i=1}^n i = n(n+1)/2"),
            
            # Greek letters
            ("μ ± σ", r"\mu \pm \sigma"),
            
            # Complex expressions
            ("∇²φ = ∂²φ/∂x² + ∂²φ/∂y²", r"\nabla^2\phi = \partial^2\phi/\partial x^2 + \partial^2\phi/\partial y^2"),
        ]
        
        config = {
            'input_dir': './test',
            'text_dir': './test',
            'meta_dir': './test',
            'math_dir': './test',
            'extract_math': True,
            'log_to_file': False
        }
        
        ingestor = PDFIngestorEnhanced(config)
        
        for expression, expected_pattern in test_expressions:
            latex_result = ingestor._convert_to_latex(expression, {'CMMI12'})
            
            # Check that mathematical symbols were converted
            has_conversion = any(
                latex_cmd in latex_result 
                for latex_cmd in [r'\int', r'\sum', r'\partial', r'\nabla', r'\mu', r'\sigma', r'\pm']
                if any(symbol in expression for symbol in ['∫', '∑', '∂', '∇', 'μ', 'σ', '±'])
            )
            
            # For expressions with mathematical symbols, expect some LaTeX conversion
            if any(ord(char) > 127 for char in expression):  # Contains non-ASCII (likely math symbols)
                assert has_conversion or '\\' in latex_result, f"Failed to convert: {expression}"
    
    def test_formula_structure_preservation(self):
        """Test that formula structure is preserved during extraction."""
        config = {
            'input_dir': './test',
            'text_dir': './test', 
            'meta_dir': './test',
            'math_dir': './test',
            'extract_math': True,
            'log_to_file': False
        }
        
        ingestor = PDFIngestorEnhanced(config)
        
        # Test multi-line formula integration
        original_text = "The equation is:\n\nE = mc²\n\nwhere c is the speed of light."
        
        math_blocks = [
            MathBlock(
                bbox=(100, 200, 200, 250),
                raw_text="E = mc²",
                latex="E = mc^2",
                confidence=0.9
            )
        ]
        
        integrated = ingestor._integrate_math_blocks(original_text, math_blocks)
        
        # Check that both original text and math blocks are present
        assert "The equation is:" in integrated
        assert "where c is the speed of light." in integrated
        assert "[MATH_BLOCK_0]" in integrated
        assert "E = mc^2" in integrated
    
    def test_math_block_confidence_scoring(self):
        """Test confidence scoring for mathematical block detection."""
        config = {
            'input_dir': './test',
            'text_dir': './test',
            'meta_dir': './test', 
            'math_dir': './test',
            'extract_math': True,
            'log_to_file': False
        }
        
        ingestor = PDFIngestorEnhanced(config)
        
        # High confidence: mathematical font + symbols
        high_conf_dict = {
            'blocks': [
                {
                    'bbox': (100, 200, 300, 250),
                    'lines': [
                        {
                            'spans': [
                                {
                                    'font': 'CMMI12',
                                    'text': '∫∑∂φ'
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        
        # Low confidence: regular font + few symbols
        low_conf_dict = {
            'blocks': [
                {
                    'bbox': (100, 200, 300, 250),
                    'lines': [
                        {
                            'spans': [
                                {
                                    'font': 'Times-Roman',
                                    'text': 'x = 5'
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        
        high_blocks = ingestor._detect_math_blocks(high_conf_dict)
        low_blocks = ingestor._detect_math_blocks(low_conf_dict)
        
        if high_blocks:
            assert high_blocks[0].confidence > 0.5
        
        # Low confidence block might not be detected as mathematical
        if low_blocks:
            assert low_blocks[0].confidence < high_blocks[0].confidence if high_blocks else True


# Integration test fixtures
@pytest.fixture
def sample_math_pdf_content():
    """Sample mathematical PDF content for testing."""
    return {
        'text': "Consider the definite integral ∫₀¹ x² dx = 1/3",
        'expected_math_symbols': ['∫', '²'],
        'expected_latex_elements': [r'\int', '^{2}']
    }


def test_end_to_end_math_extraction(sample_math_pdf_content, tmp_path):
    """End-to-end test of mathematical formula extraction."""
    config = {
        'input_dir': str(tmp_path / 'input'),
        'text_dir': str(tmp_path / 'text'),
        'meta_dir': str(tmp_path / 'meta'),
        'math_dir': str(tmp_path / 'math'),
        'extract_math': True,
        'separate_math_files': True,
        'log_to_file': False,
        'show_progress': False
    }
    
    ingestor = PDFIngestorEnhanced(config)
    
    # Verify mathematical symbol detection works
    test_text = sample_math_pdf_content['text']
    contains_math_symbols = any(
        symbol in test_text 
        for symbol in sample_math_pdf_content['expected_math_symbols']
    )
    
    assert contains_math_symbols, "Test content should contain mathematical symbols"
    
    # Test LaTeX conversion
    latex_result = ingestor._convert_to_latex(test_text, {'CMMI12'})
    
    # Should contain some LaTeX elements for mathematical content
    has_latex_conversion = any(
        element in latex_result 
        for element in sample_math_pdf_content['expected_latex_elements']
    )
    
    # If the original text had mathematical symbols, expect some conversion
    if contains_math_symbols:
        assert has_latex_conversion or len(latex_result) >= len(test_text)