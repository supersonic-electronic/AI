"""
Tests for the MathDetector class.

These tests verify mathematical content detection accuracy, LaTeX conversion,
and OCR fallback functionality.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from src.settings import Settings
from src.ingestion.math_detector import MathDetector


@pytest.fixture
def test_settings():
    """Create test settings instance."""
    return Settings(
        math_detection_threshold=3,
        extract_math=True,
        math_ocr_fallback=False,
        openai_api_key="test-key",
        mathpix_app_id=None,
        mathpix_app_key=None
    )


@pytest.fixture
def math_detector(test_settings):
    """Create MathDetector instance for testing."""
    return MathDetector(test_settings)


class TestMathDetection:
    """Test mathematical content detection."""
    
    def test_detect_simple_equation(self, math_detector):
        """Test detection of simple equations."""
        text = "The expected return is E(R) = μ"
        is_math, confidence, breakdown = math_detector.detect_mathematical_content(text)
        
        assert is_math is True
        assert confidence > 0.5
        assert breakdown['symbols'] > 0
    
    def test_detect_portfolio_formula(self, math_detector):
        """Test detection of portfolio mathematics."""
        text = "Portfolio variance: σ² = w'Σw"
        is_math, confidence, breakdown = math_detector.detect_mathematical_content(text)
        
        assert is_math is True
        assert confidence > 0.7
        assert breakdown['symbols'] > 0
    
    def test_detect_integral(self, math_detector):
        """Test detection of integral expressions."""
        text = "The integral ∫f(x)dx represents the area"
        is_math, confidence, breakdown = math_detector.detect_mathematical_content(text)
        
        assert is_math is True
        assert confidence > 0.6
        assert breakdown['symbols'] > 0
    
    def test_reject_plain_text(self, math_detector):
        """Test rejection of plain text without mathematical content."""
        text = "This is just regular text without any mathematical symbols or equations."
        is_math, confidence, breakdown = math_detector.detect_mathematical_content(text)
        
        assert is_math is False
        assert confidence < 0.3
    
    def test_detect_with_math_fonts(self, math_detector):
        """Test detection with mathematical fonts."""
        text = "x = y + z"
        math_fonts = {"CMMI", "CMSY"}
        is_math, confidence, breakdown = math_detector.detect_mathematical_content(text, math_fonts)
        
        assert is_math is True
        assert confidence > 0.6
        assert breakdown['math_fonts'] > 0


class TestSemanticGrouping:
    """Test semantic grouping of mathematical expressions."""
    
    def test_portfolio_theory_group(self, math_detector):
        """Test portfolio theory semantic grouping."""
        text = "Expected portfolio return E(R_p) = w'μ"
        confidence = 0.8
        group = math_detector.classify_semantic_group(text, confidence)
        
        assert group == "portfolio_theory"
    
    def test_variable_definition_group(self, math_detector):
        """Test variable definition grouping."""
        text = "x = 5"
        confidence = 0.6
        group = math_detector.classify_semantic_group(text, confidence)
        
        assert group == "variable_definition"
    
    def test_equation_group(self, math_detector):
        """Test equation grouping."""
        text = "y = mx + b"
        confidence = 0.7
        group = math_detector.classify_semantic_group(text, confidence)
        
        assert group == "equation"
    
    def test_ratio_group(self, math_detector):
        """Test ratio grouping."""
        text = "Sharpe ratio = return / volatility"
        confidence = 0.6
        group = math_detector.classify_semantic_group(text, confidence)
        
        assert group == "ratio"


class TestLatexConversion:
    """Test LaTeX conversion functionality."""
    
    def test_symbol_conversion(self, math_detector):
        """Test conversion of mathematical symbols to LaTeX."""
        text = "∫ f(x) dx"
        latex = math_detector.convert_to_latex(text)
        
        assert "\\int" in latex
        assert "$" in latex  # Should be wrapped in math delimiters
    
    def test_fraction_conversion(self, math_detector):
        """Test conversion of fractions to LaTeX."""
        text = "x/y"
        latex = math_detector.convert_to_latex(text)
        
        assert "\\frac{x}{y}" in latex
    
    def test_superscript_conversion(self, math_detector):
        """Test conversion of superscripts to LaTeX."""
        text = "x^2"
        latex = math_detector.convert_to_latex(text)
        
        assert "x^{2}" in latex
    
    def test_subscript_conversion(self, math_detector):
        """Test conversion of subscripts to LaTeX."""
        text = "x1"
        latex = math_detector.convert_to_latex(text)
        
        assert "x_{1}" in latex


class TestOCRFallback:
    """Test OCR fallback functionality."""
    
    @patch('src.ingestion.math_detector.openai')
    def test_openai_ocr_success(self, mock_openai, test_settings):
        """Test successful OpenAI OCR."""
        # Setup mock
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "\\frac{x}{y}"
        mock_client.chat.completions.create.return_value = mock_response
        
        # Create detector with mocked OpenAI
        test_settings.openai_api_key = "test-key"
        detector = MathDetector(test_settings)
        detector.openai_client = mock_client
        
        # Test OCR
        image_bytes = b"fake_image_data"
        result = detector.ocr_math_with_openai(image_bytes)
        
        assert result == "\\frac{x}{y}"
        mock_client.chat.completions.create.assert_called_once()
    
    @patch('src.ingestion.math_detector.mathpix')
    def test_mathpix_ocr_success(self, mock_mathpix, test_settings):
        """Test successful Mathpix OCR."""
        # Setup mock
        mock_client = Mock()
        mock_client.latex.return_value = {'latex_simplified': '\\int f(x) dx'}
        
        # Create detector with mocked Mathpix
        test_settings.mathpix_app_id = "test-id"
        test_settings.mathpix_app_key = "test-key"
        detector = MathDetector(test_settings)
        detector.mathpix_client = mock_client
        
        # Test OCR
        image_bytes = b"fake_image_data"
        result = detector.ocr_math_with_mathpix(image_bytes)
        
        assert result == "\\int f(x) dx"
        mock_client.latex.assert_called_once()
    
    def test_ocr_fallback_no_clients(self, test_settings):
        """Test OCR fallback when no clients are available."""
        test_settings.mathpix_app_id = None
        test_settings.openai_api_key = None
        detector = MathDetector(test_settings)
        
        image_bytes = b"fake_image_data"
        result = detector.ocr_math_fallback(image_bytes)
        
        assert result is None


class TestVariableExtraction:
    """Test mathematical variable extraction."""
    
    def test_extract_single_variables(self, math_detector):
        """Test extraction of single letter variables."""
        text = "Let x, y, and z be variables"
        variables = math_detector.extract_variables(text)
        
        assert "x" in variables
        assert "y" in variables
        assert "z" in variables
    
    def test_extract_subscripted_variables(self, math_detector):
        """Test extraction of variables with subscripts."""
        text = "x1, x2, and x_i are variables"
        variables = math_detector.extract_variables(text)
        
        assert "x1" in variables
        assert "x2" in variables
    
    def test_extract_greek_letters(self, math_detector):
        """Test extraction of Greek letter variables."""
        text = "The parameters α, β, and σ are important"
        variables = math_detector.extract_variables(text)
        
        assert "α" in variables
        assert "β" in variables
        assert "σ" in variables


class TestComplexityAnalysis:
    """Test mathematical complexity analysis."""
    
    def test_simple_expression_complexity(self, math_detector):
        """Test complexity analysis of simple expressions."""
        text = "x = 5"
        complexity = math_detector.analyze_mathematical_complexity(text)
        
        assert complexity['symbol_count'] == 0
        assert complexity['operator_count'] == 1  # '='
        assert complexity['variable_count'] == 1  # 'x'
        assert complexity['complexity_score'] > 0
    
    def test_complex_expression_complexity(self, math_detector):
        """Test complexity analysis of complex expressions."""
        text = "σ² = Σ(xi - μ)²/n"
        complexity = math_detector.analyze_mathematical_complexity(text)
        
        assert complexity['symbol_count'] > 0  # Greek letters and symbols
        assert complexity['operator_count'] > 2  # Multiple operators
        assert complexity['has_fractions'] is True
        assert complexity['complexity_score'] > 2


@pytest.mark.integration
class TestIntegration:
    """Integration tests for MathDetector."""
    
    def test_full_detection_pipeline(self, math_detector):
        """Test complete detection pipeline."""
        text = "The Black-Scholes formula: C = S₀N(d₁) - Ke^(-rT)N(d₂)"
        
        # Run detection
        is_math, confidence, breakdown = math_detector.detect_mathematical_content(text)
        
        # Should be detected as mathematical
        assert is_math is True
        assert confidence > 0.5
        
        # Should have appropriate semantic grouping
        group = math_detector.classify_semantic_group(text, confidence)
        assert group in ["equation", "general_math"]
        
        # Should convert to LaTeX
        latex = math_detector.convert_to_latex(text)
        assert len(latex) > 0
        
        # Should extract variables
        variables = math_detector.extract_variables(text)
        assert len(variables) > 0