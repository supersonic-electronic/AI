#!/usr/bin/env python3

import sys
sys.path.append('.')

from src.knowledge.utils import (
    normalize_concept_name,
    generate_cache_key,
    get_concept_variants,
    is_valid_concept_name
)

def test_normalize_concept_name():
    """Test concept name normalization."""
    print("Testing normalize_concept_name...")
    
    # Basic tests
    assert normalize_concept_name("CAPM") == "capm"
    assert normalize_concept_name("  CAPM  ") == "capm"
    assert normalize_concept_name("Black-Scholes") == "black-scholes"
    assert normalize_concept_name("Capital  Asset   Pricing") == "capital asset pricing"
    assert normalize_concept_name("CAPM.") == "capm"
    
    # Edge cases
    assert normalize_concept_name("") == ""
    assert normalize_concept_name("   ") == ""
    
    # Consistency test
    inputs = ["CAPM", "capm", "Capm", "  CAPM  ", "capm."]
    normalized = [normalize_concept_name(inp) for inp in inputs]
    assert all(norm == "capm" for norm in normalized)
    
    print("✓ normalize_concept_name tests passed")

def test_generate_cache_key():
    """Test cache key generation."""
    print("Testing generate_cache_key...")
    
    key = generate_cache_key("DBpediaConnector", "CAPM")
    assert key == "dbpediaconnector_capm"
    
    # Test normalization consistency
    key1 = generate_cache_key("DBpediaConnector", "CAPM")
    key2 = generate_cache_key("DBpediaConnector", "capm")
    key3 = generate_cache_key("DBpediaConnector", "  Capm  ")
    assert key1 == key2 == key3
    
    print("✓ generate_cache_key tests passed")

def test_get_concept_variants():
    """Test concept variant generation."""
    print("Testing get_concept_variants...")
    
    variants = get_concept_variants("CAPM")
    expected = {"capm", "CAPM", "Capm", "capital asset pricing model"}
    assert variants == expected
    
    variants_var = get_concept_variants("VAR")
    assert "value at risk" in variants_var
    assert "var" in variants_var
    
    print("✓ get_concept_variants tests passed")

def test_is_valid_concept_name():
    """Test concept name validation."""
    print("Testing is_valid_concept_name...")
    
    assert is_valid_concept_name("CAPM") is True
    assert is_valid_concept_name("Black-Scholes") is True
    assert is_valid_concept_name("") is False
    assert is_valid_concept_name("   ") is False
    assert is_valid_concept_name("a") is False  # Too short
    
    print("✓ is_valid_concept_name tests passed")

def test_integration():
    """Test integration scenarios."""
    print("Testing integration scenarios...")
    
    # End-to-end test
    concept_name = "  CAPM.  "
    normalized = normalize_concept_name(concept_name)
    assert normalized == "capm"
    
    cache_key = generate_cache_key("DBpediaConnector", concept_name)
    assert cache_key == "dbpediaconnector_capm"
    
    variants = get_concept_variants(concept_name)
    assert "capital asset pricing model" in variants
    assert "capm" in variants
    
    # Case consistency test
    test_cases = [
        ("CAPM", "capm", "Capm"),
        ("BLACK-SCHOLES", "black-scholes", "Black-Scholes"),
    ]
    
    for case_variants in test_cases:
        normalized_values = [normalize_concept_name(variant) for variant in case_variants]
        assert len(set(normalized_values)) == 1
        
        cache_keys = [generate_cache_key("TestConnector", variant) for variant in case_variants]
        assert len(set(cache_keys)) == 1
    
    print("✓ Integration tests passed")

if __name__ == '__main__':
    test_normalize_concept_name()
    test_generate_cache_key()
    test_get_concept_variants()
    test_is_valid_concept_name()
    test_integration()
    print("\n🎉 All utility function tests passed!")