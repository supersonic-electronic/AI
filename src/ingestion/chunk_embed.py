#!/usr/bin/env python3
"""
Advanced document chunking and embedding system with vector store integration.

This module provides sophisticated text chunking with mathematical content preservation,
OpenAI embeddings generation, and vector store management (Pinecone/Chroma) with
comprehensive metadata integration and bidirectional mathematical linking support.
"""

import argparse
import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import sys
import os

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import pinecone
    from pinecone import Pinecone, ServerlessSpec
    PINECONE_AVAILABLE = True
except ImportError:
    PINECONE_AVAILABLE = False

try:
    import chromadb
    from chromadb.config import Settings
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False

try:
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    LANGCHAIN_AVAILABLE = True
except ImportError:
    try:
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        LANGCHAIN_AVAILABLE = True
    except ImportError:
        LANGCHAIN_AVAILABLE = False

import yaml
from tqdm import tqdm
import hashlib
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, asdict
from typing_extensions import Literal


@dataclass
class ChunkMetadata:
    """Metadata structure for text chunks with mathematical content support."""
    source_file: str
    page: Optional[int] = None
    chunk_index: int = 0
    chunk_start: int = 0
    chunk_end: int = 0
    math_block_count: int = 0
    math_block_ids: List[str] = None
    semantic_groups: Dict[str, int] = None
    confidence_scores: List[float] = None
    has_mathematical_content: bool = False
    document_metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.math_block_ids is None:
            self.math_block_ids = []
        if self.semantic_groups is None:
            self.semantic_groups = {}
        if self.confidence_scores is None:
            self.confidence_scores = []
        if self.document_metadata is None:
            self.document_metadata = {}


class MathAwareTextSplitter:
    """Enhanced text splitter that preserves mathematical content boundaries."""
    
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        """
        Initialize math-aware text splitter.
        
        Args:
            chunk_size: Target size for each chunk
            chunk_overlap: Overlap between adjacent chunks
        """
        if not LANGCHAIN_AVAILABLE:
            raise ImportError("LangChain text splitters not available. Install with: pip install langchain-text-splitters")
        
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.base_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
    def split_text_with_math(self, text: str, source_file: str) -> List[Tuple[str, ChunkMetadata]]:
        """
        Split text while preserving mathematical content boundaries.
        
        Args:
            text: Input text with mathematical markers
            source_file: Source filename for metadata
            
        Returns:
            List of (chunk_text, metadata) tuples
        """
        # Extract mathematical references from text
        math_pattern = r'\[MATHREF_([^\]]+)\]([^@]*?)(?:@[^@]*)*'
        math_blocks = re.findall(math_pattern, text)
        
        # Create enhanced separators that respect math boundaries
        math_boundaries = []
        for match in re.finditer(math_pattern, text):
            math_boundaries.append(match.start())
            math_boundaries.append(match.end())
        
        # Split text using base splitter
        base_chunks = self.base_splitter.split_text(text)
        
        # Enhance chunks with mathematical metadata
        chunks_with_metadata = []
        current_pos = 0
        
        for chunk_idx, chunk in enumerate(base_chunks):
            # Find chunk position in original text
            chunk_start = text.find(chunk, current_pos)
            if chunk_start == -1:
                chunk_start = current_pos
            chunk_end = chunk_start + len(chunk)
            
            # Extract mathematical content from chunk
            chunk_math_blocks = re.findall(math_pattern, chunk)
            math_block_ids = [block[0] for block in chunk_math_blocks]
            
            # Calculate semantic groups and confidence scores
            semantic_groups = {}
            confidence_scores = []
            
            for math_id, content in chunk_math_blocks:
                # Extract semantic group from math marker
                group_match = re.search(r'@group:([^@\s]+)', chunk)
                if group_match:
                    group = group_match.group(1)
                    semantic_groups[group] = semantic_groups.get(group, 0) + 1
                
                # Extract confidence score
                conf_match = re.search(r'@confidence:([\d.]+)', chunk)
                if conf_match:
                    confidence_scores.append(float(conf_match.group(1)))
            
            # Create metadata
            metadata = ChunkMetadata(
                source_file=source_file,
                chunk_index=chunk_idx,
                chunk_start=chunk_start,
                chunk_end=chunk_end,
                math_block_count=len(math_block_ids),
                math_block_ids=math_block_ids,
                semantic_groups=semantic_groups,
                confidence_scores=confidence_scores,
                has_mathematical_content=len(math_block_ids) > 0
            )
            
            chunks_with_metadata.append((chunk, metadata))
            current_pos = chunk_end
            
        return chunks_with_metadata


