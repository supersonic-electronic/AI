"""
Utility functions for knowledge graph operations.

This module provides shared utility functions used across the knowledge
management system to ensure consistency in concept handling.
"""

import re
from typing import Set, Optional


def normalize_concept_name(name: str) -> str:
    """
    Normalize concept names for consistent handling across all systems.
    
    This function ensures that concept names are handled consistently
    in caching, extraction, enrichment, and relationship matching.
    
    Args:
        name: Raw concept name to normalize
        
    Returns:
        Normalized concept name
        
    Examples:
        >>> normalize_concept_name("  CAPM  ")
        "capm"
        >>> normalize_concept_name("Black-Scholes")
        "black-scholes"
        >>> normalize_concept_name("α (Alpha)")
        "α (alpha)"
    """
    if not name or not isinstance(name, str):
        return ""
    
    # Strip whitespace and convert to lowercase
    normalized = name.strip().lower()
    
    # Normalize whitespace (replace multiple spaces with single space)
    normalized = re.sub(r'\s+', ' ', normalized)
    
    # Remove trailing punctuation that doesn't affect meaning
    normalized = normalized.rstrip('.,;:')
    
    return normalized


def generate_cache_key(connector_name: str, concept_name: str) -> str:
    """
    Generate a normalized cache key for external ontology data.
    
    Args:
        connector_name: Name of the external ontology connector
        concept_name: Name of the concept to cache
        
    Returns:
        Normalized cache key
        
    Examples:
        >>> generate_cache_key("DBpediaConnector", "CAPM")
        "dbpediaconnector_capm"
        >>> generate_cache_key("WikidataConnector", "  Black-Scholes  ")
        "wikidataconnector_black-scholes"
    """
    normalized_connector = connector_name.lower()
    normalized_concept = normalize_concept_name(concept_name)
    return f"{normalized_connector}_{normalized_concept}"


def get_concept_variants(concept_name: str) -> Set[str]:
    """
    Get common variants of a concept name for cache lookup.
    
    This helps identify existing cache entries that might match
    a concept under different naming conventions.
    
    Args:
        concept_name: Base concept name
        
    Returns:
        Set of concept name variants to check
        
    Examples:
        >>> get_concept_variants("CAPM")
        {"capm", "CAPM", "Capm", "capital asset pricing model"}
    """
    variants = set()
    
    # Add the normalized version
    normalized = normalize_concept_name(concept_name)
    variants.add(normalized)
    
    # Add original casing variations
    variants.add(concept_name.upper())
    variants.add(concept_name.lower())
    variants.add(concept_name.capitalize())
    
    # Add common financial acronym expansions
    financial_acronyms = {
        'capm': 'capital asset pricing model',
        'apt': 'arbitrage pricing theory',
        'var': 'value at risk',
        'etf': 'exchange traded fund',
        'reit': 'real estate investment trust',
        'ipo': 'initial public offering',
        'roi': 'return on investment',
        'npv': 'net present value',
        'irr': 'internal rate of return',
        'wacc': 'weighted average cost of capital'
    }
    
    if normalized in financial_acronyms:
        variants.add(financial_acronyms[normalized])
    
    # Remove empty strings
    variants.discard("")
    
    return variants


def is_valid_concept_name(name: str) -> bool:
    """
    Check if a concept name is valid for processing.
    
    Args:
        name: Concept name to validate
        
    Returns:
        True if the concept name is valid for processing
    """
    if not name or not isinstance(name, str):
        return False
    
    # Must have some non-whitespace content
    if not name.strip():
        return False
    
    # Must be reasonable length (not too short or too long)
    stripped = name.strip()
    if len(stripped) < 2 or len(stripped) > 200:
        return False
    
    return True


def fix_acronym_casing(name: str) -> str:
    """
    Fix the casing of known financial acronyms.
    
    Args:
        name: Concept name to fix
        
    Returns:
        Name with proper acronym casing
        
    Examples:
        >>> fix_acronym_casing("capm")
        "CAPM"
        >>> fix_acronym_casing("Var")
        "VAR"
        >>> fix_acronym_casing("Portfolio Theory")
        "Portfolio Theory"
    """
    if not name or not isinstance(name, str):
        return name
    
    # Known financial acronyms that should be uppercase
    financial_acronyms = {
        'capm': 'CAPM',
        'var': 'VAR',
        'apt': 'APT',
        'etf': 'ETF',
        'reit': 'REIT',
        'ipo': 'IPO',
        'roi': 'ROI',
        'npv': 'NPV',
        'irr': 'IRR',
        'wacc': 'WACC',
        'cvar': 'CVaR',
        'esg': 'ESG',
        'pe': 'PE',
        'pb': 'PB',
        'eps': 'EPS'
    }
    
    # Check if the name (when normalized) is a known acronym
    normalized = name.lower().strip()
    if normalized in financial_acronyms:
        return financial_acronyms[normalized]
    
    # Return original name if not a known acronym
    return name