#!/usr/bin/env python3
"""
Test script for enhanced metadata extraction functionality.
"""

import re
from typing import List

class SimpleSettings:
    """Simple settings class for testing."""
    pass

class EnhancedMetadataExtractor:
    """
    Enhanced metadata extractor for complexity levels, prerequisites, and domain classification.
    """
    
    def __init__(self, settings):
        """Initialize the enhanced metadata extractor."""
        self.settings = settings
        
        # Complexity level indicators
        self.complexity_indicators = {
            'beginner': [
                re.compile(r'introduction\s+to|basic|fundamental|elementary|simple', re.IGNORECASE),
                re.compile(r'primer|overview|getting\s+started|basics', re.IGNORECASE),
                re.compile(r'introductory|elementary|simple\s+example', re.IGNORECASE),
            ],
            'intermediate': [
                re.compile(r'intermediate|moderate|standard|typical', re.IGNORECASE),
                re.compile(r'application|practical|implementation', re.IGNORECASE),
                re.compile(r'case\s+study|real.world|empirical', re.IGNORECASE),
            ],
            'advanced': [
                re.compile(r'advanced|sophisticated|complex|rigorous', re.IGNORECASE),
                re.compile(r'theoretical|mathematical\s+proof|derivation', re.IGNORECASE),
                re.compile(r'research|cutting.edge|state.of.the.art', re.IGNORECASE),
                re.compile(r'phd|doctoral|graduate.level', re.IGNORECASE),
            ]
        }
        
        # Mathematical complexity indicators
        self.math_complexity_patterns = [
            # Advanced: Multiple integrals, differential equations
            (re.compile(r'∫∫|∭|∂²|∇²|differential\s+equation'), 'advanced'),
            # Advanced: Matrix operations, eigenvalues
            (re.compile(r'eigenvalue|eigenvector|matrix\s+inverse|determinant'), 'advanced'),
            # Intermediate: Single integrals, derivatives
            (re.compile(r'∫|∂|derivative|integral'), 'intermediate'),
            # Intermediate: Summations, products
            (re.compile(r'∑|∏|summation|product'), 'intermediate'),
            # Beginner: Basic arithmetic operations
            (re.compile(r'[+\-*/=]|arithmetic|calculation'), 'beginner'),
        ]
        
        # Prerequisite indicators
        self.prerequisite_patterns = [
            re.compile(r'assumes?\s+(?:familiarity\s+with|knowledge\s+of|understanding\s+of)\s+([^.,;]+)', re.IGNORECASE),
            re.compile(r'requires?\s+(?:knowledge\s+of|understanding\s+of|familiarity\s+with)\s+([^.,;]+)', re.IGNORECASE),
            re.compile(r'builds?\s+(?:on|upon)\s+([^.,;]+)', re.IGNORECASE),
            re.compile(r'based\s+on\s+([^.,;]+)', re.IGNORECASE),
            re.compile(r'given\s+(?:knowledge\s+of|understanding\s+of)\s+([^.,;]+)', re.IGNORECASE),
            re.compile(r'prerequisite[s]?\s*:\s*([^.,;]+)', re.IGNORECASE),
            re.compile(r'background\s+in\s+([^.,;]+)', re.IGNORECASE),
        ]
        
        # Domain classification patterns
        self.domain_patterns = {
            'mathematics': [
                re.compile(r'mathematical|theorem|proof|lemma|corollary', re.IGNORECASE),
                re.compile(r'algebra|calculus|statistics|probability|geometry', re.IGNORECASE),
                re.compile(r'analysis|topology|number\s+theory', re.IGNORECASE),
            ],
            'finance': [
                re.compile(r'financial|portfolio|investment|trading|market', re.IGNORECASE),
                re.compile(r'asset|security|bond|stock|option|derivative', re.IGNORECASE),
                re.compile(r'risk\s+management|capital|banking|hedge', re.IGNORECASE),
            ],
            'economics': [
                re.compile(r'economic|economy|econometric|microeconomic|macroeconomic', re.IGNORECASE),
                re.compile(r'supply|demand|market\s+equilibrium|elasticity', re.IGNORECASE),
                re.compile(r'gdp|inflation|monetary|fiscal|policy', re.IGNORECASE),
            ],
            'statistics': [
                re.compile(r'statistical|regression|correlation|hypothesis', re.IGNORECASE),
                re.compile(r'distribution|normal|gaussian|chi.square|t.test', re.IGNORECASE),
                re.compile(r'confidence\s+interval|p.value|significance', re.IGNORECASE),
            ],
            'optimization': [
                re.compile(r'optimization|minimize|maximize|constraint|lagrange', re.IGNORECASE),
                re.compile(r'linear\s+programming|quadratic\s+programming|convex', re.IGNORECASE),
                re.compile(r'objective\s+function|feasible\s+region|optimal', re.IGNORECASE),
            ]
        }
    
    def extract_complexity_level(self, text: str, context: str = "") -> str:
        """Extract complexity level from document text and context."""
        full_text = f"{context} {text}".lower()
        
        # Score based on indicators
        scores = {'beginner': 0, 'intermediate': 0, 'advanced': 0}
        
        # Check textual indicators
        for level, patterns in self.complexity_indicators.items():
            for pattern in patterns:
                matches = len(pattern.findall(full_text))
                scores[level] += matches
        
        # Check mathematical complexity
        for pattern, level in self.math_complexity_patterns:
            matches = len(pattern.findall(text))
            scores[level] += matches * 2  # Weight math patterns higher
        
        # Additional heuristics
        # Length-based complexity (longer derivations tend to be more advanced)
        if len(text) > 2000:
            scores['advanced'] += 1
        elif len(text) < 500:
            scores['beginner'] += 1
        
        # Equation density
        math_symbols = len(re.findall(r'[∫∂∑∏√±≤≥≠∞∈∉⊂⊆∪∩]', text))
        if math_symbols > 20:
            scores['advanced'] += 2
        elif math_symbols > 5:
            scores['intermediate'] += 1
        
        # Return level with highest score, default to intermediate
        if scores['advanced'] > scores['intermediate'] and scores['advanced'] > scores['beginner']:
            return 'advanced'
        elif scores['beginner'] > scores['intermediate']:
            return 'beginner'
        else:
            return 'intermediate'  # Default for financial mathematics
    
    def extract_prerequisites(self, text: str, ontology=None) -> List[str]:
        """Extract prerequisite concepts from document text."""
        prerequisites = set()
        
        for pattern in self.prerequisite_patterns:
            matches = pattern.findall(text)
            for match in matches:
                # Clean up the matched text
                prereq_text = match.strip().rstrip('.,;')
                prerequisites.add(prereq_text)
        
        return list(prerequisites)
    
    def extract_domain(self, text: str, context: str = "") -> str:
        """Extract domain classification from document text and context."""
        full_text = f"{context} {text}".lower()
        
        # Score each domain
        domain_scores = {}
        for domain, patterns in self.domain_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(pattern.findall(full_text))
                score += matches
            domain_scores[domain] = score
        
        # Return domain with highest score, default to finance
        if domain_scores:
            max_domain = max(domain_scores, key=domain_scores.get)
            if domain_scores[max_domain] > 0:
                return max_domain
        
        return 'finance'  # Default for financial mathematics corpus