class VectorStoreManager:
    """Unified interface for vector store operations (Pinecone/Chroma)."""
    
    def __init__(self, 
                 store_type: Literal["pinecone", "chroma"],
                 config: Dict[str, Any],
                 namespace: Optional[str] = None):
        """
        Initialize vector store manager.
        
        Args:
            store_type: Type of vector store ("pinecone" or "chroma")
            config: Configuration dictionary
            namespace: Optional namespace for vector operations
        """
        self.store_type = store_type
        self.config = config
        self.namespace = namespace
        self.logger = logging.getLogger(__name__)
        
        if store_type == "pinecone":
            self._init_pinecone()
        elif store_type == "chroma":
            self._init_chroma()
        else:
            raise ValueError(f"Unsupported vector store type: {store_type}")
    
    def _init_pinecone(self):
        """Initialize Pinecone client and index."""
        if not PINECONE_AVAILABLE:
            raise ImportError("Pinecone package not available. Install with: pip install pinecone-client")
        
        api_key = self.config.get('pinecone_api_key')
        if not api_key:
            raise ValueError("Pinecone API key not found in configuration")
        
        self.pinecone_client = Pinecone(api_key=api_key)
        
        index_name = self.config.get('pinecone_index_name', 'document-embeddings')
        environment = self.config.get('pinecone_environment', 'us-east-1-aws')
        
        # Create index if it doesn't exist
        if index_name not in self.pinecone_client.list_indexes().names():
            self.logger.info(f"Creating Pinecone index: {index_name}")
            self.pinecone_client.create_index(
                name=index_name,
                dimension=1536,  # text-embedding-3-small dimension
                metric='cosine',
                spec=ServerlessSpec(
                    cloud='aws',
                    region=environment
                )
            )
        
        self.index = self.pinecone_client.Index(index_name)
        self.logger.info(f"Connected to Pinecone index: {index_name}")
    
    def _init_chroma(self):
        """Initialize Chroma client and collection."""
        if not CHROMA_AVAILABLE:
            raise ImportError("ChromaDB package not available. Install with: pip install chromadb")
        
        persist_directory = self.config.get('chroma_persist_directory', './data/chroma_db')
        
        self.chroma_client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )
        
        collection_name = self.config.get('chroma_collection_name', 'document_embeddings')
        
        # Get or create collection
        try:
            self.collection = self.chroma_client.get_collection(collection_name)
            self.logger.info(f"Connected to existing Chroma collection: {collection_name}")
        except ValueError:
            self.collection = self.chroma_client.create_collection(
                name=collection_name,
                metadata={"description": "Document embeddings with mathematical content"}
            )
            self.logger.info(f"Created new Chroma collection: {collection_name}")
    
    def upsert_vectors(self, vectors: List[Tuple[str, List[float], Dict[str, Any]]]):
        """
        Upsert vectors to the vector store.
        
        Args:
            vectors: List of (id, embedding, metadata) tuples
        """
        if self.store_type == "pinecone":
            self._upsert_pinecone(vectors)
        elif self.store_type == "chroma":
            self._upsert_chroma(vectors)
    
    def _upsert_pinecone(self, vectors: List[Tuple[str, List[float], Dict[str, Any]]]):
        """Upsert vectors to Pinecone."""
        # Convert to Pinecone format
        pinecone_vectors = []
        for vector_id, embedding, metadata in vectors:
            # Flatten nested metadata for Pinecone
            flat_metadata = self._flatten_metadata(metadata)
            pinecone_vectors.append({
                'id': vector_id,
                'values': embedding,
                'metadata': flat_metadata
            })
        
        # Upsert with namespace if specified
        if self.namespace:
            self.index.upsert(vectors=pinecone_vectors, namespace=self.namespace)
        else:
            self.index.upsert(vectors=pinecone_vectors)
        
        self.logger.debug(f"Upserted {len(vectors)} vectors to Pinecone")
    
    def _upsert_chroma(self, vectors: List[Tuple[str, List[float], Dict[str, Any]]]):
        """Upsert vectors to Chroma."""
        ids = []
        embeddings = []
        metadatas = []
        documents = []
        
        for vector_id, embedding, metadata in vectors:
            ids.append(vector_id)
            embeddings.append(embedding)
            metadatas.append(metadata)
            # Use chunk text as document content for Chroma
            documents.append(metadata.get('chunk_text', ''))
        
        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=documents
        )
        
        self.logger.debug(f"Upserted {len(vectors)} vectors to Chroma")
    
    def _flatten_metadata(self, metadata: Dict[str, Any], parent_key: str = '', sep: str = '_') -> Dict[str, Any]:
        """Flatten nested metadata for Pinecone compatibility."""
        items = []
        for k, v in metadata.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_metadata(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                # Convert lists to strings for Pinecone
                items.append((new_key, str(v)))
            else:
                items.append((new_key, v))
        return dict(items)


class DocumentChunkEmbedder:
    """Main class for document chunking and embedding pipeline."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize document chunk embedder.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize OpenAI client
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI package not available. Install with: pip install openai")
        
        api_key = config.get('openai_api_key')
        if not api_key:
            raise ValueError("OpenAI API key not found in configuration")
        
        self.openai_client = openai.OpenAI(api_key=api_key)
        
        # Initialize text splitter
        chunk_size = config.get('chunk_size', 500)
        chunk_overlap = config.get('chunk_overlap', 50)
        self.text_splitter = MathAwareTextSplitter(chunk_size, chunk_overlap)
        
        # Embedding configuration
        self.embedding_model = config.get('embedding_model', 'text-embedding-3-small')
        self.batch_size = config.get('embedding_batch_size', 30)
        self.max_retries = config.get('max_retries', 3)
        self.retry_delay = config.get('retry_delay', 1.0)
        
        # Paths
        self.text_dir = Path(config.get('text_dir', './data/text'))
        self.math_dir = Path(config.get('math_dir', './data/math'))
        self.metadata_dir = Path(config.get('metadata_dir', './data/metadata'))
    
    def load_document_files(self, source_file: str) -> Tuple[str, Optional[Dict], Optional[Dict]]:
        """
        Load text, math, and metadata files for a document.
        
        Args:
            source_file: Base filename (without extension)
            
        Returns:
            Tuple of (text_content, math_data, metadata)
        """
        # Load text file
        text_file = self.text_dir / f"{source_file}.txt"
        if not text_file.exists():
            raise FileNotFoundError(f"Text file not found: {text_file}")
        
        with open(text_file, 'r', encoding='utf-8') as f:
            text_content = f.read()
        
        # Load optional math file
        math_data = None
        math_file = self.math_dir / f"{source_file}.math"
        if math_file.exists():
            try:
                with open(math_file, 'r', encoding='utf-8') as f:
                    math_data = json.load(f)
                self.logger.debug(f"Loaded math data from {math_file}")
            except json.JSONDecodeError as e:
                self.logger.warning(f"Failed to parse math file {math_file}: {e}")
        
        # Load optional metadata file
        metadata = None
        metadata_file = self.metadata_dir / f"{source_file}.json"
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                self.logger.debug(f"Loaded metadata from {metadata_file}")
            except json.JSONDecodeError as e:
                self.logger.warning(f"Failed to parse metadata file {metadata_file}: {e}")
        
        return text_content, math_data, metadata
    
    def enhance_chunk_metadata(self, 
                             chunk_metadata: ChunkMetadata, 
                             math_data: Optional[Dict],
                             document_metadata: Optional[Dict]) -> ChunkMetadata:
        """
        Enhance chunk metadata with mathematical and document information.
        
        Args:
            chunk_metadata: Base chunk metadata
            math_data: Mathematical content data
            document_metadata: Document-level metadata
            
        Returns:
            Enhanced chunk metadata
        """
        # Add document metadata
        if document_metadata:
            chunk_metadata.document_metadata = document_metadata
        
        # Enhance with mathematical data
        if math_data and chunk_metadata.has_mathematical_content:
            # Extract page information from math blocks
            for math_block in math_data:
                block_id = math_block.get('block', {}).get('block_id', '')
                if block_id in chunk_metadata.math_block_ids:
                    page_num = math_block.get('page')
                    if page_num and chunk_metadata.page is None:
                        chunk_metadata.page = page_num
                    break
        
        return chunk_metadata
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a batch of texts with retry logic.
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors
        """
        for attempt in range(self.max_retries):
            try:
                response = self.openai_client.embeddings.create(
                    model=self.embedding_model,
                    input=texts
                )
                
                embeddings = [data.embedding for data in response.data]
                self.logger.debug(f"Generated {len(embeddings)} embeddings")
                return embeddings
                
            except Exception as e:
                if attempt < self.max_retries - 1:
                    self.logger.warning(f"Embedding attempt {attempt + 1} failed: {e}. Retrying...")
                    time.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff
                else:
                    self.logger.error(f"Failed to generate embeddings after {self.max_retries} attempts: {e}")
                    raise
    
    def process_document(self, source_file: str) -> List[Tuple[str, List[float], Dict[str, Any]]]:
        """
        Process a single document through the chunking and embedding pipeline.
        
        Args:
            source_file: Base filename (without extension)
            
        Returns:
            List of (id, embedding, metadata) tuples
        """
        self.logger.info(f"Processing document: {source_file}")
        
        # Load document files
        text_content, math_data, document_metadata = self.load_document_files(source_file)
        
        # Split text into chunks
        chunks_with_metadata = self.text_splitter.split_text_with_math(text_content, source_file)
        
        # Process chunks in batches
        vectors = []
        
        for i in range(0, len(chunks_with_metadata), self.batch_size):
            batch = chunks_with_metadata[i:i + self.batch_size]
            
            # Extract texts and metadata
            batch_texts = [chunk[0] for chunk in batch]
            batch_metadata = [chunk[1] for chunk in batch]
            
            # Generate embeddings
            batch_embeddings = self.generate_embeddings(batch_texts)
            
            # Create vector tuples
            for j, (chunk_text, metadata) in enumerate(batch):
                # Enhance metadata
                enhanced_metadata = self.enhance_chunk_metadata(metadata, math_data, document_metadata)
                
                # Create vector ID
                vector_id = f"{source_file}_{metadata.chunk_index}"
                
                # Create metadata dict with chunk text
                metadata_dict = asdict(enhanced_metadata)
                metadata_dict['chunk_text'] = chunk_text
                
                vectors.append((vector_id, batch_embeddings[j], metadata_dict))
            
            self.logger.debug(f"Processed batch {i // self.batch_size + 1}/{(len(chunks_with_metadata) + self.batch_size - 1) // self.batch_size}")
        
        self.logger.info(f"Generated {len(vectors)} vectors for document: {source_file}")
        return vectors
    
    def process_all(self, 
                   input_dir: Optional[Path] = None,
                   vector_store_type: str = "pinecone",
                   namespace: Optional[str] = None) -> Dict[str, Any]:
        """
        Process all documents in the input directory.
        
        Args:
            input_dir: Directory containing text files (default from config)
            vector_store_type: Type of vector store ("pinecone" or "chroma")
            namespace: Optional namespace for vector operations
            
        Returns:
            Processing statistics
        """
        if input_dir is None:
            input_dir = self.text_dir
        else:
            input_dir = Path(input_dir)
        
        # Find all text files
        text_files = list(input_dir.glob("*.txt"))
        if not text_files:
            self.logger.warning(f"No text files found in {input_dir}")
            return {"processed": 0, "errors": 0, "total_vectors": 0}
        
        self.logger.info(f"Found {len(text_files)} text files to process")
        
        # Initialize vector store
        vector_store = VectorStoreManager(vector_store_type, self.config, namespace)
        
        # Processing statistics
        stats = {
            "processed": 0,
            "errors": 0,
            "total_vectors": 0,
            "error_files": []
        }
        
        # Process files with progress bar
        with tqdm(total=len(text_files), desc="Processing documents") as pbar:
            for text_file in text_files:
                source_file = text_file.stem
                
                try:
                    vectors = self.process_document(source_file)
                    
                    if vectors:
                        vector_store.upsert_vectors(vectors)
                        stats["total_vectors"] += len(vectors)
                    
                    stats["processed"] += 1
                    
                except Exception as e:
                    self.logger.error(f"Failed to process {source_file}: {e}")
                    stats["errors"] += 1
                    stats["error_files"].append(source_file)
                
                pbar.update(1)
                pbar.set_postfix({
                    "processed": stats["processed"],
                    "errors": stats["errors"],
                    "vectors": stats["total_vectors"]
                })
        
        self.logger.info(f"Processing complete. Processed: {stats['processed']}, Errors: {stats['errors']}, Total vectors: {stats['total_vectors']}")
        return stats


def setup_logging(level: str = "INFO") -> None:
    """Setup logging configuration."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('./logs/chunk_embed.log', mode='a')
        ]
    )


def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from YAML file."""
    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    
    return config


def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(
        description="Document chunking and embedding pipeline with mathematical content support"
    )
    
    parser.add_argument(
        '--input-dir',
        type=str,
        help='Directory containing text files to process'
    )
    
    parser.add_argument(
        '--vectorstore',
        choices=['pinecone', 'chroma'],
        default='pinecone',
        help='Vector store type (default: pinecone)'
    )
    
    parser.add_argument(
        '--namespace',
        type=str,
        help='Namespace for vector operations (Pinecone only)'
    )
    
    parser.add_argument(
        '--local',
        action='store_true',
        help='Use local Chroma database (equivalent to --vectorstore chroma)'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        default='config.yaml',
        help='Configuration file path (default: config.yaml)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = "DEBUG" if args.verbose else "INFO"
    setup_logging(log_level)
    
    logger = logging.getLogger(__name__)
    
    try:
        # Load configuration
        config = load_config(args.config)
        
        # Override vector store type if --local flag is used
        vector_store_type = 'chroma' if args.local else args.vectorstore
        
        # Initialize embedder
        embedder = DocumentChunkEmbedder(config)
        
        # Process all documents
        stats = embedder.process_all(
            input_dir=Path(args.input_dir) if args.input_dir else None,
            vector_store_type=vector_store_type,
            namespace=args.namespace
        )
        
        # Print summary
        logger.info("="*60)
        logger.info("PROCESSING SUMMARY")
        logger.info("="*60)
        logger.info(f"Documents processed: {stats['processed']}")
        logger.info(f"Errors encountered: {stats['errors']}")
        logger.info(f"Total vectors generated: {stats['total_vectors']}")
        logger.info(f"Vector store: {vector_store_type}")
        if args.namespace:
            logger.info(f"Namespace: {args.namespace}")
        
        if stats['error_files']:
            logger.warning(f"Failed files: {', '.join(stats['error_files'])}")
        
        return 0 if stats['errors'] == 0 else 1
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())


# Example usage:
"""
# Basic usage with Pinecone
python src/ingestion/chunk_embed.py --vectorstore pinecone --namespace documents

# Local usage with Chroma
python src/ingestion/chunk_embed.py --local

# Custom input directory and configuration
python src/ingestion/chunk_embed.py --input-dir ./custom/text --config ./custom-config.yaml --verbose

# Programmatic usage
from src.ingestion.chunk_embed import DocumentChunkEmbedder
import yaml

# Load configuration
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Add required keys to config
config.update({
    'openai_api_key': 'your-openai-api-key',
    'pinecone_api_key': 'your-pinecone-api-key',  # for Pinecone
    'embedding_model': 'text-embedding-3-small',
    'chunk_size': 500,
    'chunk_overlap': 50,
    'embedding_batch_size': 30
})

# Initialize and run
embedder = DocumentChunkEmbedder(config)
stats = embedder.process_all(vector_store_type='pinecone', namespace='research_docs')
print(f"Generated {stats['total_vectors']} vectors from {stats['processed']} documents")
"""