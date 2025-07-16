"""
Tests for concept normalization utility functions.
"""

import pytest
from src.knowledge.utils import (
    normalize_concept_name,
    generate_cache_key,
    get_concept_variants,
    is_valid_concept_name
)


class TestNormalizeConceptName:
    """Test concept name normalization."""
    
    def test_basic_normalization(self):
        """Test basic lowercase and strip functionality."""
        assert normalize_concept_name("CAPM") == "capm"
        assert normalize_concept_name("  CAPM  ") == "capm"
        assert normalize_concept_name("Black-Scholes") == "black-scholes"
        
    def test_whitespace_normalization(self):
        """Test whitespace handling."""
        assert normalize_concept_name("Capital  Asset   Pricing") == "capital asset pricing"
        assert normalize_concept_name("\t\nCAPM\t\n") == "capm"
        
    def test_punctuation_handling(self):
        """Test trailing punctuation removal."""
        assert normalize_concept_name("CAPM.") == "capm"
        assert normalize_concept_name("Alpha,") == "alpha"
        assert normalize_concept_name("Beta;") == "beta"
        assert normalize_concept_name("Variance:") == "variance"
        
    def test_special_characters(self):
        """Test handling of special characters."""
        assert normalize_concept_name("α (Alpha)") == "α (alpha)"
        assert normalize_concept_name("β-value") == "β-value"
        
    def test_edge_cases(self):
        """Test edge cases and invalid inputs."""
        assert normalize_concept_name("") == ""
        assert normalize_concept_name(None) == ""
        assert normalize_concept_name("   ") == ""
        
    def test_consistency(self):
        """Test that normalization is consistent."""
        inputs = ["CAPM", "capm", "Capm", "  CAPM  ", "capm."]
        normalized = [normalize_concept_name(inp) for inp in inputs]
        assert all(norm == "capm" for norm in normalized)


class TestGenerateCacheKey:
    """Test cache key generation."""
    
    def test_basic_cache_key(self):
        """Test basic cache key generation."""
        key = generate_cache_key("DBpediaConnector", "CAPM")
        assert key == "dbpediaconnector_capm"
        
    def test_connector_normalization(self):
        """Test connector name normalization."""
        key1 = generate_cache_key("DBpediaConnector", "CAPM")
        key2 = generate_cache_key("dbpediaconnector", "CAPM")
        key3 = generate_cache_key("DBPEDIACONNECTOR", "CAPM")
        assert key1 == key2 == key3
        
    def test_concept_normalization(self):
        """Test concept name normalization in cache keys."""
        key1 = generate_cache_key("DBpediaConnector", "CAPM")
        key2 = generate_cache_key("DBpediaConnector", "capm")
        key3 = generate_cache_key("DBpediaConnector", "  Capm  ")
        assert key1 == key2 == key3
        
    def test_special_characters_in_cache_key(self):
        """Test cache keys with special characters."""
        key = generate_cache_key("WikidataConnector", "Black-Scholes")
        assert key == "wikidataconnector_black-scholes"


class TestGetConceptVariants:
    """Test concept variant generation."""
    
    def test_basic_variants(self):
        """Test basic variant generation."""
        variants = get_concept_variants("CAPM")
        expected = {"capm", "CAPM", "Capm", "capital asset pricing model"}
        assert variants == expected
        
    def test_acronym_expansion(self):
        """Test financial acronym expansion."""
        variants = get_concept_variants("VAR")
        assert "value at risk" in variants
        assert "var" in variants
        
    def test_non_acronym(self):
        """Test non-acronym concept variants."""
        variants = get_concept_variants("Portfolio")
        assert "portfolio" in variants
        assert "PORTFOLIO" in variants
        assert "Portfolio" in variants
        
    def test_no_duplicates(self):
        """Test that variants don't contain duplicates."""
        variants = get_concept_variants("test")
        assert len(variants) == len(set(variants))
        
    def test_empty_strings_filtered(self):
        """Test that empty strings are filtered out."""
        variants = get_concept_variants("   ")
        assert "" not in variants


class TestIsValidConceptName:
    """Test concept name validation."""
    
    def test_valid_names(self):
        """Test valid concept names."""
        assert is_valid_concept_name("CAPM") is True
        assert is_valid_concept_name("Black-Scholes") is True
        assert is_valid_concept_name("Portfolio Theory") is True
        
    def test_invalid_names(self):
        """Test invalid concept names."""
        assert is_valid_concept_name("") is False
        assert is_valid_concept_name(None) is False
        assert is_valid_concept_name("   ") is False
        assert is_valid_concept_name("a") is False  # Too short
        
    def test_length_limits(self):
        """Test concept name length validation."""
        # Just at the limit
        assert is_valid_concept_name("ab") is True
        assert is_valid_concept_name("a" * 200) is True
        
        # Over the limit
        assert is_valid_concept_name("a" * 201) is False
        
    def test_non_string_input(self):
        """Test non-string inputs."""
        assert is_valid_concept_name(123) is False
        assert is_valid_concept_name([]) is False
        assert is_valid_concept_name({}) is False


class TestIntegrationScenarios:
    """Test integration scenarios that combine multiple functions."""
    
    def test_end_to_end_normalization(self):
        """Test complete normalization workflow."""
        concept_name = "  CAPM.  "
        
        # Normalize the name
        normalized = normalize_concept_name(concept_name)
        assert normalized == "capm"
        
        # Generate cache key
        cache_key = generate_cache_key("DBpediaConnector", concept_name)
        assert cache_key == "dbpediaconnector_capm"
        
        # Get variants
        variants = get_concept_variants(concept_name)
        assert "capital asset pricing model" in variants
        assert "capm" in variants
        
    def test_acronym_workflow(self):
        """Test complete workflow for financial acronyms."""
        for acronym in ["CAPM", "VAR", "ETF", "REIT"]:
            # Should be valid
            assert is_valid_concept_name(acronym) is True
            
            # Should normalize consistently
            normalized = normalize_concept_name(acronym)
            assert normalized == acronym.lower()
            
            # Should have expanded variants
            variants = get_concept_variants(acronym)
            assert len(variants) >= 3  # At least the acronym variants
            
    def test_case_insensitive_consistency(self):
        """Test that case variations produce identical results."""
        test_cases = [
            ("CAPM", "capm", "Capm"),
            ("BLACK-SCHOLES", "black-scholes", "Black-Scholes"),
            ("PORTFOLIO", "portfolio", "Portfolio")
        ]
        
        for case_variants in test_cases:
            # All should normalize to the same value
            normalized_values = [normalize_concept_name(variant) for variant in case_variants]
            assert len(set(normalized_values)) == 1
            
            # All should generate the same cache key
            cache_keys = [generate_cache_key("TestConnector", variant) for variant in case_variants]
            assert len(set(cache_keys)) == 1