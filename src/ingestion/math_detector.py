"""
Mathematical content detection with precompiled regex patterns and heuristics.

This module provides a specialized MathDetector class for identifying and extracting
mathematical content from PDF documents with high accuracy and performance.
"""

import logging
import re
from typing import Dict, List, Optional, Set, Tuple, Union

import fitz  # PyMuPDF

from src.settings import Settings


class MathDetector:
    """
    Mathematical content detector with precompiled patterns and advanced heuristics.
    
    This class provides efficient mathematical content detection using precompiled
    regex patterns, font analysis, and configurable scoring algorithms.
    """
    
    def __init__(self, settings: Settings):
        """
        Initialize the math detector with precompiled patterns.
        
        Args:
            settings: Application settings instance
        """
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        
        # Precompile mathematical symbol patterns
        self._compile_patterns()
        
        # Mathematical font sets
        self.math_fonts = {
            'CMMI', 'CMSY', 'CMEX', 'CMTI', 'CMR',  # Computer Modern
            'MSAM', 'MSBM',  # AMS fonts
            'MTMI', 'MTSY',  # MathTime
            'Symbol', 'MT-Symbol', 'ZapfDingbats'  # Symbol fonts
        }
        
        # LaTeX symbol mappings
        self.symbol_to_latex = {
            '∫': r'\int',
            '∑': r'\sum',
            '∏': r'\prod',
            '∂': r'\partial',
            '∇': r'\nabla',
            '∞': r'\infty',
            '≤': r'\leq',
            '≥': r'\geq',
            '≠': r'\neq',
            '≈': r'\approx',
            '±': r'\pm',
            '∓': r'\mp',
            '×': r'\times',
            '÷': r'\div',
            '∘': r'\circ',
            '√': r'\sqrt',
            'α': r'\alpha',
            'β': r'\beta',
            'γ': r'\gamma',
            'δ': r'\delta',
            'ε': r'\epsilon',
            'ζ': r'\zeta',
            'η': r'\eta',
            'θ': r'\theta',
            'λ': r'\lambda',
            'μ': r'\mu',
            'π': r'\pi',
            'ρ': r'\rho',
            'σ': r'\sigma',
            'τ': r'\tau',
            'φ': r'\phi',
            'χ': r'\chi',
            'ψ': r'\psi',
            'ω': r'\omega',
            'Γ': r'\Gamma',
            'Δ': r'\Delta',
            'Θ': r'\Theta',
            'Λ': r'\Lambda',
            'Π': r'\Pi',
            'Σ': r'\Sigma',
            'Φ': r'\Phi',
            'Ψ': r'\Psi',
            'Ω': r'\Omega'
        }
        
        # Initialize Mathpix client if configured
        self.mathpix_client = None
        if settings.mathpix_app_id and settings.mathpix_app_key:
            try:
                from mpxpy.mathpix_client import MathpixClient
                self.mathpix_client = MathpixClient(
                    app_id=settings.mathpix_app_id,
                    app_key=settings.mathpix_app_key
                )
                self.logger.info("Mathpix client initialized via mpxpy")
            except ImportError:
                self.logger.warning("mpxpy package not available, OCR fallback disabled")
            except Exception as e:
                self.logger.error(f"Failed to initialize Mathpix client: {e}")
        
        # Initialize OpenAI client if configured
        self.openai_client = None
        if settings.openai_api_key:
            try:
                import openai
                self.openai_client = openai.OpenAI(api_key=settings.openai_api_key)
                self.logger.info("OpenAI client initialized successfully")
            except ImportError:
                self.logger.warning("OpenAI package not available")
            except Exception as e:
                self.logger.error(f"Failed to initialize OpenAI client: {e}")
    
    def _compile_patterns(self) -> None:
        """Precompile all regex patterns for performance."""
        # Mathematical symbol patterns
        self.math_symbols_pattern = re.compile(
            r'[∫∑∏∂∇∞≤≥≠≈±∓×÷∘√αβγδεζηθλμπρστφχψωΓΔΘΛΠΣΦΨΩ]'
        )
        
        # Equation patterns
        self.equation_patterns = [
            re.compile(r'[a-zA-Z_]\w*\s*=\s*[^=]'),  # Variable = expression
            re.compile(r'[0-9]+\s*=\s*[^=]'),        # Number = expression
            re.compile(r'=\s*[a-zA-Z0-9_]'),         # = variable/number
        ]
        
        # Mathematical operator patterns
        self.operator_pattern = re.compile(r'[+\-*/^()[\]{}|]')
        
        # Subscript/superscript patterns
        self.subscript_pattern = re.compile(r'[a-zA-Z_]\w*[_₀₁₂₃₄₅₆₇₈₉]')
        self.superscript_pattern = re.compile(r'[a-zA-Z_]\w*[\^⁰¹²³⁴⁵⁶⁷⁸⁹]')
        
        # Mathematical variable patterns
        self.variable_patterns = [
            re.compile(r'\b[a-zA-Z]\b'),              # Single letter variables
            re.compile(r'\b[a-zA-Z][0-9]+\b'),        # Variables with numbers (x1, x2)
            re.compile(r'\b[a-zA-Z]_[a-zA-Z0-9]+\b'), # Variables with subscripts
        ]
        
        # Financial/statistical patterns
        self.finance_patterns = [
            re.compile(r'\b(?:return|variance|covariance|correlation|portfolio|sharpe|beta|alpha)\b', re.IGNORECASE),
            re.compile(r'\b(?:E\(.*?\)|Var\(.*?\)|Cov\(.*?\))\b'),  # E(X), Var(X), Cov(X,Y)
            re.compile(r'\b(?:σ|μ|ρ|β|α)\b'),                       # Greek letters in finance
        ]
        
        # Matrix/vector patterns
        self.matrix_patterns = [
            re.compile(r'\[[^\]]*\]'),                # Square brackets
            re.compile(r'∑[^∑]*'),                    # Summation expressions
            re.compile(r'∏[^∏]*'),                    # Product expressions
            re.compile(r'∫[^∫]*'),                    # Integral expressions
        ]
        
        # Fraction patterns
        self.fraction_pattern = re.compile(r'\d+/\d+|[a-zA-Z_]\w*/[a-zA-Z_]\w*')
        
        # Mathematical reference patterns (for enhanced text)
        self.mathref_pattern = re.compile(r'\[MATHREF_[^\]]+\]')
        
        self.logger.debug("Compiled mathematical detection patterns")
    
    def detect_mathematical_content(self, text: str, font_names: Optional[Set[str]] = None) -> Tuple[bool, float, Dict[str, int]]:
        """
        Detect if text contains mathematical content using multiple heuristics.
        
        Args:
            text: Text to analyze
            font_names: Set of font names found in the text
            
        Returns:
            Tuple of (is_mathematical, confidence_score, score_breakdown)
        """
        if not text.strip():
            return False, 0.0, {}
        
        font_names = font_names or set()
        score_breakdown = {}
        total_score = 0.0
        
        # 1. Mathematical symbols score
        symbol_matches = len(self.math_symbols_pattern.findall(text))
        symbol_score = min(3.0, symbol_matches * 0.5)
        total_score += symbol_score
        score_breakdown['symbols'] = symbol_matches
        
        # 2. Equation patterns score
        equation_score = 0.0
        for pattern in self.equation_patterns:
            if pattern.search(text):
                equation_score += 1.0
        equation_score = min(2.0, equation_score)
        total_score += equation_score
        score_breakdown['equations'] = int(equation_score)
        
        # 3. Mathematical operators score
        operator_matches = len(self.operator_pattern.findall(text))
        operator_score = min(2.0, operator_matches * 0.2)
        total_score += operator_score
        score_breakdown['operators'] = operator_matches
        
        # 4. Mathematical fonts score
        math_font_count = len(font_names & self.math_fonts)
        font_score = min(3.0, math_font_count * 1.5)
        total_score += font_score
        score_breakdown['math_fonts'] = math_font_count
        
        # 5. Variables score
        variable_score = 0.0
        for pattern in self.variable_patterns:
            matches = len(pattern.findall(text))
            variable_score += matches * 0.1
        variable_score = min(1.5, variable_score)
        total_score += variable_score
        score_breakdown['variables'] = int(variable_score * 10)
        
        # 6. Financial/statistical terms score
        finance_score = 0.0
        for pattern in self.finance_patterns:
            if pattern.search(text):
                finance_score += 0.5
        finance_score = min(2.0, finance_score)
        total_score += finance_score
        score_breakdown['finance_terms'] = int(finance_score * 2)
        
        # 7. Matrix/vector expressions score
        matrix_score = 0.0
        for pattern in self.matrix_patterns:
            if pattern.search(text):
                matrix_score += 1.0
        matrix_score = min(2.0, matrix_score)
        total_score += matrix_score
        score_breakdown['matrix_vector'] = int(matrix_score)
        
        # 8. Subscript/superscript score
        subscript_matches = len(self.subscript_pattern.findall(text))
        superscript_matches = len(self.superscript_pattern.findall(text))
        script_score = min(1.0, (subscript_matches + superscript_matches) * 0.3)
        total_score += script_score
        score_breakdown['subscripts_superscripts'] = subscript_matches + superscript_matches
        
        # 9. Fraction score
        fraction_matches = len(self.fraction_pattern.findall(text))
        fraction_score = min(1.0, fraction_matches * 0.5)
        total_score += fraction_score
        score_breakdown['fractions'] = fraction_matches
        
        # 10. Mathematical reference markers (for enhanced text)
        mathref_matches = len(self.mathref_pattern.findall(text))
        if mathref_matches > 0:
            total_score += 5.0  # Strong indicator
            score_breakdown['mathref_markers'] = mathref_matches
        
        # Calculate confidence score (0.0 to 1.0)
        max_possible_score = 15.0
        confidence = min(1.0, total_score / max_possible_score)
        
        # Determine if content is mathematical
        is_mathematical = total_score >= self.settings.math_detection_threshold
        
        self.logger.debug(f"Math detection: score={total_score:.2f}, confidence={confidence:.3f}, is_math={is_mathematical}")
        
        return is_mathematical, confidence, score_breakdown
    
    def extract_mathematical_fonts(self, page_dict: Dict) -> Set[str]:
        """
        Extract mathematical font names from a page dictionary.
        
        Args:
            page_dict: PyMuPDF page dictionary from get_text("rawdict")
            
        Returns:
            Set of mathematical font names found
        """
        font_names = set()
        
        if 'blocks' not in page_dict:
            return font_names
        
        for block in page_dict['blocks']:
            if 'lines' not in block:
                continue
            
            for line in block['lines']:
                if 'spans' not in line:
                    continue
                
                for span in line['spans']:
                    font_name = span.get('font', '')
                    if font_name:
                        # Check if font name contains mathematical indicators
                        font_upper = font_name.upper()
                        for math_font in self.math_fonts:
                            if math_font in font_upper:
                                font_names.add(font_name)
                                break
        
        return font_names
    
    def classify_semantic_group(self, text: str, confidence: float) -> str:
        """
        Classify mathematical content into semantic groups.
        
        Args:
            text: Mathematical text to classify
            confidence: Confidence score from detection
            
        Returns:
            Semantic group identifier
        """
        text_lower = text.lower()
        
        # High-confidence specific classifications
        if confidence > 0.7:
            # Portfolio/Finance mathematical expressions
            if any(term in text_lower for term in ['portfolio', 'return', 'variance', 'covariance', 'weight', 'sharpe']):
                return "portfolio_theory"
            
            # Statistics and probability
            if any(term in text_lower for term in ['probability', 'distribution', 'hypothesis', 'test', 'correlation']):
                return "statistics"
            
            # Matrix and vector operations
            if any(symbol in text for symbol in ['∑', '∏', '∫']) or 'matrix' in text_lower:
                return "matrix_vector"
        
        # Medium-confidence classifications
        if confidence > 0.4:
            # Variable definitions (simple assignments)
            if re.match(r'^[a-zA-Z]\s*=', text.strip()):
                return "variable_definition"
            
            # Equations (complex expressions with multiple operations)
            if text.count('=') == 1 and any(op in text for op in ['+', '-', '*', '/']):
                return "equation"
            
            # Ratios and fractions
            if '/' in text or any(word in text_lower for word in ['ratio', 'rate']):
                return "ratio"
        
        # Default classification
        return "general_math"
    
    def convert_to_latex(self, text: str, preserve_structure: bool = True) -> str:
        """
        Convert mathematical text to LaTeX representation.
        
        Args:
            text: Text to convert
            preserve_structure: Whether to preserve original structure
            
        Returns:
            LaTeX representation of the mathematical content
        """
        latex = text
        
        # Replace Unicode mathematical symbols
        for symbol, latex_cmd in self.symbol_to_latex.items():
            latex = latex.replace(symbol, latex_cmd)
        
        # Convert subscripts (x1 -> x_{1})
        latex = re.sub(r'([a-zA-Z])([0-9]+)(?!\w)', r'\1_{\2}', latex)
        
        # Convert simple superscripts (x^2 -> x^{2})
        latex = re.sub(r'([a-zA-Z])\^([0-9]+)(?!\w)', r'\1^{\2}', latex)
        
        # Handle fractions (a/b -> \frac{a}{b} for simple cases)
        if preserve_structure and '/' in latex:
            # Simple fraction pattern
            latex = re.sub(r'([a-zA-Z0-9_{}]+)/([a-zA-Z0-9_{}]+)', r'\\frac{\1}{\2}', latex)
        
        # Wrap in math delimiters if not already present and contains mathematical content
        if preserve_structure and not latex.startswith(('$', '\\[')):
            # Check if it needs math delimiters
            has_math_content = (
                any(symbol in latex for symbol in self.symbol_to_latex.values()) or
                '_' in latex or '^' in latex or
                any(op in latex for op in ['\\frac', '\\sum', '\\int', '\\prod'])
            )
            
            if has_math_content:
                latex = f'${latex}$'
        
        return latex
    
    def extract_variables(self, text: str) -> Set[str]:
        """
        Extract mathematical variables from text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Set of variable names found
        """
        variables = set()
        
        # Extract variables using precompiled patterns
        for pattern in self.variable_patterns:
            matches = pattern.findall(text)
            variables.update(matches)
        
        # Add Greek letters
        for symbol in self.symbol_to_latex.keys():
            if symbol in text and len(symbol) == 1:
                variables.add(symbol)
        
        return variables
    
    def analyze_mathematical_complexity(self, text: str) -> Dict[str, Union[int, float, str]]:
        """
        Analyze the complexity of mathematical content.
        
        Args:
            text: Mathematical text to analyze
            
        Returns:
            Dictionary with complexity metrics
        """
        complexity = {
            'symbol_count': len(self.math_symbols_pattern.findall(text)),
            'operator_count': len(self.operator_pattern.findall(text)),
            'variable_count': len(self.extract_variables(text)),
            'equation_count': sum(1 for pattern in self.equation_patterns if pattern.search(text)),
            'has_fractions': bool(self.fraction_pattern.search(text)),
            'has_subscripts': bool(self.subscript_pattern.search(text)),
            'has_superscripts': bool(self.superscript_pattern.search(text)),
            'text_length': len(text),
            'complexity_score': 0.0
        }
        
        # Calculate overall complexity score
        score = (
            complexity['symbol_count'] * 0.5 +
            complexity['operator_count'] * 0.3 +
            complexity['variable_count'] * 0.4 +
            complexity['equation_count'] * 1.0 +
            (1.0 if complexity['has_fractions'] else 0.0) +
            (0.5 if complexity['has_subscripts'] else 0.0) +
            (0.5 if complexity['has_superscripts'] else 0.0)
        )
        
        complexity['complexity_score'] = round(score, 2)
        
        return complexity
    
    def ocr_math_with_mathpix(self, image_bytes: bytes) -> Optional[str]:
        """
        Use Mathpix to extract LaTeX from mathematical formula image.
        
        Args:
            image_bytes: Image bytes containing the formula
            
        Returns:
            LaTeX representation or None if OCR fails
        """
        if not self.mathpix_client:
            return None
        
        try:
            import base64
            
            # Convert bytes to base64 for Mathpix API
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
            
            # Use mpxpy to process the image
            import tempfile
            import os
            
            # Create temporary image file for mpxpy
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
                    self.logger.debug(f"Mathpix extracted LaTeX: {latex[:100]}")
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
        
        return None
    
    def ocr_math_with_openai(self, image_bytes: bytes) -> Optional[str]:
        """
        Use OpenAI Vision to extract LaTeX from mathematical formula image.
        
        Args:
            image_bytes: Image bytes containing the formula
            
        Returns:
            LaTeX representation or None if OCR fails
        """
        if not self.openai_client:
            return None
        
        try:
            import base64
            
            # Encode image for OpenAI
            base64_image = base64.b64encode(image_bytes).decode('utf-8')
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4-vision-preview",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Convert this mathematical formula image to LaTeX. Return only the LaTeX code without explanation."
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
                self.logger.debug(f"OpenAI Vision extracted LaTeX: {latex[:100]}")
                return latex
            
        except Exception as e:
            self.logger.warning(f"OpenAI Vision OCR failed: {e}")
        
        return None
    
    def ocr_math_fallback(self, image_bytes: bytes) -> Optional[str]:
        """
        Try multiple OCR methods as fallback for mathematical formula extraction.
        
        Args:
            image_bytes: Image bytes containing the formula
            
        Returns:
            LaTeX representation from the first successful method or None
        """
        # Try Mathpix first (specialized for math)
        if self.mathpix_client:
            result = self.ocr_math_with_mathpix(image_bytes)
            if result:
                return result
        
        # Fall back to OpenAI Vision
        if self.openai_client:
            result = self.ocr_math_with_openai(image_bytes)
            if result:
                return result
        
        self.logger.debug("All OCR methods failed for mathematical formula")
        return None


# Example usage and testing
if __name__ == "__main__":
    from src.settings import Settings
    
    # Create test settings
    settings = Settings()
    detector = MathDetector(settings)
    
    # Test mathematical content detection
    test_cases = [
        "The expected return is E(R) = μ",
        "Portfolio variance: σ² = w'Σw",
        "The integral ∫f(x)dx represents the area",
        "Simple text without mathematical content",
        "Sharpe ratio = (E(R) - Rf) / σ",
        "Let x₁, x₂, ..., xₙ be the variables",
        "The equation y = mx + b is linear"
    ]
    
    print("Mathematical Content Detection Tests")
    print("=" * 50)
    
    for i, text in enumerate(test_cases, 1):
        is_math, confidence, breakdown = detector.detect_mathematical_content(text)
        semantic_group = detector.classify_semantic_group(text, confidence)
        latex = detector.convert_to_latex(text)
        
        print(f"\nTest {i}: {text}")
        print(f"  Mathematical: {is_math}")
        print(f"  Confidence: {confidence:.3f}")
        print(f"  Semantic group: {semantic_group}")
        print(f"  LaTeX: {latex}")
        print(f"  Score breakdown: {breakdown}")
    
    print("\nMath detector testing completed")