#!/usr/bin/env python3
"""
Analysis of mathematical content detection issues and improvements.

This script analyzes the current math detection problems and demonstrates
the improvements without requiring the full environment setup.
"""

import re
from typing import Dict, List, Tuple


class OriginalMathDetector:
    """Simplified version of the original math detector to show issues."""
    
    def __init__(self):
        self.math_detection_threshold = 3  # Original low threshold
        self._compile_patterns()
    
    def _compile_patterns(self):
        # Original patterns (too permissive)
        self.math_symbols_pattern = re.compile(
            r'[∫∑∏∂∇∞≤≥≠≈±∓×÷∘√αβγδεζηθλμπρστφχψωΓΔΘΛΠΣΦΨΩ]'
        )
        self.equation_patterns = [
            re.compile(r'[a-zA-Z_]\w*\s*=\s*[^=]'),
            re.compile(r'[0-9]+\s*=\s*[^=]'),
            re.compile(r'=\s*[a-zA-Z0-9_]'),
        ]
        self.operator_pattern = re.compile(r'[+\-*/^()[\]{}|]')
    
    def detect_mathematical_content(self, text: str) -> Tuple[bool, float, Dict]:
        if not text.strip():
            return False, 0.0, {}
        
        score = 0.0
        breakdown = {}
        
        # Mathematical symbols
        symbol_matches = len(self.math_symbols_pattern.findall(text))
        symbol_score = min(3.0, symbol_matches * 0.5)
        score += symbol_score
        breakdown['symbols'] = symbol_matches
        
        # Equation patterns
        equation_score = 0.0
        for pattern in self.equation_patterns:
            if pattern.search(text):
                equation_score += 1.0
        equation_score = min(2.0, equation_score)
        score += equation_score
        breakdown['equations'] = int(equation_score)
        
        # Mathematical operators
        operator_matches = len(self.operator_pattern.findall(text))
        operator_score = min(2.0, operator_matches * 0.2)
        score += operator_score
        breakdown['operators'] = operator_matches
        
        # Variables (too permissive)
        variable_matches = len(re.findall(r'\b[a-zA-Z]\b', text))
        variable_score = min(1.5, variable_matches * 0.1)
        score += variable_score
        breakdown['variables'] = variable_matches
        
        confidence = min(1.0, score / 10.0)
        is_mathematical = score >= self.math_detection_threshold
        
        return is_mathematical, confidence, breakdown


