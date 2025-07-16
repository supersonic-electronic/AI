"""
Graph database implementation using Neo4j for storing and querying ontological knowledge.

This module provides a Neo4j-based graph database for storing concepts, relationships,
and semantic knowledge extracted from financial mathematics documents.
"""

import logging
from typing import Dict, List, Optional, Tuple, Union, Any
from contextlib import contextmanager
import json
from datetime import datetime

try:
    from neo4j import GraphDatabase, Session, Transaction
    from neo4j.exceptions import ServiceUnavailable, AuthError, ClientError
except ImportError:
    # Neo4j not available - provide stubs for basic functionality
    GraphDatabase = None
    Session = None
    Transaction = None
    ServiceUnavailable = Exception
    AuthError = Exception
    ClientError = Exception

from .ontology import Concept, Relationship, ConceptType, RelationshipType, FinancialMathOntology
from src.settings import Settings


class GraphDatabase:
    """
    Neo4j graph database interface for storing and querying ontological knowledge.
    
    This class provides methods to store concepts and relationships in Neo4j,
    execute queries, and manage the knowledge graph structure.
    """
    
    def __init__(self, settings: Settings):
        """Initialize the graph database connection."""
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        
        # Neo4j connection details
        self.uri = getattr(settings, 'neo4j_uri', 'neo4j://localhost:7687')
        self.username = getattr(settings, 'neo4j_username', 'neo4j')
        self.password = getattr(settings, 'neo4j_password', 'password')
        self.database = getattr(settings, 'neo4j_database', 'neo4j')
        
        # Initialize driver
        self.driver = None
        self._initialize_driver()
        
        # Create constraints and indexes
        self._create_constraints()
        self._create_indexes()
    
    def _initialize_driver(self) -> None:
        """Initialize the Neo4j driver."""
        if GraphDatabase is None:
            self.logger.warning("Neo4j not available - graph database functionality disabled")
            self.driver = None
            return
            
        try:
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.username, self.password),
                encrypted=False  # Set to True for production
            )
            # Test connection
            self.driver.verify_connectivity()
            self.logger.info("Connected to Neo4j database successfully")
        except ServiceUnavailable as e:
            self.logger.error(f"Neo4j service unavailable: {e}")
            raise
        except AuthError as e:
            self.logger.error(f"Neo4j authentication failed: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Failed to connect to Neo4j: {e}")
            raise
    
    def _create_constraints(self) -> None:
        """Create database constraints for data integrity."""
        if self.driver is None:
            return
            
        constraints = [
            "CREATE CONSTRAINT concept_id_unique IF NOT EXISTS FOR (c:Concept) REQUIRE c.id IS UNIQUE",
            "CREATE CONSTRAINT concept_name_exists IF NOT EXISTS FOR (c:Concept) REQUIRE c.name IS NOT NULL",
            "CREATE CONSTRAINT relationship_type_exists IF NOT EXISTS FOR ()-[r:RELATED_TO]-() REQUIRE r.type IS NOT NULL",
        ]
        
        with self.driver.session(database=self.database) as session:
            for constraint in constraints:
                try:
                    session.run(constraint)
                    self.logger.debug(f"Created constraint: {constraint}")
                except ClientError as e:
                    if "already exists" not in str(e):
                        self.logger.warning(f"Failed to create constraint: {e}")
    
    def _create_indexes(self) -> None:
        """Create database indexes for performance."""
        if self.driver is None:
            return
            
        indexes = [
            "CREATE INDEX concept_type_index IF NOT EXISTS FOR (c:Concept) ON (c.type)",
            "CREATE INDEX concept_name_index IF NOT EXISTS FOR (c:Concept) ON (c.name)",
            "CREATE INDEX relationship_type_index IF NOT EXISTS FOR ()-[r:RELATED_TO]-() ON (r.type)",
            "CREATE INDEX document_index IF NOT EXISTS FOR (c:Concept) ON (c.source_document)",
            "CREATE INDEX page_index IF NOT EXISTS FOR (c:Concept) ON (c.source_page)",
        ]
        
        with self.driver.session(database=self.database) as session:
            for index in indexes:
                try:
                    session.run(index)
                    self.logger.debug(f"Created index: {index}")
                except ClientError as e:
                    if "already exists" not in str(e):
                        self.logger.warning(f"Failed to create index: {e}")
    
    @contextmanager
    def session(self):
        """Context manager for database sessions."""
        if self.driver is None:
            yield None
            return
            
        session = self.driver.session(database=self.database)
        try:
            yield session
        finally:
            session.close()
    
    def add_concept(self, concept: Concept) -> bool:
        """Add a concept to the graph database."""
        query = """
        MERGE (c:Concept {id: $id})
        SET c.name = $name,
            c.type = $type,
            c.description = $description,
            c.notation = $notation,
            c.latex = $latex,
            c.aliases = $aliases,
            c.properties = $properties,
            c.source_document = $source_document,
            c.source_page = $source_page,
            c.confidence = $confidence,
            c.created_at = $created_at,
            c.updated_at = $updated_at
        RETURN c
        """
        
        parameters = {
            "id": concept.id,
            "name": concept.name,
            "type": concept.concept_type.value,
            "description": concept.description,
            "notation": concept.notation,
            "latex": concept.latex,
            "aliases": list(concept.aliases),
            "properties": concept.properties,
            "source_document": concept.source_document,
            "source_page": concept.source_page,
            "confidence": concept.confidence,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        try:
            with self.session() as session:
                if session is None:
                    self.logger.warning(f"Cannot add concept {concept.name}: Neo4j not available")
                    return False
                result = session.run(query, parameters)
                record = result.single()
                if record:
                    self.logger.debug(f"Added concept: {concept.name}")
                    return True
                return False
        except Exception as e:
            self.logger.error(f"Failed to add concept {concept.name}: {e}")
            return False
    
    def add_relationship(self, relationship: Relationship) -> bool:
        """Add a relationship to the graph database."""
        query = """
        MATCH (source:Concept {id: $source_id})
        MATCH (target:Concept {id: $target_id})
        MERGE (source)-[r:RELATED_TO {type: $rel_type}]->(target)
        SET r.confidence = $confidence,
            r.properties = $properties,
            r.source_document = $source_document,
            r.source_page = $source_page,
            r.context = $context,
            r.created_at = $created_at,
            r.updated_at = $updated_at
        RETURN r
        """
        
        parameters = {
            "source_id": relationship.source_concept_id,
            "target_id": relationship.target_concept_id,
            "rel_type": relationship.relationship_type.value,
            "confidence": relationship.confidence,
            "properties": relationship.properties,
            "source_document": relationship.source_document,
            "source_page": relationship.source_page,
            "context": relationship.context,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        try:
            with self.session() as session:
                if session is None:
                    self.logger.warning(f"Cannot add relationship: Neo4j not available")
                    return False
                result = session.run(query, parameters)
                record = result.single()
                if record:
                    self.logger.debug(f"Added relationship: {relationship.source_concept_id} -> {relationship.target_concept_id}")
                    return True
                return False
        except Exception as e:
            self.logger.error(f"Failed to add relationship: {e}")
            return False
    
    def get_concept(self, concept_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a concept by ID."""
        query = "MATCH (c:Concept {id: $id}) RETURN c"
        
        try:
            with self.session() as session:
                if session is None:
                    return None
                result = session.run(query, {"id": concept_id})
                record = result.single()
                if record:
                    return dict(record["c"])
                return None
        except Exception as e:
            self.logger.error(f"Failed to get concept {concept_id}: {e}")
            return None
    
    def get_concepts_by_type(self, concept_type: ConceptType) -> List[Dict[str, Any]]:
        """Get all concepts of a specific type."""
        query = "MATCH (c:Concept {type: $type}) RETURN c ORDER BY c.name"
        
        try:
            with self.session() as session:
                if session is None:
                    return []
                result = session.run(query, {"type": concept_type.value})
                return [dict(record["c"]) for record in result]
        except Exception as e:
            self.logger.error(f"Failed to get concepts by type {concept_type}: {e}")
            return []
    
    def get_related_concepts(self, concept_id: str, 
                           relationship_type: Optional[RelationshipType] = None,
                           direction: str = "both") -> List[Dict[str, Any]]:
        """Get concepts related to a given concept."""
        if direction == "outgoing":
            query = "MATCH (c:Concept {id: $id})-[r:RELATED_TO]->(related:Concept)"
        elif direction == "incoming":
            query = "MATCH (c:Concept {id: $id})<-[r:RELATED_TO]-(related:Concept)"
        else:  # both
            query = "MATCH (c:Concept {id: $id})-[r:RELATED_TO]-(related:Concept)"
        
        if relationship_type:
            query += " WHERE r.type = $rel_type"
        
        query += " RETURN related, r ORDER BY r.confidence DESC"
        
        parameters = {"id": concept_id}
        if relationship_type:
            parameters["rel_type"] = relationship_type.value
        
        try:
            with self.session() as session:
                if session is None:
                    return []
                result = session.run(query, parameters)
                return [
                    {
                        "concept": dict(record["related"]),
                        "relationship": dict(record["r"])
                    }
                    for record in result
                ]
        except Exception as e:
            self.logger.error(f"Failed to get related concepts for {concept_id}: {e}")
            return []
    
    def search_concepts(self, query_text: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for concepts by name or description."""
        query = """
        MATCH (c:Concept)
        WHERE c.name CONTAINS $query OR c.description CONTAINS $query
           OR any(alias IN c.aliases WHERE alias CONTAINS $query)
        RETURN c
        ORDER BY c.confidence DESC
        LIMIT $limit
        """
        
        try:
            with self.session() as session:
                if session is None:
                    return []
                result = session.run(query, {"query": query_text, "limit": limit})
                return [dict(record["c"]) for record in result]
        except Exception as e:
            self.logger.error(f"Failed to search concepts: {e}")
            return []
    
    def get_concept_path(self, source_id: str, target_id: str, 
                        max_length: int = 5) -> List[Dict[str, Any]]:
        """Find the shortest path between two concepts."""
        query = """
        MATCH path = shortestPath((source:Concept {id: $source_id})
                                 -[:RELATED_TO*1..{max_length}]-
                                 (target:Concept {id: $target_id}))
        RETURN path
        """.format(max_length=max_length)
        
        try:
            with self.session() as session:
                result = session.run(query, {"source_id": source_id, "target_id": target_id})
                record = result.single()
                if record:
                    path = record["path"]
                    return [
                        {
                            "concept": dict(node),
                            "relationship": dict(rel) if rel else None
                        }
                        for node, rel in zip(path.nodes, path.relationships + [None])
                    ]
                return []
        except Exception as e:
            self.logger.error(f"Failed to find path between {source_id} and {target_id}: {e}")
            return []
    
    def get_concept_neighbors(self, concept_id: str, depth: int = 2) -> Dict[str, Any]:
        """Get all concepts within a specified depth from a given concept."""
        query = """
        MATCH (c:Concept {id: $id})
        CALL apoc.path.subgraphNodes(c, {
            relationshipFilter: "RELATED_TO",
            maxLevel: $depth
        }) YIELD node
        WITH c, collect(node) AS neighbors
        MATCH (c)-[r:RELATED_TO*1..{depth}]-(neighbor)
        RETURN c, neighbors, collect(r) AS relationships
        """.format(depth=depth)
        
        try:
            with self.session() as session:
                result = session.run(query, {"id": concept_id, "depth": depth})
                record = result.single()
                if record:
                    return {
                        "center": dict(record["c"]),
                        "neighbors": [dict(node) for node in record["neighbors"]],
                        "relationships": [dict(rel) for rel in record["relationships"]]
                    }
                return {}
        except Exception as e:
            self.logger.error(f"Failed to get neighbors for {concept_id}: {e}")
            return {}
    
    def get_document_concepts(self, document_name: str) -> List[Dict[str, Any]]:
        """Get all concepts from a specific document."""
        query = """
        MATCH (c:Concept {source_document: $document})
        RETURN c
        ORDER BY c.source_page, c.name
        """
        
        try:
            with self.session() as session:
                result = session.run(query, {"document": document_name})
                return [dict(record["c"]) for record in result]
        except Exception as e:
            self.logger.error(f"Failed to get concepts from document {document_name}: {e}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics."""
        queries = {
            "total_concepts": "MATCH (c:Concept) RETURN count(c) AS count",
            "total_relationships": "MATCH ()-[r:RELATED_TO]->() RETURN count(r) AS count",
            "concepts_by_type": "MATCH (c:Concept) RETURN c.type AS type, count(c) AS count ORDER BY count DESC",
            "relationships_by_type": "MATCH ()-[r:RELATED_TO]->() RETURN r.type AS type, count(r) AS count ORDER BY count DESC",
            "documents_processed": "MATCH (c:Concept) WHERE c.source_document IS NOT NULL RETURN count(DISTINCT c.source_document) AS count"
        }
        
        stats = {}
        try:
            with self.session() as session:
                for stat_name, query in queries.items():
                    result = session.run(query)
                    if stat_name in ["concepts_by_type", "relationships_by_type"]:
                        stats[stat_name] = [{"type": record["type"], "count": record["count"]} for record in result]
                    else:
                        record = result.single()
                        stats[stat_name] = record["count"] if record else 0
        except Exception as e:
            self.logger.error(f"Failed to get statistics: {e}")
        
        return stats
    
    def clear_database(self) -> bool:
        """Clear all data from the database (use with caution)."""
        query = "MATCH (n) DETACH DELETE n"
        
        try:
            with self.session() as session:
                session.run(query)
                self.logger.info("Database cleared successfully")
                return True
        except Exception as e:
            self.logger.error(f"Failed to clear database: {e}")
            return False
    
    def close(self) -> None:
        """Close the database connection."""
        if self.driver:
            self.driver.close()
            self.logger.info("Neo4j connection closed")
    
    def __del__(self):
        """Cleanup when object is destroyed."""
        self.close()