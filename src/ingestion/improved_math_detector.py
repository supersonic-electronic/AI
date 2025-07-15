"""
Improved mathematical content detector with better precision and reduced false positives.

This module provides enhanced mathematical content detection that reduces false positives
by implementing stricter filtering criteria and better context analysis.
"""

import logging
import re
from typing import Dict, List, Optional, Set, Tuple, Union

from src.settings import Settings


class ImprovedMathDetector:
    """
    Enhanced mathematical content detector with improved precision.
    
    This class reduces false positives by implementing stricter filtering
    and better context analysis for mathematical content detection.
    """
    
    def __init__(self, settings: Settings):
        """
        Initialize the improved math detector.
        
        Args:
            settings: Application settings instance
        """
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        
        # Precompile mathematical patterns
        self._compile_patterns()
        
        # Initialize OCR clients if available
        self._initialize_ocr_clients()
    
    def _compile_patterns(self) -> None:
        """Compile all regex patterns for mathematical content detection."""
        
        # Mathematical symbols pattern (unchanged)
        self.math_symbols_pattern = re.compile(
            r'[∫∑∏∂∇∞≤≥≠≈±∓×÷∘√αβγδεζηθλμπρστφχψωΓΔΘΛΠΣΦΨΩ]'
        )
        
        # Enhanced equation patterns (more specific)
        self.equation_patterns = [
            # Complete equations with both sides
            re.compile(r'[a-zA-Z_][a-zA-Z0-9_]*\s*=\s*[a-zA-Z0-9_+\-*/()^√∫∑∏∂∇∞≤≥≠≈±∓×÷∘αβγδεζηθλμπρστφχψωΓΔΘΛΠΣΦΨΩ\s]+'),
            # Mathematical expressions with operations
            re.compile(r'[a-zA-Z_][a-zA-Z0-9_]*\s*[+\-*/^]\s*[a-zA-Z0-9_]+'),
            # Fractions
            re.compile(r'[a-zA-Z0-9_+\-*/()^]+/[a-zA-Z0-9_+\-*/()^]+'),
            # Summations and integrals
            re.compile(r'[∫∑∏]\s*[a-zA-Z0-9_+\-*/()^=\s]+'),
            # Matrix notation
            re.compile(r'[a-zA-Z][a-zA-Z0-9_]*\s*\[\s*[a-zA-Z0-9_,\s]+\s*\]'),
        ]
        
        # Patterns for rejecting non-mathematical content
        self.rejection_patterns = [
            # Page numbers
            re.compile(r'^\s*\d+\s*$'),
            # Simple citations
            re.compile(r'^\s*\[\s*\d+\s*\]\s*$'),
            # Single isolated variables (too short)
            re.compile(r'^\s*[a-zA-Z]\d*\s*$'),
            # Section headers
            re.compile(r'^\s*\d+\.\s*[A-Z][a-zA-Z\s]+$'),
            # Common words with numbers
            re.compile(r'\b(page|section|chapter|figure|table|equation|example)\s+\d+\b', re.IGNORECASE),
            # Stock symbols (like XXX)
            re.compile(r'^[A-Z]{2,5}$'),
            # Time formats
            re.compile(r'\d{1,2}:\d{2}'),
            # Dates
            re.compile(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}'),
        ]
        
        # Enhanced mathematical operator patterns
        self.operator_pattern = re.compile(r'[+\-*/^()[\]{}|=<>≤≥≠≈±∓×÷∘]')
        
        # Subscript/superscript patterns (more specific)
        self.subscript_pattern = re.compile(r'[a-zA-Z_][a-zA-Z0-9_]*[_₀₁₂₃₄₅₆₇₈₉]')
        self.superscript_pattern = re.compile(r'[a-zA-Z_][a-zA-Z0-9_]*[\^⁰¹²³⁴⁵⁶⁷⁸⁹]')
        
        # Financial/statistical patterns (more specific)
        self.finance_patterns = [
            re.compile(r'\\b(?:E\\(.*?\\)|Var\\(.*?\\)|Cov\\(.*?\\)|Corr\\(.*?\\))\\b'),
            re.compile(r'\\b(?:return|variance|covariance|correlation|portfolio|sharpe|beta|alpha)\\s*[=:]', re.IGNORECASE),
            re.compile(r'\\b(?:σ|μ|ρ|β|α)\\s*[=:]'),
        ]
        
        # Matrix/vector patterns (more specific)
        self.matrix_patterns = [
            re.compile(r'\\b[A-Z]\\s*=\\s*\\[.*?\\]'),  # Matrix assignment
            re.compile(r'[∑∏]\\s*[a-zA-Z0-9_=\\s]+'),  # Summation/product with limits
            re.compile(r'∫\\s*[a-zA-Z0-9_()\\s]+\\s*d[a-zA-Z]'),  # Integral with differential
        ]
        
        # Minimum length for mathematical expressions
        self.min_math_length = 3
        
        self.logger.debug("Compiled improved mathematical detection patterns")
    
    def _initialize_ocr_clients(self) -> None:
        """Initialize OCR clients for fallback processing."""
        self.mathpix_client = None
        self.openai_client = None
        
        # Initialize Mathpix client if configured
        if self.settings.mathpix_app_id and self.settings.mathpix_app_key:
            try:
                from mpxpy.mathpix_client import MathpixClient
                self.mathpix_client = MathpixClient(
                    app_id=self.settings.mathpix_app_id,
                    app_key=self.settings.mathpix_app_key
                )
                self.logger.info("Mathpix client initialized via mpxpy")
            except ImportError:
                self.logger.warning("mpxpy package not available")
            except Exception as e:
                self.logger.error(f"Failed to initialize Mathpix client: {e}")
        
        # Initialize OpenAI client if configured
        if self.settings.openai_api_key:
            try:
                import openai
                self.openai_client = openai.OpenAI(api_key=self.settings.openai_api_key)
                self.logger.info("OpenAI client initialized")
            except ImportError:
                self.logger.warning("OpenAI package not available")
            except Exception as e:
                self.logger.error(f"Failed to initialize OpenAI: {e}")
    
    def detect_mathematical_content(self, text: str, font_names: Optional[Set[str]] = None) -> Tuple[bool, float, Dict[str, int]]:
        """
        Detect mathematical content with improved precision.
        
        Args:
            text: Text to analyze
            font_names: Set of font names found in the text
            
        Returns:
            Tuple of (is_mathematical, confidence_score, score_breakdown)
        """
        if not text.strip():
            return False, 0.0, {}
        
        # Quick rejection filters
        if self._should_reject_text(text):
            return False, 0.0, {'rejected': 1}
        
        font_names = font_names or set()
        score_breakdown = {}
        total_score = 0.0
        
        # 1. Mathematical symbols score (higher weight)
        symbol_matches = len(self.math_symbols_pattern.findall(text))
        if symbol_matches > 0:
            symbol_score = min(4.0, symbol_matches * 0.8)  # Increased weight
            total_score += symbol_score
            score_breakdown['symbols'] = symbol_matches
        
        # 2. Enhanced equation patterns score
        equation_score = 0.0
        for pattern in self.equation_patterns:
            if pattern.search(text):
                equation_score += 2.0  # Higher weight for complete equations
                break  # Only count once
        total_score += equation_score
        score_breakdown['equations'] = int(equation_score / 2)
        
        # 3. Mathematical operators score (reduced weight for isolated operators)
        operator_matches = len(self.operator_pattern.findall(text))
        if operator_matches >= 2:  # Require at least 2 operators
            operator_score = min(2.0, operator_matches * 0.3)
            total_score += operator_score
            score_breakdown['operators'] = operator_matches
        
        # 4. Mathematical fonts score (unchanged)
        math_font_count = len(font_names & {'CMMI', 'CMSY', 'CMEX', 'CMTI', 'CMR', 'MSAM', 'MSBM', 'MTMI', 'MTSY', 'Symbol', 'MT-Symbol'})
        if math_font_count > 0:
            font_score = min(3.0, math_font_count * 1.5)
            total_score += font_score
            score_breakdown['math_fonts'] = math_font_count
        
        # 5. Enhanced financial/statistical terms score
        finance_score = 0.0
        for pattern in self.finance_patterns:
            if pattern.search(text):
                finance_score += 1.5  # Higher weight for financial math
                break
        total_score += finance_score
        score_breakdown['finance_terms'] = int(finance_score > 0)
        
        # 6. Enhanced matrix/vector expressions score
        matrix_score = 0.0
        for pattern in self.matrix_patterns:
            if pattern.search(text):
                matrix_score += 2.0  # Higher weight for matrix operations
                break
        total_score += matrix_score
        score_breakdown['matrix_vector'] = int(matrix_score > 0)
        
        # 7. Subscript/superscript score (only for meaningful patterns)
        subscript_matches = len(self.subscript_pattern.findall(text))
        superscript_matches = len(self.superscript_pattern.findall(text))
        if subscript_matches + superscript_matches > 0:
            script_score = min(1.5, (subscript_matches + superscript_matches) * 0.5)
            total_score += script_score
            score_breakdown['subscripts_superscripts'] = subscript_matches + superscript_matches
        
        # 8. Length penalty for very short expressions
        if len(text.strip()) < self.min_math_length:
            total_score *= 0.5  # Penalize very short expressions
        
        # 9. Context bonus for multi-line expressions
        if '\\n' in text and len(text.strip()) > 20:
            total_score += 1.0  # Bonus for multi-line mathematical expressions
            score_breakdown['multiline_bonus'] = 1
        
        # Calculate confidence score (0.0 to 1.0)
        max_possible_score = 18.0  # Adjusted for new scoring
        confidence = min(1.0, total_score / max_possible_score)
        
        # Use higher threshold for better precision
        threshold = max(self.settings.math_detection_threshold, 5.0)  # Minimum threshold of 5
        is_mathematical = total_score >= threshold
        
        self.logger.debug(f"Math detection: text='{text[:50]}...', score={total_score:.2f}, confidence={confidence:.3f}, is_math={is_mathematical}")
        
        return is_mathematical, confidence, score_breakdown
    
    def _should_reject_text(self, text: str) -> bool:
        """
        Check if text should be rejected as non-mathematical.
        
        Args:
            text: Text to check
            
        Returns:
            True if text should be rejected
        """
        text_stripped = text.strip()
        
        # Check rejection patterns
        for pattern in self.rejection_patterns:
            if pattern.search(text_stripped):
                return True
        
        # Reject very short text without clear mathematical indicators
        if len(text_stripped) < self.min_math_length:
            return True
        
        # Reject text that's mostly alphabetic (likely regular text)
        alpha_count = sum(1 for c in text_stripped if c.isalpha())
        if len(text_stripped) > 10 and alpha_count / len(text_stripped) > 0.8:
            return True
        
        return False
    
    def ocr_math_fallback(self, image_bytes: bytes) -> Optional[str]:
        """
        Use OCR to extract LaTeX from mathematical formula image.
        
        Args:
            image_bytes: Image bytes containing the formula
            
        Returns:
            LaTeX representation or None if OCR fails
        """
        # Try Mathpix first (specialized for math)
        if self.mathpix_client:
            try:
                import base64
                import tempfile
                import os
                
                # Create temporary image file
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                    tmp_file.write(image_bytes)
                    tmp_file_path = tmp_file.name
                
                try:
                    # Use mpxpy to process the image
                    image_result = self.mathpix_client.image_new(
                        file_path=tmp_file_path,
                        improve_mathpix=True
                    )
                    
                    # Get the LaTeX result from the image processing
                    if image_result and hasattr(image_result, 'latex_simplified'):
                        latex = image_result.latex_simplified.strip()
                        self.logger.debug(f"Mathpix OCR result: {latex[:100]}")
                        return latex
                    elif image_result and hasattr(image_result, 'text'):
                        # Fallback to regular text if LaTeX not available
                        latex = image_result.text.strip()
                        self.logger.debug(f"Mathpix OCR fallback text: {latex[:100]}")
                        return latex
                        
                finally:
                    # Clean up temporary file
                    if os.path.exists(tmp_file_path):
                        os.unlink(tmp_file_path)
                    
            except Exception as e:
                self.logger.warning(f"Mathpix OCR failed: {e}")
        
        # Fall back to OpenAI Vision
        if self.openai_client:
            try:
                import base64
                base64_image = base64.b64encode(image_bytes).decode('utf-8')
                
                response = self.openai_client.chat.completions.create(
                    model="gpt-4-vision-preview",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": "Extract the mathematical formula from this image and convert it to LaTeX. Return only the LaTeX code, no explanation."
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/png;base64,{base64_image}"
                                    }
                                }
                            ]
                        }
                    ],
                    max_tokens=300,
                    timeout=self.settings.openai_timeout
                )
                
                latex = response.choices[0].message.content.strip()
                if latex:
                    self.logger.debug(f"OpenAI Vision OCR result: {latex[:100]}")
                    return latex
                    
            except Exception as e:
                self.logger.warning(f"OpenAI Vision OCR failed: {e}")
        
        return None


def get_improved_math_detector(settings: Settings) -> ImprovedMathDetector:
    """
    Factory function to create an improved math detector instance.
    
    Args:
        settings: Application settings
        
    Returns:
        ImprovedMathDetector instance
    """
    return ImprovedMathDetector(settings)