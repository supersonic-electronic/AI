#!/usr/bin/env python3
"""
Simple test to create and display enhanced concept data.
"""

import json
from pathlib import Path

def create_enhanced_test_data():
    """Create sample enhanced concept data for testing."""
    
    concepts = {
        "portfolio_theory": {
            "name": "Portfolio Theory",
            "type": "methodology",
            "description": "Mathematical framework for constructing optimal investment portfolios",
            "definition": "A theory that describes how to construct portfolios to optimize expected return based on a given level of market risk",
            "latex": r"E[R_p] = \sum_{i=1}^{n} w_i E[R_i]",
            "notation": "E[R_p] = Expected Portfolio Return",
            "examples": [
                "Modern Portfolio Theory by Markowitz",
                "Capital Asset Pricing Model",
                "Efficient frontier construction"
            ],
            "related_formulas": [
                r"\sigma_p^2 = \sum_{i=1}^{n} \sum_{j=1}^{n} w_i w_j \sigma_{ij}",
                r"\text{Sharpe Ratio} = \frac{E[R_p] - R_f}{\sigma_p}"
            ],
            "applications": [
                "Asset allocation",
                "Risk management", 
                "Investment strategy"
            ],
            "prerequisites": [
                "Expected return",
                "Variance and covariance",
                "Risk-return relationship"
            ],
            "complexity_level": "intermediate",
            "domain": "finance",
            "keywords": ["optimization", "diversification", "risk-return"],
            "external_links": {
                "wikipedia": "https://en.wikipedia.org/wiki/Modern_portfolio_theory",
                "investopedia": "https://www.investopedia.com/terms/m/modernportfoliotheory.asp"
            },
            "confidence": 1.0,
            "frequency": 15,
            "context": "Foundation of modern quantitative finance",
            "source_docs": ["markowitz_1952.pdf"],
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        },
        "sharpe_ratio": {
            "name": "Sharpe Ratio",
            "type": "metric",
            "description": "Risk-adjusted return metric measuring excess return per unit of risk",
            "definition": "A measure for calculating risk-adjusted return, defined as the average return earned in excess of the risk-free rate per unit of volatility",
            "latex": r"S = \frac{E[R_p] - R_f}{\sigma_p}",
            "notation": "S = (Expected Return - Risk-free Rate) / Standard Deviation",
            "examples": [
                "Portfolio performance evaluation",
                "Fund comparison",
                "Risk-adjusted benchmarking"
            ],
            "related_formulas": [
                r"E[R_p] - R_f = \text{Risk Premium}",
                r"\sigma_p = \sqrt{\text{Var}(R_p)}"
            ],
            "applications": [
                "Performance measurement",
                "Portfolio optimization",
                "Risk assessment"
            ],
            "prerequisites": [
                "Expected return",
                "Standard deviation",
                "Risk-free rate"
            ],
            "complexity_level": "beginner",
            "domain": "finance",
            "keywords": ["risk-adjusted", "performance", "volatility"],
            "external_links": {
                "investopedia": "https://www.investopedia.com/terms/s/sharperatio.asp"
            },
            "confidence": 1.0,
            "frequency": 25,
            "context": "Widely used performance metric in finance",
            "source_docs": ["sharpe_1966.pdf"],
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        },
        "efficient_frontier": {
            "name": "Efficient Frontier",
            "type": "methodology",
            "description": "Set of optimal portfolios offering highest expected return for each level of risk",
            "definition": "A curve on a graph representing portfolios that provide the maximum expected return for a given level of risk",
            "latex": r"\min w^T \Sigma w \text{ subject to: } w^T \mu = \mu_p, \sum w_i = 1",
            "notation": "Optimization problem with constraints",
            "examples": [
                "Mean-variance optimization",
                "Asset allocation strategies", 
                "Portfolio construction"
            ],
            "related_formulas": [
                r"\mu_p = w^T \mu = \text{Target Return}",
                r"\sigma_p^2 = w^T \Sigma w = \text{Portfolio Variance}"
            ],
            "applications": [
                "Investment management",
                "Risk budgeting",
                "Strategic asset allocation"
            ],
            "prerequisites": [
                "Portfolio theory",
                "Mean-variance optimization",
                "Risk-return relationship"
            ],
            "complexity_level": "advanced",
            "domain": "finance",
            "keywords": ["optimization", "risk-return", "portfolio"],
            "external_links": {
                "wikipedia": "https://en.wikipedia.org/wiki/Efficient_frontier"
            },
            "confidence": 1.0,
            "frequency": 12,
            "context": "Core concept in portfolio optimization",
            "source_docs": ["markowitz_1952.pdf"],
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
    }
    
    relationships = [
        {
            "source": "portfolio_theory",
            "target": "sharpe_ratio", 
            "type": "contains",
            "confidence": 0.9
        },
        {
            "source": "portfolio_theory",
            "target": "efficient_frontier",
            "type": "produces", 
            "confidence": 0.95
        },
        {
            "source": "efficient_frontier",
            "target": "sharpe_ratio",
            "type": "maximizes",
            "confidence": 0.8
        }
    ]
    
    return {
        "concepts": concepts,
        "relationships": relationships,
        "stats": {
            "total_concepts": len(concepts),
            "total_relationships": len(relationships)
        }
    }

def save_test_data():
    """Save test data to files for the web app to consume."""
    
    data = create_enhanced_test_data()
    
    # Create test data directory
    test_dir = Path("test_data")
    test_dir.mkdir(exist_ok=True)
    
    # Save main graph data
    with open(test_dir / "knowledge_graph.json", "w") as f:
        json.dump(data, f, indent=2)
    
    # Save individual concept files  
    concepts_dir = test_dir / "concepts"
    concepts_dir.mkdir(exist_ok=True)
    
    for concept_id, concept_data in data["concepts"].items():
        with open(concepts_dir / f"{concept_id}.json", "w") as f:
            json.dump(concept_data, f, indent=2)
    
    print(f"Test data saved to {test_dir}")
    print(f"Created {len(data['concepts'])} enhanced concepts:")
    
    for concept_id, concept_data in data["concepts"].items():
        name = concept_data["name"]
        latex = "✓" if concept_data.get("latex") else "✗"
        definition = "✓" if concept_data.get("definition") else "✗"
        examples = f"{len(concept_data.get('examples', []))}"
        applications = f"{len(concept_data.get('applications', []))}"
        
        print(f"  - {name}: LaTeX={latex}, Definition={definition}, Examples={examples}, Applications={applications}")

if __name__ == "__main__":
    save_test_data()