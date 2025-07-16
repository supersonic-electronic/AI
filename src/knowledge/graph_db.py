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

from neo4j import GraphDatabase, Session, Transaction
from neo4j.exceptions import ServiceUnavailable, AuthError, ClientError

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
        session = self.driver.session(database=self.database)
        try:
            yield session
        finally:
            session.close()
    
    def add_concept(self, concept: Concept) -> bool:
        """Add a concept to the graph database."""
        query = \"\"\"\n        MERGE (c:Concept {id: $id})\n        SET c.name = $name,\n            c.type = $type,\n            c.description = $description,\n            c.notation = $notation,\n            c.latex = $latex,\n            c.aliases = $aliases,\n            c.properties = $properties,\n            c.source_document = $source_document,\n            c.source_page = $source_page,\n            c.confidence = $confidence,\n            c.created_at = $created_at,\n            c.updated_at = $updated_at\n        RETURN c\n        \"\"\"\n        \n        parameters = {\n            \"id\": concept.id,\n            \"name\": concept.name,\n            \"type\": concept.concept_type.value,\n            \"description\": concept.description,\n            \"notation\": concept.notation,\n            \"latex\": concept.latex,\n            \"aliases\": list(concept.aliases),\n            \"properties\": concept.properties,\n            \"source_document\": concept.source_document,\n            \"source_page\": concept.source_page,\n            \"confidence\": concept.confidence,\n            \"created_at\": datetime.now().isoformat(),\n            \"updated_at\": datetime.now().isoformat()\n        }\n        \n        try:\n            with self.session() as session:\n                result = session.run(query, parameters)\n                record = result.single()\n                if record:\n                    self.logger.debug(f\"Added concept: {concept.name}\")\n                    return True\n                return False\n        except Exception as e:\n            self.logger.error(f\"Failed to add concept {concept.name}: {e}\")\n            return False\n    \n    def add_relationship(self, relationship: Relationship) -> bool:\n        \"\"\"Add a relationship to the graph database.\"\"\"\n        query = \"\"\"\n        MATCH (source:Concept {id: $source_id})\n        MATCH (target:Concept {id: $target_id})\n        MERGE (source)-[r:RELATED_TO {type: $rel_type}]->(target)\n        SET r.confidence = $confidence,\n            r.properties = $properties,\n            r.source_document = $source_document,\n            r.source_page = $source_page,\n            r.context = $context,\n            r.created_at = $created_at,\n            r.updated_at = $updated_at\n        RETURN r\n        \"\"\"\n        \n        parameters = {\n            \"source_id\": relationship.source_concept_id,\n            \"target_id\": relationship.target_concept_id,\n            \"rel_type\": relationship.relationship_type.value,\n            \"confidence\": relationship.confidence,\n            \"properties\": relationship.properties,\n            \"source_document\": relationship.source_document,\n            \"source_page\": relationship.source_page,\n            \"context\": relationship.context,\n            \"created_at\": datetime.now().isoformat(),\n            \"updated_at\": datetime.now().isoformat()\n        }\n        \n        try:\n            with self.session() as session:\n                result = session.run(query, parameters)\n                record = result.single()\n                if record:\n                    self.logger.debug(f\"Added relationship: {relationship.source_concept_id} -> {relationship.target_concept_id}\")\n                    return True\n                return False\n        except Exception as e:\n            self.logger.error(f\"Failed to add relationship: {e}\")\n            return False\n    \n    def get_concept(self, concept_id: str) -> Optional[Dict[str, Any]]:\n        \"\"\"Retrieve a concept by ID.\"\"\"\n        query = \"MATCH (c:Concept {id: $id}) RETURN c\"\n        \n        try:\n            with self.session() as session:\n                result = session.run(query, {\"id\": concept_id})\n                record = result.single()\n                if record:\n                    return dict(record[\"c\"])\n                return None\n        except Exception as e:\n            self.logger.error(f\"Failed to get concept {concept_id}: {e}\")\n            return None\n    \n    def get_concepts_by_type(self, concept_type: ConceptType) -> List[Dict[str, Any]]:\n        \"\"\"Get all concepts of a specific type.\"\"\"\n        query = \"MATCH (c:Concept {type: $type}) RETURN c ORDER BY c.name\"\n        \n        try:\n            with self.session() as session:\n                result = session.run(query, {\"type\": concept_type.value})\n                return [dict(record[\"c\"]) for record in result]\n        except Exception as e:\n            self.logger.error(f\"Failed to get concepts by type {concept_type}: {e}\")\n            return []\n    \n    def get_related_concepts(self, concept_id: str, \n                           relationship_type: Optional[RelationshipType] = None,\n                           direction: str = \"both\") -> List[Dict[str, Any]]:\n        \"\"\"Get concepts related to a given concept.\"\"\"\n        if direction == \"outgoing\":\n            query = \"MATCH (c:Concept {id: $id})-[r:RELATED_TO]->(related:Concept)\"\n        elif direction == \"incoming\":\n            query = \"MATCH (c:Concept {id: $id})<-[r:RELATED_TO]-(related:Concept)\"\n        else:  # both\n            query = \"MATCH (c:Concept {id: $id})-[r:RELATED_TO]-(related:Concept)\"\n        \n        if relationship_type:\n            query += \" WHERE r.type = $rel_type\"\n        \n        query += \" RETURN related, r ORDER BY r.confidence DESC\"\n        \n        parameters = {\"id\": concept_id}\n        if relationship_type:\n            parameters[\"rel_type\"] = relationship_type.value\n        \n        try:\n            with self.session() as session:\n                result = session.run(query, parameters)\n                return [\n                    {\n                        \"concept\": dict(record[\"related\"]),\n                        \"relationship\": dict(record[\"r\"])\n                    }\n                    for record in result\n                ]\n        except Exception as e:\n            self.logger.error(f\"Failed to get related concepts for {concept_id}: {e}\")\n            return []\n    \n    def search_concepts(self, query_text: str, limit: int = 10) -> List[Dict[str, Any]]:\n        \"\"\"Search for concepts by name or description.\"\"\"\n        query = \"\"\"\n        MATCH (c:Concept)\n        WHERE c.name CONTAINS $query OR c.description CONTAINS $query\n           OR any(alias IN c.aliases WHERE alias CONTAINS $query)\n        RETURN c\n        ORDER BY c.confidence DESC\n        LIMIT $limit\n        \"\"\"\n        \n        try:\n            with self.session() as session:\n                result = session.run(query, {\"query\": query_text, \"limit\": limit})\n                return [dict(record[\"c\"]) for record in result]\n        except Exception as e:\n            self.logger.error(f\"Failed to search concepts: {e}\")\n            return []\n    \n    def get_concept_path(self, source_id: str, target_id: str, \n                        max_length: int = 5) -> List[Dict[str, Any]]:\n        \"\"\"Find the shortest path between two concepts.\"\"\"\n        query = \"\"\"\n        MATCH path = shortestPath((source:Concept {id: $source_id})\n                                 -[:RELATED_TO*1..{max_length}]-\n                                 (target:Concept {id: $target_id}))\n        RETURN path\n        \"\"\".format(max_length=max_length)\n        \n        try:\n            with self.session() as session:\n                result = session.run(query, {\"source_id\": source_id, \"target_id\": target_id})\n                record = result.single()\n                if record:\n                    path = record[\"path\"]\n                    return [\n                        {\n                            \"concept\": dict(node),\n                            \"relationship\": dict(rel) if rel else None\n                        }\n                        for node, rel in zip(path.nodes, path.relationships + [None])\n                    ]\n                return []\n        except Exception as e:\n            self.logger.error(f\"Failed to find path between {source_id} and {target_id}: {e}\")\n            return []\n    \n    def get_concept_neighbors(self, concept_id: str, depth: int = 2) -> Dict[str, Any]:\n        \"\"\"Get all concepts within a specified depth from a given concept.\"\"\"\n        query = \"\"\"\n        MATCH (c:Concept {id: $id})\n        CALL apoc.path.subgraphNodes(c, {\n            relationshipFilter: \"RELATED_TO\",\n            maxLevel: $depth\n        }) YIELD node\n        WITH c, collect(node) AS neighbors\n        MATCH (c)-[r:RELATED_TO*1..{depth}]-(neighbor)\n        RETURN c, neighbors, collect(r) AS relationships\n        \"\"\".format(depth=depth)\n        \n        try:\n            with self.session() as session:\n                result = session.run(query, {\"id\": concept_id, \"depth\": depth})\n                record = result.single()\n                if record:\n                    return {\n                        \"center\": dict(record[\"c\"]),\n                        \"neighbors\": [dict(node) for node in record[\"neighbors\"]],\n                        \"relationships\": [dict(rel) for rel in record[\"relationships\"]]\n                    }\n                return {}\n        except Exception as e:\n            self.logger.error(f\"Failed to get neighbors for {concept_id}: {e}\")\n            return {}\n    \n    def get_document_concepts(self, document_name: str) -> List[Dict[str, Any]]:\n        \"\"\"Get all concepts from a specific document.\"\"\"\n        query = \"\"\"\n        MATCH (c:Concept {source_document: $document})\n        RETURN c\n        ORDER BY c.source_page, c.name\n        \"\"\"\n        \n        try:\n            with self.session() as session:\n                result = session.run(query, {\"document\": document_name})\n                return [dict(record[\"c\"]) for record in result]\n        except Exception as e:\n            self.logger.error(f\"Failed to get concepts from document {document_name}: {e}\")\n            return []\n    \n    def get_statistics(self) -> Dict[str, Any]:\n        \"\"\"Get database statistics.\"\"\"\n        queries = {\n            \"total_concepts\": \"MATCH (c:Concept) RETURN count(c) AS count\",\n            \"total_relationships\": \"MATCH ()-[r:RELATED_TO]->() RETURN count(r) AS count\",\n            \"concepts_by_type\": \"MATCH (c:Concept) RETURN c.type AS type, count(c) AS count ORDER BY count DESC\",\n            \"relationships_by_type\": \"MATCH ()-[r:RELATED_TO]->() RETURN r.type AS type, count(r) AS count ORDER BY count DESC\",\n            \"documents_processed\": \"MATCH (c:Concept) WHERE c.source_document IS NOT NULL RETURN count(DISTINCT c.source_document) AS count\"\n        }\n        \n        stats = {}\n        try:\n            with self.session() as session:\n                for stat_name, query in queries.items():\n                    result = session.run(query)\n                    if stat_name in [\"concepts_by_type\", \"relationships_by_type\"]:\n                        stats[stat_name] = [{\"type\": record[\"type\"], \"count\": record[\"count\"]} for record in result]\n                    else:\n                        record = result.single()\n                        stats[stat_name] = record[\"count\"] if record else 0\n        except Exception as e:\n            self.logger.error(f\"Failed to get statistics: {e}\")\n        \n        return stats\n    \n    def clear_database(self) -> bool:\n        \"\"\"Clear all data from the database (use with caution).\"\"\"\n        query = \"MATCH (n) DETACH DELETE n\"\n        \n        try:\n            with self.session() as session:\n                session.run(query)\n                self.logger.info(\"Database cleared successfully\")\n                return True\n        except Exception as e:\n            self.logger.error(f\"Failed to clear database: {e}\")\n            return False\n    \n    def close(self) -> None:\n        \"\"\"Close the database connection.\"\"\"\n        if self.driver:\n            self.driver.close()\n            self.logger.info(\"Neo4j connection closed\")\n    \n    def __del__(self):\n        \"\"\"Cleanup when object is destroyed.\"\"\"\n        self.close()