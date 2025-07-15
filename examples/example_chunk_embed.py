#!/usr/bin/env python3
"""
Example script demonstrating the document chunking and embedding pipeline.

This script shows how to use the chunk_embed module to process documents
with mathematical content, generate embeddings, and store them in a vector database.
"""

import sys
import os
from pathlib import Path
import yaml
import tempfile
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.ingestion.chunk_embed import DocumentChunkEmbedder, VectorStoreManager


def create_sample_documents():
    """Create sample documents with mathematical content for testing."""
    
    # Create temporary directory structure
    base_dir = Path("./example_data")
    text_dir = base_dir / "text"
    math_dir = base_dir / "math"
    metadata_dir = base_dir / "metadata"
    
    # Create directories
    for directory in [text_dir, math_dir, metadata_dir]:
        directory.mkdir(parents=True, exist_ok=True)
    
    # Sample document 1: Portfolio theory
    portfolio_text = """
Portfolio Optimization Theory

Modern portfolio theory (MPT) is a mathematical framework for assembling a portfolio of assets such that the expected return is maximized for a given level of risk.

[MATHREF_math_p1_l1_1234] $E(R_p) = \\sum_{i=1}^{n} w_i E(R_i)$ @group:portfolio_theory @confidence:0.90

The expected return of a portfolio is the weighted average of the expected returns of the individual assets.

[MATHREF_math_p1_l2_5678] $\\sigma_p^2 = \\sum_{i=1}^{n} \\sum_{j=1}^{n} w_i w_j \\sigma_{ij}$ @group:portfolio_theory @confidence:0.85

The portfolio variance depends on the weights and the covariance matrix of the assets.

[MATHREF_math_p1_l3_9012] $\\text{Sharpe Ratio} = \\frac{E(R_p) - R_f}{\\sigma_p}$ @group:ratio @confidence:0.80

The Sharpe ratio measures risk-adjusted return.
"""
    
    portfolio_math = [
        {
            "page": 1,
            "block": {
                "block_id": "math_p1_l1_1234",
                "page_num": 1,
                "raw_text": "E(R_p) = sum_{i=1}^{n} w_i E(R_i)",
                "latex": "$E(R_p) = \\sum_{i=1}^{n} w_i E(R_i)$",
                "confidence": 0.90,
                "semantic_group": "portfolio_theory",
                "related_blocks": ["math_p1_l2_5678"],
                "context": {"before": "framework", "after": "weighted average"}
            }
        },
        {
            "page": 1,
            "block": {
                "block_id": "math_p1_l2_5678",
                "page_num": 1,
                "raw_text": "sigma_p^2 = sum_{i=1}^{n} sum_{j=1}^{n} w_i w_j sigma_{ij}",
                "latex": "$\\sigma_p^2 = \\sum_{i=1}^{n} \\sum_{j=1}^{n} w_i w_j \\sigma_{ij}$",
                "confidence": 0.85,
                "semantic_group": "portfolio_theory",
                "related_blocks": ["math_p1_l1_1234"],
                "context": {"before": "weighted average", "after": "covariance matrix"}
            }
        },
        {
            "page": 1,
            "block": {
                "block_id": "math_p1_l3_9012",
                "page_num": 1,
                "raw_text": "Sharpe Ratio = (E(R_p) - R_f) / sigma_p",
                "latex": "$\\text{Sharpe Ratio} = \\frac{E(R_p) - R_f}{\\sigma_p}$",
                "confidence": 0.80,
                "semantic_group": "ratio",
                "related_blocks": [],
                "context": {"before": "covariance matrix", "after": "risk-adjusted"}
            }
        }
    ]
    
    portfolio_metadata = {
        "filename": "portfolio_theory.pdf",
        "title": "Modern Portfolio Theory",
        "author": "Harry Markowitz",
        "subject": "Finance, Portfolio Optimization",
        "has_mathematical_content": True,
        "math_blocks_count": 3,
        "semantic_groups": {
            "portfolio_theory": 2,
            "ratio": 1
        }
    }
    
    # Sample document 2: Statistics
    stats_text = """
Statistical Inference

Statistical inference is the process of using data analysis to infer properties of an underlying distribution of probability.

[MATHREF_math_p1_l1_2468] $H_0: \\mu = \\mu_0$ @group:statistics @confidence:0.95

The null hypothesis states that the population mean equals a specific value.

[MATHREF_math_p1_l2_1357] $\\alpha = P(\\text{Type I Error}) = P(\\text{Reject } H_0 | H_0 \\text{ is true})$ @group:statistics @confidence:0.90

The significance level alpha represents the probability of Type I error.

[MATHREF_math_p1_l3_8642] $t = \\frac{\\bar{x} - \\mu_0}{s/\\sqrt{n}}$ @group:equation @confidence:0.85

The t-statistic for hypothesis testing.
"""
    
    stats_math = [
        {
            "page": 1,
            "block": {
                "block_id": "math_p1_l1_2468",
                "page_num": 1,
                "raw_text": "H_0: mu = mu_0",
                "latex": "$H_0: \\mu = \\mu_0$",
                "confidence": 0.95,
                "semantic_group": "statistics",
                "related_blocks": ["math_p1_l2_1357"],
                "context": {"before": "inference", "after": "null hypothesis"}
            }
        },
        {
            "page": 1,
            "block": {
                "block_id": "math_p1_l2_1357",
                "page_num": 1,
                "raw_text": "alpha = P(Type I Error) = P(Reject H_0 | H_0 is true)",
                "latex": "$\\alpha = P(\\text{Type I Error}) = P(\\text{Reject } H_0 | H_0 \\text{ is true})$",
                "confidence": 0.90,
                "semantic_group": "statistics",
                "related_blocks": ["math_p1_l1_2468"],
                "context": {"before": "null hypothesis", "after": "significance level"}
            }
        },
        {
            "page": 1,
            "block": {
                "block_id": "math_p1_l3_8642",
                "page_num": 1,
                "raw_text": "t = (x_bar - mu_0) / (s / sqrt(n))",
                "latex": "$t = \\frac{\\bar{x} - \\mu_0}{s/\\sqrt{n}}$",
                "confidence": 0.85,
                "semantic_group": "equation",
                "related_blocks": [],
                "context": {"before": "significance level", "after": "t-statistic"}
            }
        }
    ]
    
    stats_metadata = {
        "filename": "statistical_inference.pdf",
        "title": "Introduction to Statistical Inference",
        "author": "R.A. Fisher",
        "subject": "Statistics, Hypothesis Testing",
        "has_mathematical_content": True,
        "math_blocks_count": 3,
        "semantic_groups": {
            "statistics": 2,
            "equation": 1
        }
    }
    
    # Write files
    documents = [
        ("portfolio_theory", portfolio_text, portfolio_math, portfolio_metadata),
        ("statistical_inference", stats_text, stats_math, stats_metadata)
    ]
    
    for doc_name, text, math, metadata in documents:
        # Write text file
        with open(text_dir / f"{doc_name}.txt", 'w', encoding='utf-8') as f:
            f.write(text)
        
        # Write math file
        with open(math_dir / f"{doc_name}.math", 'w', encoding='utf-8') as f:
            json.dump(math, f, indent=2)
        
        # Write metadata file
        with open(metadata_dir / f"{doc_name}.json", 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
    
    print(f"✓ Created sample documents in {base_dir}")
    return base_dir


def run_example():
    """Run the complete example pipeline."""
    
    print("Document Chunking and Embedding Example")
    print("=" * 50)
    
    # Step 1: Create sample documents
    print("\n1. Creating sample documents...")
    data_dir = create_sample_documents()
    
    # Step 2: Setup configuration
    print("\n2. Setting up configuration...")
    config = {
        # API keys (would normally be set via environment variables)
        'openai_api_key': 'your-openai-api-key-here',  # Replace with real key
        
        # Paths
        'text_dir': str(data_dir / "text"),
        'math_dir': str(data_dir / "math"),
        'metadata_dir': str(data_dir / "metadata"),
        
        # Chunking settings
        'chunk_size': 300,
        'chunk_overlap': 50,
        
        # Embedding settings
        'embedding_model': 'text-embedding-3-small',
        'embedding_batch_size': 10,
        'max_retries': 3,
        'retry_delay': 1.0,
        
        # Chroma settings (for local example)
        'chroma_persist_directory': str(data_dir / "chroma_db"),
        'chroma_collection_name': 'example_documents'
    }
    
    print(f"✓ Configuration ready")
    
    # Step 3: Test chunking (without embeddings for demo)
    print("\n3. Testing document chunking...")
    
    try:
        # Initialize embedder (will fail if no OpenAI key, but we can test chunking)
        from src.ingestion.chunk_embed import MathAwareTextSplitter
        
        splitter = MathAwareTextSplitter(
            chunk_size=config['chunk_size'],
            chunk_overlap=config['chunk_overlap']
        )
        
        # Test with one of our sample documents
        with open(data_dir / "text" / "portfolio_theory.txt", 'r') as f:
            sample_text = f.read()
        
        chunks = splitter.split_text_with_math(sample_text, "portfolio_theory")
        
        print(f"✓ Generated {len(chunks)} chunks from portfolio_theory document")
        
        # Show chunk analysis
        for i, (chunk_text, metadata) in enumerate(chunks):
            print(f"\n  Chunk {i}:")
            print(f"    Length: {len(chunk_text)} characters")
            print(f"    Math blocks: {metadata.math_block_count}")
            if metadata.has_mathematical_content:
                print(f"    Math IDs: {metadata.math_block_ids}")
                print(f"    Semantic groups: {metadata.semantic_groups}")
                print(f"    Confidence scores: {metadata.confidence_scores}")
            print(f"    Preview: {chunk_text[:100]}...")
        
    except Exception as e:
        print(f"✗ Chunking test failed: {e}")
        return
    
    # Step 4: Show what would happen with full pipeline
    print("\n4. Full pipeline demonstration (requires API keys)...")
    print("""
To run the complete pipeline with embeddings and vector storage:

1. Set your OpenAI API key in the configuration:
   config['openai_api_key'] = 'your-actual-api-key'

2. For Pinecone (cloud):
   config['pinecone_api_key'] = 'your-pinecone-api-key'
   config['pinecone_index_name'] = 'document-embeddings'

3. Run the embedder:
   embedder = DocumentChunkEmbedder(config)
   stats = embedder.process_all(vector_store_type='chroma')  # or 'pinecone'

4. Example command line usage:
   python src/ingestion/chunk_embed.py --input-dir ./example_data/text --local --verbose
""")
    
    # Step 5: CLI usage examples
    print("\n5. CLI Usage Examples:")
    print("""
# Process documents with local Chroma database
python src/ingestion/chunk_embed.py --local --verbose

# Process with Pinecone (requires API key in config)
python src/ingestion/chunk_embed.py --vectorstore pinecone --namespace research_docs

# Custom input directory
python src/ingestion/chunk_embed.py --input-dir ./example_data/text --local

# With custom configuration
python src/ingestion/chunk_embed.py --config custom_config.yaml --local
""")
    
    print("\n✓ Example completed successfully!")
    print(f"\nSample data created in: {data_dir}")
    print("You can now test the full pipeline with your API keys.")


def cleanup_example():
    """Clean up example files."""
    import shutil
    
    example_dir = Path("./example_data")
    if example_dir.exists():
        shutil.rmtree(example_dir)
        print(f"✓ Cleaned up {example_dir}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Document chunking and embedding example")
    parser.add_argument("--cleanup", action="store_true", help="Clean up example files")
    args = parser.parse_args()
    
    if args.cleanup:
        cleanup_example()
    else:
        run_example()