#!/usr/bin/env python3
"""
Test script to demonstrate enhanced concept details functionality.
"""

import json
from pathlib import Path
from src.knowledge.ontology import FinancialMathOntology, Concept, ConceptType, Relationship, RelationshipType

def create_test_concepts():
    """Create test concepts with enhanced metadata to demonstrate functionality."""
    
    # Initialize ontology
    ontology = FinancialMathOntology()
    
    # The ontology already has enhanced concepts, let's export them
    cytoscape_data = ontology.export_for_cytoscape()
    
    # Create a test data file that the frontend can read
    test_data = {
        "concepts": {},
        "relationships": []
    }
    
    # Convert nodes to concept format
    for node in cytoscape_data["nodes"]:
        concept_id = node["data"]["id"]
        concept_data = node["data"].copy()
        test_data["concepts"][concept_id] = concept_data
    
    # Convert edges to relationship format
    for edge in cytoscape_data["edges"]:
        relationship = {
            "source": edge["data"]["source"],
            "target": edge["data"]["target"],
            "type": edge["data"]["type"],
            "confidence": edge["data"]["confidence"],
            "properties": edge["data"]["properties"],
            "source_document": edge["data"]["source_document"],
            "source_page": edge["data"]["source_page"],
            "context": edge["data"]["context"]
        }
        test_data["relationships"].append(relationship)
    
    # Add some sample stats
    test_data["stats"] = {
        "total_concepts": len(test_data["concepts"]),
        "total_relationships": len(test_data["relationships"]),
        "concepts_by_type": [],
        "relationships_by_type": []
    }
    
    return test_data

def create_mock_api_responses():
    """Create mock API response files for testing."""
    
    # Create test data
    test_data = create_test_concepts()
    
    # Create mock data directory
    mock_dir = Path("mock_api_data")
    mock_dir.mkdir(exist_ok=True)
    
    # Save graph data
    with open(mock_dir / "graph_data.json", "w") as f:
        json.dump(test_data, f, indent=2)
    
    # Create individual concept files
    concepts_dir = mock_dir / "concepts"
    concepts_dir.mkdir(exist_ok=True)
    
    for concept_id, concept_data in test_data["concepts"].items():
        # Add some enhanced test data
        concept_data.update({
            "frequency": 10,
            "context": f"Context for {concept_data['name']}",
            "source_docs": ["test_document.pdf"],
            "related_concepts": [
                {
                    "name": "Related Concept",
                    "type": "formula",
                    "relationship_type": "derives_from"
                }
            ]
        })
        
        with open(concepts_dir / f"{concept_id}.json", "w") as f:
            json.dump(concept_data, f, indent=2)
    
    print(f"Mock data created in {mock_dir}")
    print(f"Created {len(test_data['concepts'])} test concepts")
    print("Concepts with enhanced metadata:")
    
    for concept_id, concept_data in test_data["concepts"].items():
        name = concept_data.get("name", "Unknown")
        has_latex = bool(concept_data.get("latex"))
        has_definition = bool(concept_data.get("definition"))
        has_examples = bool(concept_data.get("examples"))
        
        print(f"  - {name}: LaTeX={has_latex}, Definition={has_definition}, Examples={has_examples}")

if __name__ == "__main__":
    create_mock_api_responses()