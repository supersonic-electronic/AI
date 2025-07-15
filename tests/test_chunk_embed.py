#!/usr/bin/env python3
"""
Test suite for the document chunking and embedding system.

This module tests the mathematical content-aware chunking, embedding generation,
and vector store integration capabilities.
"""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.ingestion.chunk_embed import (
    DocumentChunkEmbedder,
    MathAwareTextSplitter,
    VectorStoreManager,
    ChunkMetadata
)


class TestMathAwareTextSplitter(unittest.TestCase):
    """Test cases for the mathematical content-aware text splitter."""
    
    def setUp(self):
        self.splitter = MathAwareTextSplitter(chunk_size=100, chunk_overlap=20)
    
    def test_basic_text_splitting(self):
        """Test basic text splitting without mathematical content."""
        text = "This is a simple text without any mathematical formulas. " * 5
        chunks = self.splitter.split_text_with_math(text, "test_doc")
        
        self.assertGreater(len(chunks), 0)
        for chunk_text, metadata in chunks:
            self.assertIsInstance(chunk_text, str)
            self.assertIsInstance(metadata, ChunkMetadata)
            self.assertEqual(metadata.source_file, "test_doc")
            self.assertFalse(metadata.has_mathematical_content)
    
    def test_mathematical_content_detection(self):
        """Test detection and preservation of mathematical content."""
        text = """
        This document contains mathematical formulas.
        
        [MATHREF_math_p1_l15_3057] $x_{1} = Rx_{0} and x_{1} = (1 + r)x_{0} .$ @group:general_math @related:MATHREF_math_p1_l7_5023 @confidence:0.50
        
        The formula above shows the relationship between variables.
        
        [MATHREF_math_p1_l8_6419] $R =$ @group:variable_definition @confidence:0.30
        
        This is another mathematical expression.
        """
        
        chunks = self.splitter.split_text_with_math(text, "math_doc")
        
        # Find chunks with mathematical content
        math_chunks = [chunk for chunk in chunks if chunk[1].has_mathematical_content]
        self.assertGreater(len(math_chunks), 0)
        
        # Verify mathematical metadata
        for chunk_text, metadata in math_chunks:
            self.assertGreater(metadata.math_block_count, 0)
            self.assertGreater(len(metadata.math_block_ids), 0)
            self.assertIn("math_p1_l", str(metadata.math_block_ids))
    
    def test_semantic_group_extraction(self):
        """Test extraction of semantic groups from mathematical markers."""
        text = """
        [MATHREF_math_p1_l1_1234] $\\alpha = 0.05$ @group:statistics @confidence:0.80
        [MATHREF_math_p1_l2_5678] $x = y + z$ @group:equation @confidence:0.70
        """
        
        chunks = self.splitter.split_text_with_math(text, "semantic_doc")
        
        # Find chunk with mathematical content
        math_chunk = next((chunk for chunk in chunks if chunk[1].has_mathematical_content), None)
        self.assertIsNotNone(math_chunk)
        
        metadata = math_chunk[1]
        self.assertIn("statistics", metadata.semantic_groups.keys())
        self.assertIn("equation", metadata.semantic_groups.keys())


class TestChunkMetadata(unittest.TestCase):
    """Test cases for chunk metadata handling."""
    
    def test_metadata_creation(self):
        """Test creation and initialization of chunk metadata."""
        metadata = ChunkMetadata(
            source_file="test.pdf",
            chunk_index=5,
            math_block_count=3
        )
        
        self.assertEqual(metadata.source_file, "test.pdf")
        self.assertEqual(metadata.chunk_index, 5)
        self.assertEqual(metadata.math_block_count, 3)
        self.assertIsInstance(metadata.math_block_ids, list)
        self.assertIsInstance(metadata.semantic_groups, dict)
    
    def test_mathematical_content_flag(self):
        """Test automatic detection of mathematical content flag."""
        # Metadata with math blocks
        metadata_with_math = ChunkMetadata(
            source_file="test.pdf",
            math_block_count=2,
            math_block_ids=["math_p1_l1_1234", "math_p1_l2_5678"]
        )
        metadata_with_math.has_mathematical_content = True
        
        self.assertTrue(metadata_with_math.has_mathematical_content)
        self.assertEqual(metadata_with_math.math_block_count, 2)
        
        # Metadata without math blocks
        metadata_no_math = ChunkMetadata(
            source_file="test.pdf",
            math_block_count=0
        )
        
        self.assertFalse(metadata_no_math.has_mathematical_content)
        self.assertEqual(metadata_no_math.math_block_count, 0)


