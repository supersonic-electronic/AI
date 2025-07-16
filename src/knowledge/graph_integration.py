"""
Graph database integration with PDF ingestion pipeline.

This module provides integration between the PDF ingestion pipeline and the
graph database, automatically extracting concepts and relationships from
processed documents and storing them in Neo4j.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import json

from ..ingestion.pdf2txt import PDFIngestor
from .ontology import FinancialMathOntology
from .concept_extractor import ConceptExtractor, get_concept_extractor
from .relationship_mapper import RelationshipMapper, get_relationship_mapper
from .graph_db import GraphDatabase
from src.settings import Settings


class GraphIntegratedPDFIngestor(PDFIngestor):
    """
    Enhanced PDF ingestor with graph database integration.
    
    This class extends the standard PDF ingestor to automatically extract
    concepts and relationships from processed documents and store them
    in a Neo4j graph database.
    """
    
    def __init__(self, settings: Settings):
        """Initialize the graph-integrated PDF ingestor."""
        super().__init__(settings)
        
        # Initialize graph database components
        self.ontology = FinancialMathOntology()
        self.concept_extractor = get_concept_extractor(settings, self.ontology)
        self.relationship_mapper = get_relationship_mapper(settings, self.ontology)
        
        # Initialize graph database connection
        self.graph_db = None
        if self._should_enable_graph_db():
            try:
                self.graph_db = GraphDatabase(settings)
                self.logger.info("Graph database integration enabled")
            except Exception as e:
                self.logger.warning(f"Failed to initialize graph database: {e}")
                self.graph_db = None
        
        # Track processed documents for graph operations
        self.processed_documents: Dict[str, Dict] = {}
    
    def _should_enable_graph_db(self) -> bool:
        """Check if graph database should be enabled based on settings."""
        return (
            hasattr(self.settings, 'neo4j_uri') and
            hasattr(self.settings, 'neo4j_username') and
            hasattr(self.settings, 'neo4j_password')
        )
    
    def _process_single_pdf(self, pdf_path: Path) -> Tuple[bool, str]:
        """
        Process a single PDF file with graph database integration.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # First process with standard PDF ingestor
            success, message = super()._process_single_pdf(pdf_path)
            
            if not success:
                return success, message
            
            # If graph database is enabled, extract concepts and relationships
            if self.graph_db:
                graph_success, graph_message = self._process_document_for_graph(pdf_path)
                
                if graph_success:
                    message += f" + Graph: {graph_message}"
                else:
                    # Don't fail the entire process if graph extraction fails
                    self.logger.warning(f"Graph processing failed for {pdf_path.name}: {graph_message}")
                    message += f" (Graph processing failed: {graph_message})"
            
            return success, message
            
        except Exception as e:
            return False, f"Failed to process {pdf_path.name}: {e}"
    
    def _process_document_for_graph(self, pdf_path: Path) -> Tuple[bool, str]:
        """
        Process a document for graph database extraction.
        
        Args:
            pdf_path: Path to the processed PDF file
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Load processed text and metadata
            text_file = self.text_dir / f"{pdf_path.stem}.txt"
            meta_file = self.meta_dir / f"{pdf_path.stem}.json"
            
            if not text_file.exists():
                return False, "Text file not found"
            
            # Read extracted text
            with open(text_file, 'r', encoding='utf-8') as f:
                document_text = f.read()
            
            # Read metadata
            document_metadata = {}
            if meta_file.exists():
                with open(meta_file, 'r', encoding='utf-8') as f:
                    document_metadata = json.load(f)
            
            # Process document pages for concept extraction
            all_concepts = []
            all_relationships = []
            document_name = pdf_path.name
            
            # Split document into pages for processing
            pages = document_text.split('\n\n')  # Simple page splitting
            
            for page_num, page_text in enumerate(pages, 1):
                if not page_text.strip():
                    continue
                
                # Extract concepts and relationships from this page
                concepts, relationships = self.concept_extractor.process_document_page(
                    page_text, document_name, page_num
                )
                
                all_concepts.extend(concepts)
                all_relationships.extend(relationships)
            
            # Map additional relationships using the relationship mapper
            if all_concepts:
                # Create document texts dictionary for relationship mapping
                document_texts = {i: page for i, page in enumerate(pages, 1) if page.strip()}
                
                # Map relationships
                mapped_relationships = self.relationship_mapper.map_relationships(
                    all_concepts, all_relationships, document_texts
                )
                
                # Convert to ontology objects
                ontology_concepts, ontology_relationships = self.concept_extractor.convert_to_ontology_objects(
                    all_concepts, all_relationships
                )
                
                # Add mapped relationships
                ontology_relationships.extend(mapped_relationships)
                
                # Store in graph database
                concepts_added = 0
                relationships_added = 0
                
                # Add concepts to graph database
                for concept in ontology_concepts:
                    if self.graph_db.add_concept(concept):
                        concepts_added += 1
                
                # Add relationships to graph database
                for relationship in ontology_relationships:
                    if self.graph_db.add_relationship(relationship):
                        relationships_added += 1
                
                # Store processing record
                self.processed_documents[document_name] = {
                    'concepts_extracted': len(all_concepts),
                    'relationships_extracted': len(all_relationships),
                    'concepts_stored': concepts_added,
                    'relationships_stored': relationships_added,
                    'processing_metadata': document_metadata
                }
                
                message = f"{concepts_added} concepts, {relationships_added} relationships stored"
                return True, message
            
            else:
                return True, "No concepts extracted"
            
        except Exception as e:
            self.logger.error(f"Graph processing error for {pdf_path.name}: {e}")
            return False, str(e)
    
    def get_graph_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the graph database.
        
        Returns:
            Dictionary containing graph statistics
        """
        if not self.graph_db:
            return {"error": "Graph database not initialized"}
        
        try:
            stats = self.graph_db.get_statistics()
            
            # Add processing statistics
            stats['processed_documents'] = len(self.processed_documents)
            stats['total_concepts_extracted'] = sum(
                doc['concepts_extracted'] for doc in self.processed_documents.values()
            )
            stats['total_relationships_extracted'] = sum(
                doc['relationships_extracted'] for doc in self.processed_documents.values()
            )
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error getting graph statistics: {e}")
            return {"error": str(e)}
    
    def query_graph(self, query: str, **parameters) -> List[Dict[str, Any]]:
        """
        Execute a Cypher query against the graph database.
        
        Args:
            query: Cypher query string
            **parameters: Query parameters
            
        Returns:
            List of query results
        """
        if not self.graph_db:
            return []
        
        try:
            with self.graph_db.session() as session:
                result = session.run(query, parameters)
                return [record.data() for record in result]
                
        except Exception as e:
            self.logger.error(f"Error executing graph query: {e}")
            return []
    
    def search_concepts(self, search_term: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for concepts in the graph database.
        
        Args:
            search_term: Term to search for
            limit: Maximum number of results
            
        Returns:
            List of matching concepts
        """
        if not self.graph_db:
            return []
        
        return self.graph_db.search_concepts(search_term, limit)
    
    def get_concept_relationships(self, concept_id: str) -> List[Dict[str, Any]]:
        """
        Get relationships for a specific concept.
        
        Args:
            concept_id: ID of the concept
            
        Returns:
            List of related concepts and their relationships
        """
        if not self.graph_db:
            return []
        
        return self.graph_db.get_related_concepts(concept_id)
    
    def get_document_concepts(self, document_name: str) -> List[Dict[str, Any]]:
        """
        Get all concepts extracted from a specific document.
        
        Args:
            document_name: Name of the document
            
        Returns:
            List of concepts from the document
        """
        if not self.graph_db:
            return []
        
        return self.graph_db.get_document_concepts(document_name)
    
    def analyze_concept_network(self, concept_id: str, depth: int = 2) -> Dict[str, Any]:
        """
        Analyze the network around a specific concept.
        
        Args:
            concept_id: ID of the central concept
            depth: Maximum depth to explore
            
        Returns:
            Network analysis results
        """
        if not self.graph_db:
            return {}
        
        # Get concept neighbors
        network = self.graph_db.get_concept_neighbors(concept_id, depth)
        
        # Add network analysis
        if network:
            # Analyze relationship patterns
            relationships = self.relationship_mapper.analyze_relationship_patterns(
                [rel for rel in network.get('relationships', [])]
            )
            network['analysis'] = relationships
        
        return network
    
    def export_graph_data(self, output_path: Path) -> bool:
        """
        Export graph data to a file.
        
        Args:
            output_path: Path to save the export
            
        Returns:
            True if successful, False otherwise
        """
        if not self.graph_db:
            return False
        
        try:
            # Get all concepts and relationships
            all_concepts = self.query_graph("MATCH (c:Concept) RETURN c")
            all_relationships = self.query_graph("MATCH ()-[r:RELATED_TO]->() RETURN r")
            
            export_data = {
                'concepts': all_concepts,
                'relationships': all_relationships,
                'statistics': self.get_graph_statistics(),
                'processed_documents': self.processed_documents
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Graph data exported to {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting graph data: {e}")
            return False
    
    def clear_graph_database(self) -> bool:
        """
        Clear all data from the graph database.
        
        Returns:
            True if successful, False otherwise
        """
        if not self.graph_db:
            return False
        
        try:
            success = self.graph_db.clear_database()
            if success:
                self.processed_documents.clear()
                self.logger.info("Graph database cleared successfully")
            return success
            
        except Exception as e:
            self.logger.error(f"Error clearing graph database: {e}")
            return False
    
    def close(self):
        """Close the graph database connection."""
        if self.graph_db:
            self.graph_db.close()
            self.logger.info("Graph database connection closed")


class GraphQueryInterface:
    """
    Interface for querying the knowledge graph.
    
    This class provides high-level methods for querying and analyzing
    the knowledge graph built from processed documents.
    """
    
    def __init__(self, settings: Settings):
        """Initialize the graph query interface."""
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        
        # Initialize graph database
        self.graph_db = GraphDatabase(settings)
        
        # Initialize ontology for reference
        self.ontology = FinancialMathOntology()
    
    def find_related_concepts(self, concept_name: str, 
                            relationship_type: Optional[str] = None,
                            max_depth: int = 2) -> List[Dict[str, Any]]:
        """
        Find concepts related to a given concept.
        
        Args:
            concept_name: Name of the concept to search for
            relationship_type: Optional relationship type filter
            max_depth: Maximum relationship depth
            
        Returns:
            List of related concepts
        """
        # First find the concept by name
        concepts = self.graph_db.search_concepts(concept_name, limit=1)
        
        if not concepts:
            return []
        
        concept_id = concepts[0]['id']
        
        # Get related concepts
        if relationship_type:
            from .ontology import RelationshipType
            rel_type = RelationshipType(relationship_type)
            return self.graph_db.get_related_concepts(concept_id, rel_type)
        else:
            return self.graph_db.get_related_concepts(concept_id)
    
    def trace_concept_dependencies(self, concept_name: str) -> Dict[str, Any]:
        """
        Trace the dependency chain for a concept.
        
        Args:
            concept_name: Name of the concept
            
        Returns:
            Dependency trace information
        """
        from .ontology import RelationshipType
        
        # Find the concept
        concepts = self.graph_db.search_concepts(concept_name, limit=1)
        
        if not concepts:
            return {"error": f"Concept '{concept_name}' not found"}
        
        concept_id = concepts[0]['id']
        
        # Get dependencies (what this concept depends on)
        dependencies = self.graph_db.get_related_concepts(
            concept_id, RelationshipType.DEPENDS_ON, direction="outgoing"
        )
        
        # Get dependents (what depends on this concept)
        dependents = self.graph_db.get_related_concepts(
            concept_id, RelationshipType.DEPENDS_ON, direction="incoming"
        )
        
        return {
            'concept': concepts[0],
            'dependencies': dependencies,
            'dependents': dependents
        }
    
    def find_concept_definitions(self, concept_name: str) -> List[Dict[str, Any]]:
        """
        Find definitions for a concept.
        
        Args:
            concept_name: Name of the concept
            
        Returns:
            List of concept definitions
        """
        from .ontology import RelationshipType
        
        # Find concepts that define this concept
        query = """
        MATCH (definer:Concept)-[r:RELATED_TO {type: 'defines'}]->(defined:Concept)
        WHERE defined.name CONTAINS $concept_name
        RETURN definer, r, defined
        """
        
        results = []
        try:
            with self.graph_db.session() as session:
                result = session.run(query, {'concept_name': concept_name})
                for record in result:
                    results.append({
                        'definer': dict(record['definer']),
                        'defined': dict(record['defined']),
                        'relationship': dict(record['r'])
                    })
        except Exception as e:
            self.logger.error(f"Error finding definitions: {e}")
        
        return results
    
    def analyze_document_concepts(self, document_name: str) -> Dict[str, Any]:
        """
        Analyze concepts extracted from a specific document.
        
        Args:
            document_name: Name of the document
            
        Returns:
            Analysis of document concepts
        """
        concepts = self.graph_db.get_document_concepts(document_name)
        
        if not concepts:
            return {"error": f"No concepts found for document '{document_name}'"}
        
        # Group concepts by type
        concept_types = {}
        for concept in concepts:
            concept_type = concept.get('type', 'unknown')
            if concept_type not in concept_types:
                concept_types[concept_type] = []
            concept_types[concept_type].append(concept)
        
        # Find relationships between concepts in this document
        doc_relationships = []
        for concept in concepts:
            related = self.graph_db.get_related_concepts(concept['id'])
            for rel in related:
                if rel['concept']['source_document'] == document_name:
                    doc_relationships.append(rel)
        
        return {
            'document': document_name,
            'total_concepts': len(concepts),
            'concept_types': {k: len(v) for k, v in concept_types.items()},
            'concepts_by_type': concept_types,
            'internal_relationships': len(doc_relationships),
            'relationships': doc_relationships
        }
    
    def get_concept_evolution(self, concept_name: str) -> Dict[str, Any]:
        """
        Track how a concept is used across different documents.
        
        Args:
            concept_name: Name of the concept
            
        Returns:
            Evolution analysis of the concept
        """
        concepts = self.graph_db.search_concepts(concept_name)
        
        if not concepts:
            return {"error": f"Concept '{concept_name}' not found"}
        
        # Group by document
        by_document = {}
        for concept in concepts:
            doc = concept.get('source_document', 'unknown')
            if doc not in by_document:
                by_document[doc] = []
            by_document[doc].append(concept)
        
        # Analyze relationships across documents
        cross_doc_relationships = []
        for concept in concepts:
            related = self.graph_db.get_related_concepts(concept['id'])
            for rel in related:
                if rel['concept']['source_document'] != concept.get('source_document'):
                    cross_doc_relationships.append({
                        'from_document': concept.get('source_document'),
                        'to_document': rel['concept']['source_document'],
                        'relationship': rel['relationship']
                    })
        
        return {
            'concept_name': concept_name,
            'total_instances': len(concepts),
            'documents': list(by_document.keys()),
            'instances_by_document': {k: len(v) for k, v in by_document.items()},
            'cross_document_relationships': cross_doc_relationships
        }
    
    def close(self):
        """Close the graph database connection."""
        if self.graph_db:
            self.graph_db.close()


def get_graph_integrated_ingestor(settings: Settings) -> GraphIntegratedPDFIngestor:
    """
    Factory function to create a graph-integrated PDF ingestor.
    
    Args:
        settings: Application settings
        
    Returns:
        GraphIntegratedPDFIngestor instance
    """
    return GraphIntegratedPDFIngestor(settings)


def get_graph_query_interface(settings: Settings) -> GraphQueryInterface:
    """
    Factory function to create a graph query interface.
    
    Args:
        settings: Application settings
        
    Returns:
        GraphQueryInterface instance
    """
    return GraphQueryInterface(settings)