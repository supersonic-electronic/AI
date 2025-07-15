#!/usr/bin/env python3
"""
Command-line interface for the portfolio optimizer project.

This module provides a unified CLI with subcommands for different operations:
- ingest: Convert PDFs to text & metadata
- chunk: Split text into chunks  
- embed: Batch-embed chunks into vector stores
- test: Run pytest on ingestion & detection modules
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

from src.logging_config import setup_logging
from src.settings import Settings


def create_parser() -> argparse.ArgumentParser:
    """Create the main argument parser with subcommands."""
    parser = argparse.ArgumentParser(
        description="Portfolio Optimizer: AI-powered document processing and analysis",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Global arguments
    parser.add_argument(
        "--config",
        type=Path,
        default="config.yaml",
        help="Path to configuration YAML file"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging (DEBUG level)"
    )
    
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Enable quiet mode (ERROR level only)"
    )
    
    # Create subparsers
    subparsers = parser.add_subparsers(
        dest="command",
        help="Available commands",
        metavar="{ingest,chunk,embed,test}"
    )
    
    # Ingest subcommand
    ingest_parser = subparsers.add_parser(
        "ingest",
        help="Convert PDFs to text & metadata",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    add_ingest_arguments(ingest_parser)
    
    # Chunk subcommand
    chunk_parser = subparsers.add_parser(
        "chunk",
        help="Split text into chunks",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    add_chunk_arguments(chunk_parser)
    
    # Embed subcommand
    embed_parser = subparsers.add_parser(
        "embed",
        help="Batch-embed chunks into vector stores",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    add_embed_arguments(embed_parser)
    
    # Test subcommand
    test_parser = subparsers.add_parser(
        "test",
        help="Run pytest on ingestion & detection modules",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    add_test_arguments(test_parser)
    
    return parser


def add_ingest_arguments(parser: argparse.ArgumentParser) -> None:
    """Add arguments for the ingest subcommand."""
    parser.add_argument(
        "--input-dir",
        type=Path,
        help="Directory containing PDF files to process"
    )
    
    parser.add_argument(
        "--text-dir", 
        type=Path,
        help="Directory where extracted text files will be saved"
    )
    
    parser.add_argument(
        "--meta-dir",
        type=Path,
        help="Directory where metadata JSON files will be saved"
    )
    
    parser.add_argument(
        "--math-dir",
        type=Path,
        help="Directory where mathematical formula files will be saved"
    )
    
    parser.add_argument(
        "--no-math",
        action="store_true",
        help="Disable mathematical formula extraction"
    )
    
    parser.add_argument(
        "--math-ocr",
        action="store_true",
        help="Enable math OCR fallback (requires API keys)"
    )
    
    parser.add_argument(
        "--parallel-workers",
        type=int,
        help="Number of parallel workers for PDF processing"
    )
    
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip files that already have output"
    )
    
    parser.add_argument(
        "--no-progress",
        action="store_true",
        help="Disable progress bar"
    )


def add_chunk_arguments(parser: argparse.ArgumentParser) -> None:
    """Add arguments for the chunk subcommand."""
    parser.add_argument(
        "--input-dir",
        type=Path,
        help="Directory containing text files to chunk"
    )
    
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Directory where chunk files will be saved"
    )
    
    parser.add_argument(
        "--chunk-size",
        type=int,
        help="Target size for text chunks (characters)"
    )
    
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        help="Overlap between adjacent chunks (characters)"
    )
    
    parser.add_argument(
        "--preserve-math",
        action="store_true",
        help="Preserve mathematical content boundaries"
    )


def add_embed_arguments(parser: argparse.ArgumentParser) -> None:
    """Add arguments for the embed subcommand."""
    parser.add_argument(
        "--input-dir",
        type=Path,
        help="Directory containing chunk files to embed"
    )
    
    parser.add_argument(
        "--vectorstore",
        choices=["pinecone", "chroma"],
        default="chroma",
        help="Vector store to use for embeddings"
    )
    
    parser.add_argument(
        "--local",
        action="store_true",
        help="Use local Chroma database"
    )
    
    parser.add_argument(
        "--namespace",
        type=str,
        help="Namespace for Pinecone index"
    )
    
    parser.add_argument(
        "--batch-size",
        type=int,
        help="Number of texts to embed per batch"
    )
    
    parser.add_argument(
        "--embedding-model",
        type=str,
        help="OpenAI embedding model to use"
    )


def add_test_arguments(parser: argparse.ArgumentParser) -> None:
    """Add arguments for the test subcommand."""
    parser.add_argument(
        "--test-path",
        type=Path,
        default="tests/",
        help="Path to test directory or specific test file"
    )
    
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Run tests with coverage reporting"
    )
    
    parser.add_argument(
        "--markers",
        type=str,
        help="Pytest markers to select tests (e.g., 'unit', 'integration')"
    )
    
    parser.add_argument(
        "--maxfail",
        type=int,
        default=5,
        help="Stop after N test failures"
    )


def run_ingest(args: argparse.Namespace, settings: Settings) -> int:
    """Run the ingest command."""
    try:
        from src.ingestion.pdf2txt import PDFIngestor
        
        # Update settings with command line arguments
        if args.input_dir:
            settings.input_dir = args.input_dir
        if args.text_dir:
            settings.text_dir = args.text_dir
        if args.meta_dir:
            settings.meta_dir = args.meta_dir
        if args.math_dir:
            settings.math_dir = args.math_dir
        if args.no_math:
            settings.extract_math = False
        if args.math_ocr:
            settings.math_ocr_fallback = True
        if args.parallel_workers:
            settings.parallel_workers = args.parallel_workers
        if args.skip_existing:
            settings.skip_existing = True
        if args.no_progress:
            settings.show_progress = False
        
        # Create and run ingestor
        ingestor = PDFIngestor(settings)
        ingestor.process_all()
        
        return 0
        
    except Exception as e:
        logging.error(f"Ingestion failed: {e}")
        return 1


def run_chunk(args: argparse.Namespace, settings: Settings) -> int:
    """Run the chunk command."""
    try:
        from src.ingestion.chunk_embed import DocumentChunker
        
        # Update settings with command line arguments
        if args.input_dir:
            settings.text_dir = args.input_dir
        if args.chunk_size:
            settings.chunk_size = args.chunk_size
        if args.chunk_overlap:
            settings.chunk_overlap = args.chunk_overlap
        
        # Create and run chunker
        chunker = DocumentChunker(settings)
        output_dir = args.output_dir or Path("./data/chunks")
        chunker.process_directory(settings.text_dir, output_dir)
        
        return 0
        
    except Exception as e:
        logging.error(f"Chunking failed: {e}")
        return 1


def run_embed(args: argparse.Namespace, settings: Settings) -> int:
    """Run the embed command."""
    try:
        from src.ingestion.chunk_embed import EmbeddingPipeline
        
        # Update settings with command line arguments
        if args.batch_size:
            settings.embedding_batch_size = args.batch_size
        if args.embedding_model:
            settings.embedding_model = args.embedding_model
        if args.namespace:
            settings.pinecone_namespace = args.namespace
        
        # Determine vector store
        use_local = args.local or args.vectorstore == "chroma"
        
        # Create and run embedding pipeline
        pipeline = EmbeddingPipeline(settings)
        input_dir = args.input_dir or Path("./data/chunks")
        
        if use_local:
            pipeline.embed_to_chroma(input_dir)
        else:
            pipeline.embed_to_pinecone(input_dir, namespace=args.namespace)
        
        return 0
        
    except Exception as e:
        logging.error(f"Embedding failed: {e}")
        return 1


def run_test(args: argparse.Namespace, settings: Settings) -> int:
    """Run the test command."""
    try:
        import subprocess
        
        # Build pytest command
        cmd = ["pytest"]
        
        # Add test path
        cmd.append(str(args.test_path))
        
        # Add coverage if requested
        if args.coverage:
            cmd.extend(["--cov=src", "--cov-report=html", "--cov-report=term"])
        
        # Add markers if specified
        if args.markers:
            cmd.extend(["-m", args.markers])
        
        # Add maxfail
        cmd.extend([f"--maxfail={args.maxfail}"])
        
        # Add verbose output
        cmd.append("-v")
        
        # Run pytest
        result = subprocess.run(cmd, cwd=Path.cwd())
        return result.returncode
        
    except Exception as e:
        logging.error(f"Testing failed: {e}")
        return 1


def main() -> int:
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Show help if no command provided
    if not args.command:
        parser.print_help()
        return 1
    
    try:
        # Load settings
        settings = Settings.from_env_and_yaml(args.config)
        
        # Override log level based on verbosity
        if args.verbose:
            settings.log_level = "DEBUG"
        elif args.quiet:
            settings.log_level = "ERROR"
        
        # Setup logging
        setup_logging(settings)
        
        # Create directories
        settings.create_directories()
        
        # Route to appropriate command handler
        if args.command == "ingest":
            return run_ingest(args, settings)
        elif args.command == "chunk":
            return run_chunk(args, settings)
        elif args.command == "embed":
            return run_embed(args, settings)
        elif args.command == "test":
            return run_test(args, settings)
        else:
            logging.error(f"Unknown command: {args.command}")
            return 1
            
    except Exception as e:
        logging.error(f"CLI execution failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())