def test_enhanced_metadata_extractor():
    """Test the enhanced metadata extraction functionality."""
    
    print("=== Enhanced Metadata Extractor Test ===")
    print()
    
    # Create extractor
    settings = SimpleSettings()
    extractor = EnhancedMetadataExtractor(settings)
    print("✓ Enhanced metadata extractor created successfully!")
    print()
    
    # Test cases
    test_cases = [
        {
            'name': 'Advanced Mathematical Text',
            'text': 'This is an advanced mathematical derivation involving complex integrals ∫∫ and eigenvalue decomposition. The proof requires sophisticated theoretical knowledge.',
            'expected_complexity': 'advanced',
            'expected_domain': 'mathematics'
        },
        {
            'name': 'Finance Portfolio Text',
            'text': 'This paper discusses portfolio optimization and risk management in financial markets. We examine asset allocation strategies for investment portfolios.',
            'expected_complexity': 'intermediate',
            'expected_domain': 'finance'
        },
        {
            'name': 'Beginner Introduction',
            'text': 'This is a basic introduction to fundamental concepts in finance. Simple examples demonstrate basic arithmetic calculations.',
            'expected_complexity': 'beginner',
            'expected_domain': 'finance'
        },
        {
            'name': 'Prerequisites Text',
            'text': 'This method assumes familiarity with linear algebra and requires knowledge of probability theory. The approach builds on matrix theory.',
            'expected_complexity': 'intermediate',
            'expected_domain': 'mathematics'
        }
    ]
    
    # Run tests
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test {i}: {test_case['name']}")
        print(f"Text: {test_case['text'][:80]}...")
        print()
        
        # Test complexity extraction
        complexity = extractor.extract_complexity_level(test_case['text'])
        print(f"Detected complexity: {complexity}")
        complexity_match = "✓" if complexity == test_case['expected_complexity'] else "✗"
        print(f"Expected complexity: {test_case['expected_complexity']} {complexity_match}")
        print()
        
        # Test domain extraction
        domain = extractor.extract_domain(test_case['text'])
        print(f"Detected domain: {domain}")
        domain_match = "✓" if domain == test_case['expected_domain'] else "✗"
        print(f"Expected domain: {test_case['expected_domain']} {domain_match}")
        print()
        
        # Test prerequisite extraction
        prereqs = extractor.extract_prerequisites(test_case['text'])
        print(f"Detected prerequisites: {prereqs}")
        print()
        
        print("-" * 60)
        print()
    
    print("=== Integration Test Complete ===")


if __name__ == "__main__":
    test_enhanced_metadata_extractor()