class ImprovedMathDetector:
    """Improved math detector with better precision."""
    
    def __init__(self):
        self.math_detection_threshold = 6  # Higher threshold
        self.min_math_length = 3
        self._compile_patterns()
    
    def _compile_patterns(self):
        # Enhanced patterns
        self.math_symbols_pattern = re.compile(
            r'[∫∑∏∂∇∞≤≥≠≈±∓×÷∘√αβγδεζηθλμπρστφχψωΓΔΘΛΠΣΦΨΩ]'
        )
        
        # More specific equation patterns
        self.equation_patterns = [
            re.compile(r'[a-zA-Z_][a-zA-Z0-9_]*\s*=\s*[a-zA-Z0-9_+\-*/()^√∫∑∏∂∇∞≤≥≠≈±∓×÷∘αβγδεζηθλμπρστφχψωΓΔΘΛΠΣΦΨΩ\s]+'),
            re.compile(r'[a-zA-Z_][a-zA-Z0-9_]*\s*[+\-*/^]\s*[a-zA-Z0-9_]+'),
            re.compile(r'[a-zA-Z0-9_+\-*/()^]+/[a-zA-Z0-9_+\-*/()^]+'),
        ]
        
        # Rejection patterns
        self.rejection_patterns = [
            re.compile(r'^\s*\d+\s*$'),  # Page numbers
            re.compile(r'^\s*\[\s*\d+\s*\]\s*$'),  # Citations
            re.compile(r'^\s*[a-zA-Z]\d*\s*$'),  # Single variables
            re.compile(r'^\s*\d+\.\s*[A-Z][a-zA-Z\s]+$'),  # Section headers
            re.compile(r'\b(page|section|chapter|figure|table|equation|example)\s+\d+\b', re.IGNORECASE),
            re.compile(r'^[A-Z]{2,5}$'),  # Stock symbols
        ]
        
        self.operator_pattern = re.compile(r'[+\-*/^()=[\]{}|<>≤≥≠≈±∓×÷∘]')
    
    def _should_reject_text(self, text: str) -> bool:
        text_stripped = text.strip()
        
        # Check rejection patterns
        for pattern in self.rejection_patterns:
            if pattern.search(text_stripped):
                return True
        
        # Reject very short text
        if len(text_stripped) < self.min_math_length:
            return True
        
        # Reject mostly alphabetic text
        if len(text_stripped) > 10:
            alpha_count = sum(1 for c in text_stripped if c.isalpha())
            if alpha_count / len(text_stripped) > 0.8:
                return True
        
        return False
    
    def detect_mathematical_content(self, text: str) -> Tuple[bool, float, Dict]:
        if not text.strip():
            return False, 0.0, {}
        
        # Quick rejection
        if self._should_reject_text(text):
            return False, 0.0, {'rejected': 1}
        
        score = 0.0
        breakdown = {}
        
        # Mathematical symbols (higher weight)
        symbol_matches = len(self.math_symbols_pattern.findall(text))
        if symbol_matches > 0:
            symbol_score = min(4.0, symbol_matches * 0.8)
            score += symbol_score
            breakdown['symbols'] = symbol_matches
        
        # Enhanced equation patterns
        equation_score = 0.0
        for pattern in self.equation_patterns:
            if pattern.search(text):
                equation_score += 2.0
                break
        score += equation_score
        breakdown['equations'] = int(equation_score / 2)
        
        # Operators (require at least 2)
        operator_matches = len(self.operator_pattern.findall(text))
        if operator_matches >= 2:
            operator_score = min(2.0, operator_matches * 0.3)
            score += operator_score
            breakdown['operators'] = operator_matches
        
        # Length penalty for short expressions
        if len(text.strip()) < self.min_math_length:
            score *= 0.5
        
        # Multi-line bonus
        if '\n' in text and len(text.strip()) > 20:
            score += 1.0
            breakdown['multiline_bonus'] = 1
        
        confidence = min(1.0, score / 12.0)
        is_mathematical = score >= self.math_detection_threshold
        
        return is_mathematical, confidence, breakdown


def analyze_current_issues():
    """Analyze the issues with current mathematical detection."""
    
    print("Analysis of Current Mathematical Detection Issues")
    print("=" * 60)
    
    # Examples from the actual math files
    problematic_cases = [
        "Markowitz Mean-Variance Portfolio Theory",  # Document title
        "x1",  # Single variable
        "R =",  # Incomplete equation
        "x0",  # Another single variable
        "to short (or short sell) a particular stock XXX",  # Regular text
        "Page 5",  # Page number
        "[1]",  # Citation
        "1. Introduction",  # Section header
    ]
    
    real_math_cases = [
        "E(R_p) = w'μ",  # Expected return formula
        "σ² = w'Σw",  # Variance formula
        "x₁ = Rx₀ and x₁ = (1 + r)x₀",  # Return equations
        "∫f(x)dx",  # Integral
        "∑(i=1 to n) wi = 1",  # Summation
    ]
    
    original_detector = OriginalMathDetector()
    
    print("\nProblematic Cases (should NOT be detected as math):")
    print("-" * 50)
    false_positives = 0
    
    for text in problematic_cases:
        is_math, conf, breakdown = original_detector.detect_mathematical_content(text)
        if is_math:
            false_positives += 1
        status = "DETECTED ❌" if is_math else "Rejected ✅"
        print(f"{text[:40]:<42} {status} (conf: {conf:.2f})")
    
    print(f"\nFalse positives: {false_positives}/{len(problematic_cases)}")
    
    print("\nReal Mathematical Cases (should be detected):")
    print("-" * 50)
    true_positives = 0
    
    for text in real_math_cases:
        is_math, conf, breakdown = original_detector.detect_mathematical_content(text)
        if is_math:
            true_positives += 1
        status = "DETECTED ✅" if is_math else "Missed ❌"
        print(f"{text[:40]:<42} {status} (conf: {conf:.2f})")
    
    print(f"\nTrue positives: {true_positives}/{len(real_math_cases)}")
    
    # Calculate precision and recall
    total_detected = false_positives + true_positives
    precision = true_positives / total_detected if total_detected > 0 else 0
    recall = true_positives / len(real_math_cases)
    
    print(f"\nOriginal Detector Performance:")
    print(f"Precision: {precision:.2%}")
    print(f"Recall: {recall:.2%}")
    
    return false_positives, true_positives


