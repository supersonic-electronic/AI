"""
Enhanced PDF text extraction module with advanced mathematical formula support.

This module provides a PDFIngestorEnhanced class that reliably extracts and preserves
complex mathematical formulas, including multi-line equations, integrals, summations,
and superscripts/subscripts from PDF files.
"""

import argparse
import base64
import io
import json
import logging
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import fitz  # PyMuPDF
import yaml
from tqdm import tqdm

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logging.warning("PIL not available, image extraction disabled")

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logging.warning("OpenAI not available, math OCR fallback disabled")


class MathBlock:
    """Represents a mathematical expression block in a PDF with enhanced linking capabilities."""
    
    def __init__(self, bbox: Tuple[float, float, float, float], 
                 raw_text: str, latex: str = "", confidence: float = 0.0,
                 block_id: str = "", page_num: int = 0, 
                 char_start: int = -1, char_end: int = -1,
                 line_start: int = -1, line_end: int = -1,
                 semantic_group: str = ""):
        """
        Initialize a mathematical block with enhanced linking information.
        
        Args:
            bbox: Bounding box (x0, y0, x1, y1) of the math block
            raw_text: Raw extracted text
            latex: LaTeX representation of the formula
            confidence: Confidence score for the extraction
            block_id: Unique identifier for this math block
            page_num: Page number where this block appears
            char_start: Character offset start in the full document text
            char_end: Character offset end in the full document text
            line_start: Line number start in the extracted text
            line_end: Line number end in the extracted text
            semantic_group: Semantic grouping identifier for related expressions
        """
        self.bbox = bbox
        self.raw_text = raw_text
        self.latex = latex
        self.confidence = confidence
        self.block_id = block_id
        self.page_num = page_num
        self.char_start = char_start
        self.char_end = char_end
        self.line_start = line_start
        self.line_end = line_end
        self.semantic_group = semantic_group
        
        # Additional linking properties
        self.related_blocks: List[str] = []  # IDs of related math blocks
        self.context_before: str = ""  # Text context before this block
        self.context_after: str = ""   # Text context after this block
    
    def add_related_block(self, block_id: str) -> None:
        """Add a related math block ID."""
        if block_id not in self.related_blocks:
            self.related_blocks.append(block_id)
    
    def set_context(self, before: str, after: str) -> None:
        """Set the textual context around this math block."""
        self.context_before = before.strip()
        self.context_after = after.strip()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert math block to dictionary format with enhanced linking."""
        return {
            'block_id': self.block_id,
            'page_num': self.page_num,
            'bbox': self.bbox,
            'raw_text': self.raw_text,
            'latex': self.latex,
            'confidence': self.confidence,
            'char_position': {
                'start': self.char_start,
                'end': self.char_end
            },
            'line_position': {
                'start': self.line_start,
                'end': self.line_end
            },
            'semantic_group': self.semantic_group,
            'related_blocks': self.related_blocks,
            'context': {
                'before': self.context_before,
                'after': self.context_after
            }
        }


class PDFIngestor:
    """
    Enhanced PDF ingestion class with advanced mathematical formula extraction.
    
    This class processes PDF files and extracts both regular text and mathematical
    formulas with high fidelity, preserving complex mathematical notation and
    providing LaTeX representations where possible.
    
    Note: This class has been enhanced from the original PDFIngestor to include
    mathematical formula detection and extraction capabilities.
    """
    
    # Mathematical font patterns
    MATH_FONTS = {
        'CMMI', 'CMSY', 'CMEX', 'CMTI', 'CMR',  # Computer Modern
        'MSAM', 'MSBM',  # AMS fonts
        'MTMI', 'MTSY',  # MathTime
        'Symbol', 'MT-Symbol', 'ZapfDingbats'  # Symbol fonts
    }
    
    # Common mathematical symbols to LaTeX mapping
    SYMBOL_TO_LATEX = {
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
        '√': r'\sqrt',
        'α': r'\alpha',
        'β': r'\beta',
        'γ': r'\gamma',
        'δ': r'\delta',
        'ε': r'\epsilon',
        'θ': r'\theta',
        'λ': r'\lambda',
        'μ': r'\mu',
        'π': r'\pi',
        'σ': r'\sigma',
        'φ': r'\phi',
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
        'Ω': r'\Omega',
    }
    
    def __init__(self, config: Dict[str, Any]) -> None:
        """
        Initialize the enhanced PDFIngestor with configuration.
        
        Args:
            config: Configuration dictionary loaded from YAML
        """
        self.config = config
        self.input_dir = Path(config['input_dir'])
        self.text_dir = Path(config['text_dir'])
        self.meta_dir = Path(config['meta_dir'])
        
        # Create math output directory
        self.math_dir = Path(config.get('math_dir', './data/math'))
        self.math_dir.mkdir(parents=True, exist_ok=True)
        
        # Create directories if they don't exist
        self.input_dir.mkdir(parents=True, exist_ok=True)
        self.text_dir.mkdir(parents=True, exist_ok=True)
        self.meta_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self._setup_logging()
        
        # Compile DOI regex pattern
        self.doi_pattern = re.compile(config.get('doi_regex', r'10\.[0-9]{4,}[-._;()/:a-zA-Z0-9]*'))
        self.doi_prefixes = config.get('doi_prefixes', ['doi:', 'DOI:', 'https://doi.org/', 'http://dx.doi.org/'])
        
        # Math extraction settings
        self.extract_math = config.get('extract_math', True)
        self.math_ocr_fallback = config.get('math_ocr_fallback', False)
        self.separate_math_files = config.get('separate_math_files', True)
        self.math_detection_threshold = config.get('math_detection_threshold', 3)
        
        # Initialize OpenAI client if available and configured
        self.openai_client = None
        if OPENAI_AVAILABLE and self.math_ocr_fallback:
            api_key = config.get('openai_api_key') or config.get('OPENAI_API_KEY')
            if api_key:
                self.openai_client = openai.OpenAI(api_key=api_key)
            else:
                self.logger.warning("Math OCR fallback enabled but no OpenAI API key provided")
    
    def _setup_logging(self) -> None:
        """Setup logging configuration based on config settings."""
        log_level = getattr(logging, self.config.get('log_level', 'INFO').upper())
        
        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        
        # Setup logger
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(log_level)
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # File handler if enabled
        if self.config.get('log_to_file', False):
            log_file = Path(self.config.get('log_file', './logs/pdf_ingestion.log'))
            log_file.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
    def _is_math_font(self, font_name: str) -> bool:
        """
        Check if a font name indicates mathematical content.
        
        Args:
            font_name: Font name to check
            
        Returns:
            True if font is likely mathematical, False otherwise
        """
        if not font_name:
            return False
        
        font_upper = font_name.upper()
        return any(math_font in font_upper for math_font in self.MATH_FONTS)
    
    def _detect_math_blocks(self, page_dict: Dict[str, Any]) -> List[MathBlock]:
        """
        Detect mathematical blocks on a page using font, layout, and pattern analysis.
        
        Args:
            page_dict: Raw page dictionary from PyMuPDF
            
        Returns:
            List of detected mathematical blocks
        """
        math_blocks = []
        
        if 'blocks' not in page_dict:
            return math_blocks
        
        for block in page_dict['blocks']:
            if 'lines' not in block:
                continue
            
            # Analyze block for mathematical content
            math_chars = 0
            total_chars = 0
            math_fonts_found = set()
            block_text = ""
            bbox = block.get('bbox', (0, 0, 0, 0))
            
            for line in block['lines']:
                if 'spans' not in line:
                    continue
                
                for span in line['spans']:
                    font_name = span.get('font', '')
                    text = span.get('text', '')
                    
                    block_text += text
                    total_chars += len(text)
                    
                    # Check for mathematical fonts
                    if self._is_math_font(font_name):
                        math_fonts_found.add(font_name)
                        math_chars += len(text)
                    
                    # Check for mathematical symbols
                    for char in text:
                        if char in self.SYMBOL_TO_LATEX:
                            math_chars += 1
            
            # Enhanced mathematical pattern detection
            is_mathematical = self._is_mathematical_content(block_text, math_fonts_found, total_chars)
            
            if is_mathematical:
                latex = self._convert_to_latex(block_text, math_fonts_found)
                confidence = self._calculate_math_confidence(block_text, math_fonts_found, total_chars)
                
                math_block = MathBlock(bbox, block_text.strip(), latex, confidence)
                math_blocks.append(math_block)
                
                self.logger.debug(f"Detected math block: {block_text[:50]}...")
        
        return math_blocks
    
    def _detect_math_in_text(self, text: str, page_num: int, char_offset_base: int = 0) -> List[MathBlock]:
        """
        Detect mathematical content with enhanced character-level positioning and linking.
        
        This method works better when block-level analysis fails due to 
        mathematical content being split across multiple rendering elements.
        
        Args:
            text: Full page text
            page_num: Page number for reference
            char_offset_base: Character offset base for this page in the full document
            
        Returns:
            List of detected mathematical blocks with enhanced linking
        """
        math_blocks = []
        
        if not text.strip():
            return math_blocks
        
        # Split text into potential mathematical expressions while tracking positions
        lines = text.split('\n')
        current_char_pos = char_offset_base
        
        for i, line in enumerate(lines):
            original_line = line
            line = line.strip()
            
            # Calculate character positions for this line
            line_start_pos = current_char_pos + (len(original_line) - len(original_line.lstrip()))
            line_end_pos = line_start_pos + len(line)
            
            if line:
                # Check if this line looks mathematical
                is_mathematical = self._is_mathematical_content(line, set(), len(line))
                
                if is_mathematical:
                    # Generate unique block ID
                    block_id = f"math_p{page_num}_l{i}_{hash(line) % 10000:04d}"
                    
                    # Create a math block with enhanced positioning
                    bbox = (0, i * 12, 500, (i + 1) * 12)  # Approximate bbox
                    
                    latex = self._convert_to_latex(line, set())
                    confidence = self._calculate_math_confidence(line, set(), len(line))
                    
                    # Determine semantic group based on content
                    semantic_group = self._determine_semantic_group(line)
                    
                    # Extract context (previous and next lines)
                    context_before = lines[i-1].strip() if i > 0 else ""
                    context_after = lines[i+1].strip() if i < len(lines) - 1 else ""
                    
                    math_block = MathBlock(
                        bbox=bbox, 
                        raw_text=line, 
                        latex=latex, 
                        confidence=confidence,
                        block_id=block_id,
                        page_num=page_num,
                        char_start=line_start_pos,
                        char_end=line_end_pos,
                        line_start=i,
                        line_end=i,
                        semantic_group=semantic_group
                    )
                    
                    math_block.set_context(context_before, context_after)
                    math_blocks.append(math_block)
                    
                    self.logger.debug(f"Detected math in text on page {page_num}: {line[:50]}... (pos: {line_start_pos}-{line_end_pos})")
            
            # Update character position for next line (including newline)
            current_char_pos += len(original_line) + 1
        
        # Look for multi-line mathematical expressions with enhanced tracking
        current_char_pos = char_offset_base
        for i in range(len(lines) - 1):
            line1 = lines[i].strip()
            line2 = lines[i + 1].strip()
            
            if not line1 or not line2:
                current_char_pos += len(lines[i]) + 1
                continue
                
            # Check for mathematical continuation patterns
            combined = f"{line1} {line2}"
            
            # Look for split equations or expressions
            if (any(op in line1 for op in ['=', '+', '-']) and 
                any(char in line2 for char in ['x', 'y', 'r', 'R', '(', ')']) and
                len(line1) < 50 and len(line2) < 50):
                
                is_mathematical = self._is_mathematical_content(combined, set(), len(combined))
                
                if is_mathematical:
                    # Generate unique block ID for multi-line
                    block_id = f"math_p{page_num}_ml{i}_{hash(combined) % 10000:04d}"
                    
                    # Calculate character positions for multi-line block
                    line1_start = current_char_pos
                    line1_end = line1_start + len(lines[i])
                    line2_start = line1_end + 1  # +1 for newline
                    line2_end = line2_start + len(lines[i + 1])
                    
                    bbox = (0, i * 12, 500, (i + 2) * 12)
                    latex = self._convert_to_latex(combined, set())
                    confidence = self._calculate_math_confidence(combined, set(), len(combined))
                    semantic_group = self._determine_semantic_group(combined)
                    
                    math_block = MathBlock(
                        bbox=bbox, 
                        raw_text=combined, 
                        latex=latex, 
                        confidence=confidence,
                        block_id=block_id,
                        page_num=page_num,
                        char_start=line1_start,
                        char_end=line2_end,
                        line_start=i,
                        line_end=i + 1,
                        semantic_group=semantic_group
                    )
                    
                    # Set context for multi-line block
                    context_before = lines[i-1].strip() if i > 0 else ""
                    context_after = lines[i+2].strip() if i + 2 < len(lines) else ""
                    math_block.set_context(context_before, context_after)
                    
                    math_blocks.append(math_block)
                    
                    self.logger.debug(f"Detected multi-line math on page {page_num}: {combined[:50]}... (pos: {line1_start}-{line2_end})")
            
            current_char_pos += len(lines[i]) + 1
        
        # Group related mathematical expressions
        math_blocks = self._group_related_math_blocks(math_blocks)
        
        return math_blocks
    
    def _is_mathematical_content(self, text: str, math_fonts: set, total_chars: int) -> bool:
        """
        Enhanced detection of mathematical content using multiple criteria.
        
        Args:
            text: Text to analyze
            math_fonts: Set of mathematical fonts detected
            total_chars: Total character count
            
        Returns:
            True if content appears mathematical, False otherwise
        """
        if total_chars == 0:
            return False
        
        # Count mathematical indicators
        math_score = 0
        
        # 1. Mathematical symbols
        math_symbols_count = sum(1 for char in text if char in self.SYMBOL_TO_LATEX)
        if math_symbols_count > 0:
            math_score += min(3, math_symbols_count)
        
        # 2. Mathematical fonts
        if math_fonts:
            math_score += 2
        
        # 3. Mathematical patterns (equations, expressions)
        math_patterns = [
            r'[a-zA-Z]\s*[=]\s*[a-zA-Z0-9\(\)\+\-\*/\^\s]+',  # Variable assignments: x = ...
            r'[a-zA-Z]\s*[+-]\s*[a-zA-Z]',                     # Simple algebra: x + y, a - b
            r'[a-zA-Z][0-9]*\s*[\*/]\s*[a-zA-Z][0-9]*',       # Multiplication/division: xy, x*y, x/y
            r'[a-zA-Z][0-9]+',                                 # Subscripts: x1, R2
            r'[a-zA-Z]\^[0-9]+',                              # Exponents: x^2, y^3
            r'\([a-zA-Z0-9\+\-\*/\s]+\)',                     # Parenthetical expressions
            r'[0-9]+/[0-9]+',                                 # Fractions: 1/2, 3/4
            r'[A-Z]\s*[=]\s*',                                # Uppercase variables: R = , E = 
            r'[a-z]_[0-9a-z]+',                               # Subscripts: x_i, r_t
            r'\\[a-zA-Z]+',                                   # LaTeX commands
            r'[Pp]ortfolio|[Rr]eturn|[Vv]ariance|[Cc]ovariance|[Oo]ptim',  # Financial math terms
            r'[Ss]um|[Mm]aximum|[Mm]inimum|[Ee]xpected|[Mm]ean',  # Mathematical operations
        ]
        
        pattern_matches = 0
        for pattern in math_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                pattern_matches += 1
        
        if pattern_matches >= 2:
            math_score += 2
        elif pattern_matches == 1:
            math_score += 1
        
        # 4. Mathematical structure indicators
        structural_indicators = [
            '=',      # Equations
            '(',      # Parentheses
            '+', '-', # Basic operations
            '*', '/', # Multiplication/division
            '^',      # Exponentiation
            '_',      # Subscripts
        ]
        
        structure_count = sum(1 for indicator in structural_indicators if indicator in text)
        if structure_count >= 3:
            math_score += 2
        elif structure_count >= 2:
            math_score += 1
        
        # 5. Isolated mathematical expressions (short blocks with high math content)
        if total_chars < 100 and any(char.isalpha() and char in text for char in 'xyzijkmnpqr'):
            # Short blocks with common mathematical variables
            if any(op in text for op in ['=', '+', '-', '*', '/', '^', '(']):
                math_score += 2
        
        # 6. Check for ratio of non-space mathematical characters
        non_space_chars = len(text.replace(' ', ''))
        if non_space_chars > 0:
            math_char_ratio = (math_symbols_count + 
                             sum(1 for c in text if c in '=+-*/^()_0123456789')) / non_space_chars
            if math_char_ratio > 0.4:
                math_score += 2
            elif math_char_ratio > 0.2:
                math_score += 1
        
        # Decision threshold: configurable minimum score for mathematical content
        threshold = getattr(self, 'math_detection_threshold', 3)
        return math_score >= threshold
    
    def _calculate_math_confidence(self, text: str, math_fonts: set, total_chars: int) -> float:
        """
        Calculate confidence score for mathematical content detection.
        
        Args:
            text: Text content
            math_fonts: Mathematical fonts detected
            total_chars: Total character count
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        if total_chars == 0:
            return 0.0
        
        confidence = 0.0
        
        # Base confidence from mathematical symbols
        math_symbols_count = sum(1 for char in text if char in self.SYMBOL_TO_LATEX)
        symbol_ratio = math_symbols_count / total_chars
        confidence += min(0.4, symbol_ratio * 2)
        
        # Confidence from mathematical fonts
        if math_fonts:
            confidence += 0.3
        
        # Confidence from mathematical patterns
        equation_patterns = [r'[a-zA-Z]\s*=', r'[0-9]\s*=', r'=\s*[a-zA-Z0-9]']
        if any(re.search(pattern, text) for pattern in equation_patterns):
            confidence += 0.2
        
        # Confidence from mathematical structure
        math_ops = sum(1 for op in ['+', '-', '*', '/', '^', '(', ')'] if op in text)
        if math_ops >= 2:
            confidence += 0.2
        
        # Confidence from typical mathematical variables
        if any(var in text for var in ['x', 'y', 'z', 'R', 'r', 'w', 'E', 'V']):
            confidence += 0.1
        
        return min(1.0, confidence)
    
    def _convert_to_latex(self, text: str, math_fonts: set) -> str:
        """
        Convert mathematical text to LaTeX representation.
        
        Args:
            text: Text to convert
            math_fonts: Set of mathematical fonts detected
            
        Returns:
            LaTeX representation of the mathematical expression
        """
        latex = text
        
        # Replace known symbols with LaTeX equivalents
        for symbol, latex_cmd in self.SYMBOL_TO_LATEX.items():
            latex = latex.replace(symbol, latex_cmd)
        
        # Enhanced pattern conversion for text-based math
        
        # 1. Handle fractions more comprehensively
        latex = re.sub(r'(\w+)\s*/\s*(\w+)', r'\\frac{\1}{\2}', latex)  # x/y -> \frac{x}{y}
        latex = re.sub(r'(\d+)\s*/\s*(\d+)', r'\\frac{\1}{\2}', latex)  # 1/2 -> \frac{1}{2}
        
        # 2. Handle superscripts
        latex = re.sub(r'(\w+)\^(\d+)', r'\1^{\2}', latex)          # x^2 -> x^{2}
        latex = re.sub(r'(\w+)\^(\w+)', r'\1^{\2}', latex)          # x^n -> x^{n}
        latex = re.sub(r'(\w)(\d+)', r'\1_{\2}', latex)             # x1 -> x_{1} (subscripts)
        
        # 3. Handle subscripts
        latex = re.sub(r'(\w)_(\w+)', r'\1_{\2}', latex)            # x_i -> x_{i}
        
        # 4. Mathematical operations and spacing
        latex = re.sub(r'\s+\+\s+', ' + ', latex)                   # Normalize spacing around +
        latex = re.sub(r'\s+-\s+', ' - ', latex)                    # Normalize spacing around -
        latex = re.sub(r'\s*=\s*', ' = ', latex)                    # Normalize spacing around =
        
        # 5. Handle summation notation patterns
        latex = re.sub(r'[Ss]um\s+([a-zA-Z0-9_\^{}]+)', r'\\sum \1', latex)  # Sum x_i -> \sum x_i
        latex = re.sub(r'∑\s*([a-zA-Z])=([0-9]+)\s*([a-zA-Z])', r'\\sum_{\1=\2}^{\3}', latex)  # ∑i=1 n -> \sum_{i=1}^{n}
        
        # 6. Handle common mathematical functions
        latex = re.sub(r'\b(sin|cos|tan|log|ln|exp|max|min|E)\b', r'\\\1', latex)
        
        # 7. Handle matrix/vector notation
        latex = re.sub(r'\[([^\]]+)\]', r'\\begin{bmatrix} \1 \\end{bmatrix}', latex)
        
        # 8. Handle parentheses for grouping
        latex = re.sub(r'\(([^)]+)\)', r'(\1)', latex)  # Keep parentheses as-is
        
        # 9. Handle Greek letters spelled out
        greek_mapping = {
            'alpha': r'\\alpha', 'beta': r'\\beta', 'gamma': r'\\gamma', 'delta': r'\\delta',
            'epsilon': r'\\epsilon', 'theta': r'\\theta', 'lambda': r'\\lambda', 'mu': r'\\mu',
            'pi': r'\\pi', 'sigma': r'\\sigma', 'phi': r'\\phi', 'omega': r'\\omega'
        }
        for word, symbol in greek_mapping.items():
            latex = re.sub(rf'\b{word}\b', symbol, latex, flags=re.IGNORECASE)
        
        # 10. Clean up extra spaces
        latex = re.sub(r'\s+', ' ', latex).strip()
        
        # Wrap in math mode if it contains LaTeX commands or mathematical structure
        should_wrap = ('\\' in latex or 
                      any(op in latex for op in ['^', '_', '=']) or
                      any(word in latex.lower() for word in ['frac', 'sum', 'int']))
        
        if should_wrap and not latex.startswith('$'):
            latex = f'${latex}$'
        
        return latex
    
    def _determine_semantic_group(self, text: str) -> str:
        """
        Determine semantic grouping for mathematical expressions.
        
        Args:
            text: Mathematical text to analyze
            
        Returns:
            Semantic group identifier
        """
        text_lower = text.lower()
        
        # Portfolio/Finance mathematical expressions
        if any(term in text_lower for term in ['portfolio', 'return', 'variance', 'covariance', 'weight']):
            return "portfolio_theory"
        
        # Variable definitions (often contain equals signs with single variables)
        if re.match(r'^[a-zA-Z]\s*=', text.strip()):
            return "variable_definition"
        
        # Equations (more complex expressions with multiple operations)
        if text.count('=') == 1 and any(op in text for op in ['+', '-', '*', '/']):
            return "equation"
        
        # Ratios and fractions
        if '/' in text or any(word in text_lower for word in ['ratio', 'rate']):
            return "ratio"
        
        # Matrix and vector operations
        if any(symbol in text for symbol in ['∑', '∏', '∫']) or 'matrix' in text_lower:
            return "matrix_vector"
        
        # Probability and statistics
        if any(term in text_lower for term in ['prob', 'expected', 'variance', 'covariance']):
            return "statistics"
        
        # Default grouping
        return "general_math"
    
    def _group_related_math_blocks(self, math_blocks: List[MathBlock]) -> List[MathBlock]:
        """
        Group related mathematical expressions and establish cross-references.
        
        Args:
            math_blocks: List of mathematical blocks to group
            
        Returns:
            List of math blocks with enhanced cross-references
        """
        if not math_blocks:
            return math_blocks
        
        # Group blocks by semantic category
        semantic_groups = {}
        for block in math_blocks:
            group = block.semantic_group
            if group not in semantic_groups:
                semantic_groups[group] = []
            semantic_groups[group].append(block)
        
        # Establish relationships within semantic groups
        for group_name, blocks in semantic_groups.items():
            for i, block in enumerate(blocks):
                # Add references to other blocks in the same semantic group
                for other_block in blocks:
                    if other_block.block_id != block.block_id:
                        block.add_related_block(other_block.block_id)
                
                # Find blocks that reference similar variables
                block_vars = self._extract_variables(block.raw_text)
                for other_block in math_blocks:
                    if other_block.block_id != block.block_id:
                        other_vars = self._extract_variables(other_block.raw_text)
                        # If blocks share variables, they're likely related
                        if block_vars & other_vars:
                            block.add_related_block(other_block.block_id)
        
        return math_blocks
    
    def _extract_variables(self, text: str) -> set:
        """
        Extract mathematical variables from text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Set of variable names found
        """
        # Common mathematical variables
        variables = set()
        
        # Single letter variables (common in math)
        for match in re.finditer(r'\b[a-zA-Z]\b', text):
            variables.add(match.group())
        
        # Multi-character variables (like x0, x1, etc.)
        for match in re.finditer(r'\b[a-zA-Z][0-9]+\b', text):
            variables.add(match.group())
        
        # Greek letters written out
        greek_letters = ['alpha', 'beta', 'gamma', 'delta', 'sigma', 'mu', 'lambda']
        for letter in greek_letters:
            if letter in text.lower():
                variables.add(letter)
        
        return variables
    
    def _analyze_semantic_groups(self, all_math_blocks: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Analyze semantic groupings across all mathematical blocks.
        
        Args:
            all_math_blocks: List of all math blocks from document
            
        Returns:
            Dictionary mapping semantic groups to their counts
        """
        group_counts = {}
        for block_data in all_math_blocks:
            block = block_data.get('block', {})
            group = block.get('semantic_group', 'unknown')
            group_counts[group] = group_counts.get(group, 0) + 1
        
        return group_counts
    
    def _extract_math_image(self, page: fitz.Page, bbox: Tuple[float, float, float, float]) -> Optional[bytes]:
        """
        Extract mathematical formula as image for OCR processing.
        
        Args:
            page: PyMuPDF page object
            bbox: Bounding box of the mathematical region
            
        Returns:
            Image bytes or None if extraction fails
        """
        if not PIL_AVAILABLE:
            return None
        
        try:
            # Create a rect from bbox
            rect = fitz.Rect(bbox)
            
            # Get image of the math region
            mat = fitz.Matrix(2.0, 2.0)  # 2x zoom for better OCR quality
            pix = page.get_pixmap(matrix=mat, clip=rect)
            
            # Convert to PIL Image
            img_data = pix.tobytes("png")
            pix = None  # Cleanup
            
            return img_data
            
        except Exception as e:
            self.logger.warning(f"Failed to extract math image: {e}")
            return None
    
    def _ocr_math_formula(self, image_data: bytes) -> Optional[str]:
        """
        Use OCR to extract LaTeX from mathematical formula image.
        
        Args:
            image_data: Image bytes containing the formula
            
        Returns:
            LaTeX representation or None if OCR fails
        """
        if not self.openai_client:
            return None
        
        try:
            # Encode image for OpenAI
            base64_image = base64.b64encode(image_data).decode('utf-8')
            
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
                max_tokens=300
            )
            
            latex = response.choices[0].message.content.strip()
            if latex:
                self.logger.debug(f"OCR extracted LaTeX: {latex[:100]}")
                return latex
            
        except Exception as e:
            self.logger.warning(f"Math OCR failed: {e}")
        
        return None
    
    def extract_text(self, pdf_path: Path) -> str:
        """
        Extract text from a PDF file (compatibility method).
        
        This method provides backward compatibility with the original PDFIngestor.
        For enhanced mathematical formula extraction, use extract_text_with_math().
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text content from all pages
            
        Raises:
            Exception: If PDF cannot be opened or processed
        """
        if self.extract_math:
            text, _ = self.extract_text_with_math(pdf_path)
            return text
        else:
            # Original text extraction for backward compatibility
            return self._extract_text_simple(pdf_path)
    
    def _extract_text_simple(self, pdf_path: Path) -> str:
        """
        Simple text extraction without mathematical formula processing.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text content
        """
        try:
            doc = fitz.open(pdf_path)
            text_content = []
            empty_pages = []
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                # Extract text with reading order preserved if configured
                sort_text = self.config.get('preserve_reading_order', True)
                page_text = page.get_text(sort=sort_text)
                
                if not page_text.strip():
                    empty_pages.append(page_num + 1)
                    if self.config.get('warn_empty_pages', True):
                        self.logger.warning(f"Empty page found: {page_num + 1} in {pdf_path.name}")
                
                text_content.append(page_text)
            
            doc.close()
            
            if empty_pages and self.config.get('warn_empty_pages', True):
                file_name = pdf_path.name if hasattr(pdf_path, 'name') else str(pdf_path)
                self.logger.info(f"Document {file_name} has {len(empty_pages)} empty pages: {empty_pages}")
            
            return "\n".join(text_content)
            
        except Exception as e:
            self.logger.error(f"Error extracting text from {pdf_path}: {e}")
            raise
    
    def extract_text_with_math(self, pdf_path: Path) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Extract text and mathematical formulas from a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Tuple of (text_content, list_of_math_blocks)
            
        Raises:
            Exception: If PDF cannot be opened or processed
        """
        try:
            doc = fitz.open(pdf_path)
            text_content = []
            all_math_blocks = []
            empty_pages = []
            all_reference_maps = {}  # Store reference maps for each page
            document_char_offset = 0  # Track character position in full document
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                
                # Get raw dictionary for mathematical analysis
                page_dict = page.get_text("rawdict")
                
                # Extract regular text
                sort_text = self.config.get('preserve_reading_order', True)
                page_text = page.get_text(sort=sort_text)
                
                if not page_text.strip():
                    empty_pages.append(page_num + 1)
                    if self.config.get('warn_empty_pages', True):
                        self.logger.warning(f"Empty page found: {page_num + 1} in {pdf_path.name}")
                
                # Detect mathematical blocks if enabled
                page_math_blocks = []
                if self.extract_math:
                    # Use text-based detection with character offset tracking
                    page_math_blocks = self._detect_math_in_text(page_text, page_num + 1, document_char_offset)
                    
                    # Also try block-level detection as fallback
                    block_math_blocks = self._detect_math_blocks(page_dict)
                    if block_math_blocks:
                        # Update block-level math blocks with page info and positioning
                        for i, block in enumerate(block_math_blocks):
                            block.page_num = page_num + 1
                            block.block_id = f"math_p{page_num + 1}_bl{i}_{hash(block.raw_text) % 10000:04d}"
                            block.semantic_group = self._determine_semantic_group(block.raw_text)
                        page_math_blocks.extend(block_math_blocks)
                    
                    # Apply OCR fallback for low-confidence blocks
                    if self.math_ocr_fallback and self.openai_client:
                        for math_block in page_math_blocks:
                            if math_block.confidence < 0.7:
                                image_data = self._extract_math_image(page, math_block.bbox)
                                if image_data:
                                    ocr_latex = self._ocr_math_formula(image_data)
                                    if ocr_latex:
                                        math_block.latex = ocr_latex
                                        math_block.confidence = 0.9
                
                # Integrate math blocks into text with enhanced positioning
                if page_math_blocks:
                    integrated_text, reference_map = self._integrate_math_blocks(page_text, page_math_blocks)
                    text_content.append(integrated_text)
                    all_reference_maps[page_num + 1] = reference_map
                    all_math_blocks.extend([
                        {'page': page_num + 1, 'block': block.to_dict()} 
                        for block in page_math_blocks
                    ])
                else:
                    text_content.append(page_text)
                
                # Update document character offset for next page
                document_char_offset += len(page_text) + 1  # +1 for page separator
            
            # Store page count before closing document
            total_pages = len(doc)
            doc.close()
            
            if empty_pages and self.config.get('warn_empty_pages', True):
                file_name = pdf_path.name if hasattr(pdf_path, 'name') else str(pdf_path)
                self.logger.info(f"Document {file_name} has {len(empty_pages)} empty pages: {empty_pages}")
            
            if all_math_blocks:
                file_name = pdf_path.name if hasattr(pdf_path, 'name') else str(pdf_path)
                self.logger.info(f"Extracted {len(all_math_blocks)} mathematical blocks from {file_name}")
            
            # Create comprehensive document metadata with reference maps
            document_metadata = {
                'math_blocks': all_math_blocks,
                'reference_maps': all_reference_maps,
                'document_stats': {
                    'total_pages': total_pages,
                    'empty_pages': empty_pages,
                    'total_math_blocks': len(all_math_blocks),
                    'semantic_groups': self._analyze_semantic_groups(all_math_blocks)
                }
            }
            
            return "\n".join(text_content), document_metadata
            
        except Exception as e:
            self.logger.error(f"Error extracting text from {pdf_path}: {e}")
            raise
    
    def _integrate_math_blocks(self, text: str, math_blocks: List[MathBlock]) -> Tuple[str, Dict[str, Any]]:
        """
        Integrate mathematical blocks into the main text with enhanced contextual positioning.
        
        Args:
            text: Original page text
            math_blocks: List of mathematical blocks with positioning info
            
        Returns:
            Tuple of (enhanced text with bidirectional markers, reference mapping)
        """
        if not math_blocks:
            return text, {}
        
        # Create a reference mapping for bidirectional linking
        reference_map = {
            'math_to_text': {},  # math block ID -> text position
            'text_to_math': {},  # text position -> math block ID
            'semantic_groups': {}  # group -> list of block IDs
        }
        
        # Sort math blocks by their character position for proper insertion
        sorted_blocks = sorted(math_blocks, key=lambda b: b.char_start if b.char_start >= 0 else 0)
        
        # Build enhanced text with contextual markers
        enhanced_text = text
        offset = 0  # Track text length changes due to insertions
        
        for i, math_block in enumerate(sorted_blocks):
            # Create enhanced marker with bidirectional reference
            block_ref = f"MATHREF_{math_block.block_id}"
            
            if math_block.latex:
                marker = f"\n[{block_ref}] {math_block.latex}\n"
            else:
                marker = f"\n[{block_ref}] {math_block.raw_text}\n"
            
            # Add contextual information to marker
            context_info = ""
            if math_block.semantic_group:
                context_info += f" @group:{math_block.semantic_group}"
            if math_block.related_blocks:
                related_refs = [f"MATHREF_{bid}" for bid in math_block.related_blocks[:3]]  # Limit to avoid clutter
                context_info += f" @related:{','.join(related_refs)}"
            if math_block.confidence > 0:
                context_info += f" @confidence:{math_block.confidence:.2f}"
            
            if context_info:
                marker = marker.rstrip() + context_info + "\n"
            
            # Insert marker at contextually appropriate position
            insert_pos = self._find_contextual_insert_position(
                enhanced_text, math_block, offset
            )
            
            enhanced_text = enhanced_text[:insert_pos] + marker + enhanced_text[insert_pos:]
            
            # Update reference mapping
            reference_map['math_to_text'][math_block.block_id] = insert_pos + offset
            reference_map['text_to_math'][insert_pos + offset] = math_block.block_id
            
            # Update semantic groups mapping
            group = math_block.semantic_group
            if group not in reference_map['semantic_groups']:
                reference_map['semantic_groups'][group] = []
            reference_map['semantic_groups'][group].append(math_block.block_id)
            
            # Update offset for next insertion
            offset += len(marker)
        
        return enhanced_text, reference_map
    
    def _find_contextual_insert_position(self, text: str, math_block: MathBlock, offset: int) -> int:
        """
        Find the most appropriate position to insert a math block marker based on context.
        
        Args:
            text: Current text content
            math_block: Math block to insert
            offset: Current offset due to previous insertions
            
        Returns:
            Best insertion position
        """
        # If we have character positioning info, use it
        if math_block.char_start >= 0:
            # Adjust for previous insertions
            target_pos = math_block.char_start + offset
            # Ensure we don't go beyond text length
            return min(target_pos, len(text))
        
        # Fall back to line-based positioning
        if math_block.line_start >= 0:
            lines = text.split('\n')
            if math_block.line_start < len(lines):
                # Insert after the target line
                line_end_pos = sum(len(line) + 1 for line in lines[:math_block.line_start + 1])
                return min(line_end_pos, len(text))
        
        # Last resort: append to end
        return len(text)
    
    def extract_metadata(self, pdf_path: Path) -> Dict[str, Any]:
        """
        Extract metadata from a PDF file with improved DOI detection.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary containing PDF metadata
            
        Raises:
            Exception: If PDF cannot be opened or metadata cannot be extracted
        """
        try:
            doc = fitz.open(pdf_path)
            metadata = doc.metadata
            doc.close()
            
            # Clean and structure metadata
            clean_metadata = {
                'filename': pdf_path.name,
                'file_size': pdf_path.stat().st_size,
                'title': metadata.get('title', '').strip(),
                'author': metadata.get('author', '').strip(),
                'subject': metadata.get('subject', '').strip(),
                'creator': metadata.get('creator', '').strip(),
                'producer': metadata.get('producer', '').strip(),
                'creation_date': metadata.get('creationDate', '').strip(),
                'modification_date': metadata.get('modDate', '').strip(),
                'keywords': metadata.get('keywords', '').strip(),
            }
            
            # Enhanced DOI extraction using regex
            doi = self._extract_doi(clean_metadata)
            clean_metadata['doi'] = doi
            
            # Remove empty values
            clean_metadata = {k: v for k, v in clean_metadata.items() if v}
            
            return clean_metadata
            
        except Exception as e:
            self.logger.error(f"Error extracting metadata from {pdf_path}: {e}")
            raise
    
    def _extract_doi(self, metadata: Dict[str, Any]) -> str:
        """
        Extract DOI using regex patterns from metadata fields.
        
        Args:
            metadata: Metadata dictionary to search
            
        Returns:
            Extracted DOI string or empty string if not found
        """
        # Search in multiple fields
        search_fields = ['title', 'subject', 'keywords', 'author']
        
        for field in search_fields:
            field_value = metadata.get(field, '')
            if not field_value:
                continue
                
            # First try to find DOI with prefixes
            for prefix in self.doi_prefixes:
                if prefix.lower() in field_value.lower():
                    # Extract text after prefix
                    start_idx = field_value.lower().find(prefix.lower()) + len(prefix)
                    remaining_text = field_value[start_idx:].strip()
                    
                    # Apply regex to extract DOI
                    match = self.doi_pattern.search(remaining_text)
                    if match:
                        return match.group(0)
            
            # Also try direct regex search without prefix
            match = self.doi_pattern.search(field_value)
            if match:
                return match.group(0)
        
        return ''
    
    def save_text(self, text: str, pdf_path: Path) -> Path:
        """
        Save extracted text to a file.
        
        Args:
            text: Text content to save
            pdf_path: Original PDF file path (used to generate output filename)
            
        Returns:
            Path to the saved text file
        """
        output_path = self.text_dir / f"{pdf_path.stem}.txt"
        
        try:
            encoding = self.config.get('encoding', 'utf-8')
            with open(output_path, 'w', encoding=encoding) as f:
                f.write(text)
            
            self.logger.debug(f"Text saved to: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Error saving text for {pdf_path.name}: {e}")
            raise
    
    def save_math_blocks(self, math_blocks: List[Dict[str, Any]], pdf_path: Path) -> Optional[Path]:
        """
        Save mathematical blocks to a separate file.
        
        Args:
            math_blocks: List of mathematical blocks with metadata
            pdf_path: Original PDF file path
            
        Returns:
            Path to the saved math file or None if no math blocks
        """
        if not math_blocks or not self.separate_math_files:
            return None
        
        output_path = self.math_dir / f"{pdf_path.stem}.math"
        
        try:
            encoding = self.config.get('encoding', 'utf-8')
            indent = self.config.get('json_indent', 2)
            
            with open(output_path, 'w', encoding=encoding) as f:
                json.dump(math_blocks, f, indent=indent, ensure_ascii=False)
            
            self.logger.debug(f"Math blocks saved to: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Error saving math blocks for {pdf_path.name}: {e}")
            raise
    
    def save_reference_map(self, reference_maps: Dict[str, Any], pdf_path: Path) -> Optional[Path]:
        """
        Save bidirectional reference mapping between text and math blocks.
        
        Args:
            reference_maps: Reference mapping data for each page
            pdf_path: Original PDF file path
            
        Returns:
            Path to the saved reference file or None if no references
        """
        if not reference_maps:
            return None
        
        output_path = self.math_dir / f"{pdf_path.stem}.refs"
        
        try:
            encoding = self.config.get('encoding', 'utf-8')
            indent = self.config.get('json_indent', 2)
            
            with open(output_path, 'w', encoding=encoding) as f:
                json.dump(reference_maps, f, indent=indent, ensure_ascii=False)
            
            self.logger.debug(f"Saved reference mapping to {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Error saving reference mapping to {output_path}: {e}")
            return None
    
    def save_metadata(self, meta: Dict[str, Any], pdf_path: Path) -> Path:
        """
        Save metadata to a JSON file.
        
        Args:
            meta: Metadata dictionary to save
            pdf_path: Original PDF file path (used to generate output filename)
            
        Returns:
            Path to the saved JSON file
        """
        output_path = self.meta_dir / f"{pdf_path.stem}.json"
        
        try:
            encoding = self.config.get('encoding', 'utf-8')
            indent = self.config.get('json_indent', 2)
            
            with open(output_path, 'w', encoding=encoding) as f:
                json.dump(meta, f, indent=indent, ensure_ascii=False)
            
            self.logger.debug(f"Metadata saved to: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Error saving metadata for {pdf_path.name}: {e}")
            raise
    
    def _should_skip_file(self, pdf_path: Path) -> bool:
        """
        Check if file should be skipped based on existing outputs.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            True if file should be skipped, False otherwise
        """
        if not self.config.get('skip_existing', False):
            return False
            
        text_file = self.text_dir / f"{pdf_path.stem}.txt"
        meta_file = self.meta_dir / f"{pdf_path.stem}.json"
        math_file = self.math_dir / f"{pdf_path.stem}.math"
        
        required_files = [text_file, meta_file]
        if self.separate_math_files and self.extract_math:
            # Only require math file if math extraction is enabled
            return text_file.exists() and meta_file.exists()
        
        return all(f.exists() for f in required_files)
    
    def _process_single_pdf(self, pdf_path: Path) -> tuple[bool, str]:
        """
        Process a single PDF file with enhanced mathematical formula extraction.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            if self._should_skip_file(pdf_path):
                return True, f"Skipped (already processed): {pdf_path.name}"
            
            # Extract text, math blocks, and metadata
            if self.extract_math:
                text, document_metadata = self.extract_text_with_math(pdf_path)
                math_blocks = document_metadata.get('math_blocks', [])
                reference_maps = document_metadata.get('reference_maps', {})
                doc_stats = document_metadata.get('document_stats', {})
            else:
                text = self.extract_text(pdf_path)
                math_blocks = []
                reference_maps = {}
                doc_stats = {}
            
            metadata = self.extract_metadata(pdf_path)
            
            # Add enhanced math info to metadata
            if math_blocks:
                metadata['math_blocks_count'] = len(math_blocks)
                metadata['has_mathematical_content'] = True
                metadata['semantic_groups'] = doc_stats.get('semantic_groups', {})
                metadata['total_pages'] = doc_stats.get('total_pages', 0)
            
            # Save results
            self.save_text(text, pdf_path)
            self.save_metadata(metadata, pdf_path)
            
            if math_blocks and self.separate_math_files:
                self.save_math_blocks(math_blocks, pdf_path)
                # Save reference mapping file for bidirectional linking
                self.save_reference_map(reference_maps, pdf_path)
            
            math_info = f" (with {len(math_blocks)} math blocks)" if math_blocks else ""
            return True, f"Successfully processed: {pdf_path.name}{math_info}"
            
        except Exception as e:
            return False, f"Failed to process {pdf_path.name}: {e}"
    
    def process_all(self) -> None:
        """
        Process all PDF files in the input directory with enhanced math extraction.
        
        Iterates through all .pdf files in the input directory and processes
        each one by extracting text, mathematical formulas, and metadata.
        """
        pdf_files = list(self.input_dir.glob("*.pdf"))
        
        if not pdf_files:
            self.logger.warning(f"No PDF files found in {self.input_dir}")
            return
        
        self.logger.info(f"Found {len(pdf_files)} PDF files to process")
        if self.extract_math:
            self.logger.info("Enhanced mathematical formula extraction enabled")
        
        success_count = 0
        failure_count = 0
        total_math_blocks = 0
        
        # Determine if we should use parallel processing
        max_workers = self.config.get('parallel_workers', 1)
        use_parallel = max_workers > 1 and len(pdf_files) > 1
        
        # Setup progress bar if enabled
        show_progress = self.config.get('show_progress', True)
        progress_bar = tqdm(total=len(pdf_files), desc="Processing PDFs") if show_progress else None
        
        try:
            if use_parallel:
                self.logger.info(f"Using parallel processing with {max_workers} workers")
                
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    # Submit all tasks
                    future_to_path = {
                        executor.submit(self._process_single_pdf, pdf_path): pdf_path
                        for pdf_path in pdf_files
                    }
                    
                    # Process completed tasks
                    for future in as_completed(future_to_path):
                        success, message = future.result()
                        
                        if success:
                            success_count += 1
                            self.logger.info(message)
                            # Extract math block count from message
                            if "math blocks" in message:
                                count_match = re.search(r'(\d+) math blocks', message)
                                if count_match:
                                    total_math_blocks += int(count_match.group(1))
                        else:
                            failure_count += 1
                            self.logger.error(message)
                        
                        if progress_bar:
                            progress_bar.update(1)
            else:
                # Sequential processing
                for pdf_path in pdf_files:
                    success, message = self._process_single_pdf(pdf_path)
                    
                    if success:
                        success_count += 1
                        self.logger.info(message)
                        # Extract math block count from message
                        if "math blocks" in message:
                            count_match = re.search(r'(\d+) math blocks', message)
                            if count_match:
                                total_math_blocks += int(count_match.group(1))
                    else:
                        failure_count += 1
                        self.logger.error(message)
                    
                    if progress_bar:
                        progress_bar.update(1)
        
        finally:
            if progress_bar:
                progress_bar.close()
        
        # Final summary
        self.logger.info(f"Processing complete. Successes: {success_count}, Failures: {failure_count}")
        if total_math_blocks > 0:
            self.logger.info(f"Total mathematical blocks extracted: {total_math_blocks}")


# Alias for backward compatibility
PDFIngestorEnhanced = PDFIngestor


def load_config() -> Dict[str, Any]:
    """
    Load configuration from config.yaml file.
    
    Returns:
        Configuration dictionary
        
    Raises:
        FileNotFoundError: If config.yaml is not found
        yaml.YAMLError: If config.yaml is invalid
    """
    config_path = Path("config.yaml")
    
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    return config


def get_interactive_input(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get interactive input from user with config defaults.
    
    Args:
        config: Base configuration dictionary
        
    Returns:
        Updated configuration with user inputs
    """
    updated_config = config.copy()
    
    print("Enhanced PDF Ingestion Configuration")
    print("=" * 40)
    
    # Input directory
    default_input = config['input_dir']
    input_dir = input(f"Enter input directory [{default_input}]: ").strip()
    if input_dir:
        updated_config['input_dir'] = input_dir
    
    # Text output directory
    default_text = config['text_dir']
    text_dir = input(f"Enter text output directory [{default_text}]: ").strip()
    if text_dir:
        updated_config['text_dir'] = text_dir
    
    # Metadata directory
    default_meta = config['meta_dir']
    meta_dir = input(f"Enter metadata directory [{default_meta}]: ").strip()
    if meta_dir:
        updated_config['meta_dir'] = meta_dir
    
    # Math directory (if math extraction is enabled)
    if config.get('extract_math', True):
        default_math = config.get('math_dir', './data/math')
        math_dir = input(f"Enter math blocks directory [{default_math}]: ").strip()
        if math_dir:
            updated_config['math_dir'] = math_dir
    
    print()
    return updated_config


def main() -> None:
    """
    Command-line interface for enhanced PDFIngestor with mathematical formula support.
    """
    parser = argparse.ArgumentParser(
        description="Extract text, mathematical formulas, and metadata from PDF files",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        "--input-dir",
        type=Path,
        help="Directory containing PDF files to process"
    )
    
    parser.add_argument(
        "--text-dir",
        type=Path,
        help="Directory where extracted text files will be saved"
    )
    
    parser.add_argument(
        "--meta-dir",
        type=Path,
        help="Directory where metadata JSON files will be saved"
    )
    
    parser.add_argument(
        "--math-dir",
        type=Path,
        help="Directory where mathematical formula files will be saved"
    )
    
    parser.add_argument(
        "--config",
        type=Path,
        default="config.yaml",
        help="Path to configuration YAML file"
    )
    
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Run in non-interactive mode"
    )
    
    parser.add_argument(
        "--no-math",
        action="store_true",
        help="Disable mathematical formula extraction"
    )
    
    parser.add_argument(
        "--math-ocr",
        action="store_true",
        help="Enable math OCR fallback (requires OpenAI API key)"
    )
    
    # Mutually exclusive verbose/quiet group
    verbosity_group = parser.add_mutually_exclusive_group()
    verbosity_group.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output (DEBUG level logging)"
    )
    verbosity_group.add_argument(
        "--quiet", "-q", 
        action="store_true",
        help="Quiet mode (ERROR level logging only)"
    )
    
    args = parser.parse_args()
    
    try:
        # Load configuration
        config = load_config()
        
        # Validate configuration (optional)
        try:
            from .config_schema import validate_config
            validate_config(config)
        except ImportError:
            pass
        
        # Get interactive input if not in non-interactive mode
        if not args.non_interactive and not any([args.input_dir, args.text_dir, args.meta_dir]):
            config = get_interactive_input(config)
        
        # Override with command line arguments
        if args.input_dir:
            config['input_dir'] = str(args.input_dir)
        if args.text_dir:
            config['text_dir'] = str(args.text_dir)
        if args.meta_dir:
            config['meta_dir'] = str(args.meta_dir)
        if args.math_dir:
            config['math_dir'] = str(args.math_dir)
        
        # Handle math extraction options
        if args.no_math:
            config['extract_math'] = False
        if args.math_ocr:
            config['math_ocr_fallback'] = True
        
        # Handle verbosity overrides
        if args.verbose:
            config['log_level'] = 'DEBUG'
        elif args.quiet:
            config['log_level'] = 'ERROR'
        
        # Create and run the enhanced ingestor
        ingestor = PDFIngestor(config)
        ingestor.process_all()
        
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        print("Please ensure config.yaml exists in the current directory.", file=sys.stderr)
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error parsing configuration file: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()