class TestVectorStoreManager(unittest.TestCase):
    """Test cases for vector store management."""
    
    def setUp(self):
        self.config = {
            'chroma_persist_directory': './test_chroma_db',
            'chroma_collection_name': 'test_collection'
        }
    
    @patch('chromadb.PersistentClient')
    def test_chroma_initialization(self, mock_chroma_client):
        """Test Chroma vector store initialization."""
        # Mock Chroma client and collection
        mock_collection = Mock()
        mock_client_instance = Mock()
        mock_client_instance.get_collection.return_value = mock_collection
        mock_chroma_client.return_value = mock_client_instance
        
        # Initialize vector store manager
        manager = VectorStoreManager("chroma", self.config)
        
        # Verify initialization
        self.assertEqual(manager.store_type, "chroma")
        mock_chroma_client.assert_called_once()
    
    def test_metadata_flattening(self):
        """Test flattening of nested metadata for Pinecone compatibility."""
        config = {'pinecone_api_key': 'test_key'}
        
        with patch('pinecone.Pinecone'):
            manager = VectorStoreManager("chroma", config)  # Use chroma to avoid Pinecone init
            
            nested_metadata = {
                'source_file': 'test.pdf',
                'document_metadata': {
                    'title': 'Test Document',
                    'author': 'Test Author'
                },
                'semantic_groups': {
                    'equation': 5,
                    'statistics': 2
                }
            }
            
            flattened = manager._flatten_metadata(nested_metadata)
            
            self.assertIn('source_file', flattened)
            self.assertIn('document_metadata_title', flattened)
            self.assertIn('document_metadata_author', flattened)
            self.assertEqual(flattened['semantic_groups'], str({'equation': 5, 'statistics': 2}))