def compare_detectors():
    """Compare original vs improved detectors."""
    
    print("\n\nComparison: Original vs Improved Detector")
    print("=" * 60)
    
    test_cases = [
        # Real math (should be detected)
        ("E(R_p) = w'μ", "Real math"),
        ("σ² = w'Σw", "Real math"),
        ("x₁ = Rx₀ and x₁ = (1 + r)x₀", "Real math"),
        ("∫f(x)dx from a to b", "Real math"),
        ("∑(i=1 to n) wixi = 1", "Real math"),
        ("max{w'μ - (λ/2)w'Σw}", "Real math"),
        
        # False positives (should NOT be detected)
        ("x1", "Single var"),
        ("R =", "Incomplete"),
        ("Page 5", "Page number"),
        ("[1]", "Citation"),
        ("XXX", "Stock symbol"),
        ("1. Introduction", "Section header"),
        ("Markowitz Mean-Variance Portfolio Theory", "Title"),
        ("to short (or short sell) a particular stock XXX", "Regular text"),
    ]
    
    original = OriginalMathDetector()
    improved = ImprovedMathDetector()
    
    print(f"{'Text':<45} {'Original':<12} {'Improved':<12} {'Type'}")
    print("-" * 80)
    
    orig_detections = 0
    impr_detections = 0
    
    for text, text_type in test_cases:
        is_math_orig, conf_orig, _ = original.detect_mathematical_content(text)
        is_math_impr, conf_impr, _ = improved.detect_mathematical_content(text)
        
        if is_math_orig:
            orig_detections += 1
        if is_math_impr:
            impr_detections += 1
        
        orig_result = f"✓ ({conf_orig:.2f})" if is_math_orig else f"✗ ({conf_orig:.2f})"
        impr_result = f"✓ ({conf_impr:.2f})" if is_math_impr else f"✗ ({conf_impr:.2f})"
        
        print(f"{text[:43]:<45} {orig_result:<12} {impr_result:<12} {text_type}")
    
    print("-" * 80)
    print(f"Total detections: Original={orig_detections}, Improved={impr_detections}")
    
    # Calculate improvement
    real_math_count = 6  # First 6 are real math
    orig_fp = max(0, orig_detections - real_math_count)
    impr_fp = max(0, impr_detections - real_math_count)
    
    print(f"\nFalse positive reduction: {orig_fp - impr_fp}")
    
    if orig_detections > 0:
        orig_precision = min(real_math_count, orig_detections) / orig_detections
        print(f"Original precision: {orig_precision:.2%}")
    
    if impr_detections > 0:
        impr_precision = min(real_math_count, impr_detections) / impr_detections
        print(f"Improved precision: {impr_precision:.2%}")


def provide_solutions():
    """Provide solutions and recommendations."""
    
    print("\n\nSolutions and Recommendations")
    print("=" * 40)
    
    print("\n1. Immediate Fixes (No OCR Required):")
    print("   - Increase math_detection_threshold from 3 to 6+")
    print("   - Use the improved math detector")
    print("   - Add rejection patterns for common false positives")
    print("   - Require minimum expression length (3+ characters)")
    print("   - Require multiple operators for mathematical detection")
    
    print("\n2. Configuration Changes:")
    print("   - Set math_detection_threshold: 6 in config.yaml")
    print("   - Use config-improved-math.yaml as template")
    print("   - Enable debug logging to monitor detections")
    
    print("\n3. OCR Configuration (for complex formulas):")
    print("   - Mathpix: Get app_id and app_key from mathpix.com")
    print("   - OpenAI: Get API key from platform.openai.com")
    print("   - Set environment variables or config file")
    print("   - Enable math_ocr_fallback: true")
    
    print("\n4. Testing Commands:")
    print("   - Test with improved config:")
    print("     python -m src.cli ingest --config config-improved-math.yaml")
    print("   - Enable OCR fallback:")
    print("     python -m src.cli ingest --math-ocr --verbose")
    print("   - Compare results:")
    print("     Check confidence scores in generated .math files")


def main():
    """Main analysis function."""
    analyze_current_issues()
    compare_detectors()
    provide_solutions()


if __name__ == "__main__":
    main()