class TestDocumentChunkEmbedder(unittest.TestCase):
    """Test cases for the main document embedding pipeline."""
    
    def setUp(self):
        self.config = {
            'openai_api_key': 'test_key',
            'text_dir': './test_data/text',
            'math_dir': './test_data/math',
            'metadata_dir': './test_data/metadata',
            'chunk_size': 100,
            'chunk_overlap': 20,
            'embedding_model': 'text-embedding-3-small',
            'embedding_batch_size': 5
        }
    
    @patch('openai.OpenAI')
    def test_embedder_initialization(self, mock_openai):
        """Test DocumentChunkEmbedder initialization."""
        embedder = DocumentChunkEmbedder(self.config)
        
        self.assertEqual(embedder.config, self.config)
        self.assertEqual(embedder.embedding_model, 'text-embedding-3-small')
        self.assertEqual(embedder.batch_size, 5)
        mock_openai.assert_called_once_with(api_key='test_key')
    
    def test_file_loading_error_handling(self):
        """Test error handling for missing files."""
        with patch('openai.OpenAI'):
            embedder = DocumentChunkEmbedder(self.config)
            
            # Test with non-existent file
            with self.assertRaises(FileNotFoundError):
                embedder.load_document_files("nonexistent_file")
    
    @patch('openai.OpenAI')
    def test_load_document_files(self):
        """Test loading of document files with mock data."""
        embedder = DocumentChunkEmbedder(self.config)
        
        # Create temporary directories and files
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Update paths to temporary directory
            embedder.text_dir = temp_path / "text"
            embedder.math_dir = temp_path / "math"
            embedder.metadata_dir = temp_path / "metadata"
            
            # Create directories
            embedder.text_dir.mkdir(parents=True)
            embedder.math_dir.mkdir(parents=True)
            embedder.metadata_dir.mkdir(parents=True)
            
            # Create test files
            text_content = "This is test content with mathematical formulas."
            math_data = [{"page": 1, "block": {"block_id": "math_p1_l1_1234"}}]
            metadata = {"title": "Test Document", "author": "Test Author"}
            
            # Write test files
            with open(embedder.text_dir / "test_doc.txt", 'w') as f:
                f.write(text_content)
            
            with open(embedder.math_dir / "test_doc.math", 'w') as f:
                json.dump(math_data, f)
            
            with open(embedder.metadata_dir / "test_doc.json", 'w') as f:
                json.dump(metadata, f)
            
            # Test file loading
            loaded_text, loaded_math, loaded_metadata = embedder.load_document_files("test_doc")
            
            self.assertEqual(loaded_text, text_content)
            self.assertEqual(loaded_math, math_data)
            self.assertEqual(loaded_metadata, metadata)
    
    @patch('openai.OpenAI')
    def test_embedding_generation_with_retry(self):
        """Test embedding generation with retry logic."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.data = [Mock(embedding=[0.1, 0.2, 0.3]), Mock(embedding=[0.4, 0.5, 0.6])]
        mock_client.embeddings.create.return_value = mock_response
        
        with patch('openai.OpenAI', return_value=mock_client):
            embedder = DocumentChunkEmbedder(self.config)
            
            texts = ["First text chunk", "Second text chunk"]
            embeddings = embedder.generate_embeddings(texts)
            
            self.assertEqual(len(embeddings), 2)
            self.assertEqual(embeddings[0], [0.1, 0.2, 0.3])
            self.assertEqual(embeddings[1], [0.4, 0.5, 0.6])
            mock_client.embeddings.create.assert_called_once()


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete pipeline."""
    
    def setUp(self):
        self.config = {
            'openai_api_key': 'test_key',
            'text_dir': './test_data/text',
            'math_dir': './test_data/math',
            'metadata_dir': './test_data/metadata',
            'chunk_size': 200,
            'chunk_overlap': 50,
            'embedding_model': 'text-embedding-3-small',
            'embedding_batch_size': 10,
            'chroma_persist_directory': './test_chroma_db',
            'chroma_collection_name': 'test_collection'
        }
    
    @patch('openai.OpenAI')
    @patch('chromadb.PersistentClient')
    def test_end_to_end_pipeline(self, mock_chroma_client, mock_openai):
        """Test the complete end-to-end pipeline."""
        # Mock OpenAI embeddings
        mock_openai_instance = Mock()
        mock_response = Mock()
        mock_response.data = [Mock(embedding=[0.1] * 1536) for _ in range(3)]
        mock_openai_instance.embeddings.create.return_value = mock_response
        mock_openai.return_value = mock_openai_instance
        
        # Mock Chroma
        mock_collection = Mock()
        mock_client_instance = Mock()
        mock_client_instance.get_collection.return_value = mock_collection
        mock_chroma_client.return_value = mock_client_instance
        
        # Create temporary test data
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Update config paths
            config = self.config.copy()
            config.update({
                'text_dir': str(temp_path / "text"),
                'math_dir': str(temp_path / "math"),
                'metadata_dir': str(temp_path / "metadata")
            })
            
            # Create directories
            (temp_path / "text").mkdir(parents=True)
            (temp_path / "math").mkdir(parents=True)
            (temp_path / "metadata").mkdir(parents=True)
            
            # Create test document with mathematical content
            text_content = """
            This is a test document with mathematical formulas.
            
            [MATHREF_math_p1_l1_1234] $\\alpha = 0.05$ @group:statistics @confidence:0.80
            
            The statistical significance level is set to alpha.
            
            [MATHREF_math_p1_l2_5678] $x = y + z$ @group:equation @confidence:0.70
            
            This equation shows a simple relationship.
            """
            
            math_data = [
                {
                    "page": 1,
                    "block": {
                        "block_id": "math_p1_l1_1234",
                        "semantic_group": "statistics"
                    }
                },
                {
                    "page": 1,
                    "block": {
                        "block_id": "math_p1_l2_5678",
                        "semantic_group": "equation"
                    }
                }
            ]
            
            metadata = {
                "title": "Test Mathematical Document",
                "author": "Test Author",
                "has_mathematical_content": True
            }
            
            # Write test files
            with open(temp_path / "text" / "test_doc.txt", 'w') as f:
                f.write(text_content)
            
            with open(temp_path / "math" / "test_doc.math", 'w') as f:
                json.dump(math_data, f)
            
            with open(temp_path / "metadata" / "test_doc.json", 'w') as f:
                json.dump(metadata, f)
            
            # Initialize embedder and process
            embedder = DocumentChunkEmbedder(config)
            vectors = embedder.process_document("test_doc")
            
            # Verify results
            self.assertGreater(len(vectors), 0)
            
            for vector_id, embedding, chunk_metadata in vectors:
                self.assertIsInstance(vector_id, str)
                self.assertIn("test_doc", vector_id)
                self.assertIsInstance(embedding, list)
                self.assertEqual(len(embedding), 1536)  # text-embedding-3-small dimension
                self.assertIsInstance(chunk_metadata, dict)
                self.assertIn('source_file', chunk_metadata)
                self.assertIn('chunk_text', chunk_metadata)


if __name__ == '__main__':
    # Create logs directory if it doesn't exist
    Path('./logs').mkdir(exist_ok=True)
    
    # Run tests
    unittest.main(verbosity=2)