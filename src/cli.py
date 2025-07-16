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
from src.config_validator import validate_and_transform_config, ConfigValidationError


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
        metavar="{ingest,chunk,embed,test,graph,watch,batch,serve}"
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
    
    # Graph subcommand
    graph_parser = subparsers.add_parser(
        "graph",
        help="Graph database operations",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    add_graph_arguments(graph_parser)
    
    # Watch subcommand
    watch_parser = subparsers.add_parser(
        "watch",
        help="Watch directories for real-time document processing",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    add_watch_arguments(watch_parser)
    
    # Batch subcommand
    batch_parser = subparsers.add_parser(
        "batch",
        help="Batch processing of multiple documents",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    add_batch_arguments(batch_parser)
    
    # Serve subcommand
    serve_parser = subparsers.add_parser(
        "serve",
        help="Launch the web visualization server",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    add_serve_arguments(serve_parser)
    
    return parser


def add_ingest_arguments(parser: argparse.ArgumentParser) -> None:
    """Add arguments for the ingest subcommand."""
    parser.add_argument(
        "--input-dir",
        type=Path,
        help="Directory containing documents to process (PDF, HTML, DOCX, XML, LaTeX)"
    )
    
    parser.add_argument(
        "--file-types",
        nargs="+",
        choices=["pdf", "html", "docx", "xml", "latex"],
        default=["pdf", "html", "docx", "xml", "latex"],
        help="Document types to process"
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


def add_graph_arguments(parser: argparse.ArgumentParser) -> None:
    """Add arguments for the graph subcommand."""
    # Create subparsers for graph operations
    graph_subparsers = parser.add_subparsers(
        dest="graph_command",
        help="Graph database operations",
        metavar="{ingest,query,search,stats,export,clear}"
    )
    
    # Graph ingest subcommand
    ingest_parser = graph_subparsers.add_parser(
        "ingest",
        help="Ingest documents with graph database integration"
    )
    ingest_parser.add_argument(
        "--input-dir",
        type=Path,
        help="Directory containing PDF files to process"
    )
    ingest_parser.add_argument(
        "--no-math",
        action="store_true",
        help="Disable mathematical formula extraction"
    )
    ingest_parser.add_argument(
        "--math-ocr",
        action="store_true",
        help="Enable math OCR fallback"
    )
    
    # Graph query subcommand
    query_parser = graph_subparsers.add_parser(
        "query",
        help="Execute Cypher queries against the graph database"
    )
    query_parser.add_argument(
        "query",
        help="Cypher query to execute"
    )
    query_parser.add_argument(
        "--format",
        choices=["json", "table", "csv"],
        default="json",
        help="Output format"
    )
    query_parser.add_argument(
        "--output",
        type=Path,
        help="Output file (stdout if not specified)"
    )
    
    # Graph search subcommand
    search_parser = graph_subparsers.add_parser(
        "search",
        help="Search for concepts in the graph database"
    )
    search_parser.add_argument(
        "term",
        help="Search term"
    )
    search_parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum number of results"
    )
    search_parser.add_argument(
        "--type",
        help="Filter by concept type"
    )
    search_parser.add_argument(
        "--related",
        action="store_true",
        help="Show related concepts"
    )
    
    # Graph stats subcommand
    stats_parser = graph_subparsers.add_parser(
        "stats",
        help="Display graph database statistics"
    )
    stats_parser.add_argument(
        "--detailed",
        action="store_true",
        help="Show detailed statistics"
    )
    
    # Graph export subcommand
    export_parser = graph_subparsers.add_parser(
        "export",
        help="Export graph data to file"
    )
    export_parser.add_argument(
        "output_file",
        type=Path,
        help="Output file path"
    )
    export_parser.add_argument(
        "--format",
        choices=["json", "graphml", "cypher"],
        default="json",
        help="Export format"
    )
    
    # Graph clear subcommand
    clear_parser = graph_subparsers.add_parser(
        "clear",
        help="Clear all data from the graph database"
    )
    clear_parser.add_argument(
        "--confirm",
        action="store_true",
        help="Confirm deletion without prompting"
    )
    
    # Graph analyze subcommand
    analyze_parser = graph_subparsers.add_parser(
        "analyze",
        help="Analyze concept relationships"
    )
    analyze_parser.add_argument(
        "concept",
        help="Concept to analyze"
    )
    analyze_parser.add_argument(
        "--depth",
        type=int,
        default=2,
        help="Analysis depth"
    )
    analyze_parser.add_argument(
        "--document",
        help="Analyze concepts from specific document"
    )


def add_watch_arguments(parser: argparse.ArgumentParser) -> None:
    """Add arguments for the watch subcommand."""
    parser.add_argument(
        "--watch-dirs",
        nargs="+",
        type=Path,
        required=True,
        help="Directories to watch for document changes"
    )
    
    parser.add_argument(
        "--file-types",
        nargs="+",
        choices=["pdf", "html", "docx", "xml", "latex"],
        default=["pdf", "html", "docx", "xml", "latex"],
        help="Document types to monitor"
    )
    
    parser.add_argument(
        "--recursive",
        action="store_true",
        default=True,
        help="Watch subdirectories recursively"
    )
    
    parser.add_argument(
        "--batch-mode",
        action="store_true",
        help="Use batch mode for processing file events"
    )
    
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Number of files to batch together"
    )
    
    parser.add_argument(
        "--batch-timeout",
        type=float,
        default=5.0,
        help="Timeout for batch processing (seconds)"
    )
    
    parser.add_argument(
        "--ignore-patterns",
        nargs="+",
        default=[".*", "*~", "*.tmp", "*.swp"],
        help="File patterns to ignore"
    )


def add_batch_arguments(parser: argparse.ArgumentParser) -> None:
    """Add arguments for the batch subcommand."""
    parser.add_argument(
        "--input-dir",
        type=Path,
        required=True,
        help="Directory containing documents to process"
    )
    
    parser.add_argument(
        "--file-types",
        nargs="+",
        choices=["pdf", "html", "docx", "xml", "latex"],
        default=["pdf", "html", "docx", "xml", "latex"],
        help="Document types to process"
    )
    
    parser.add_argument(
        "--recursive",
        action="store_true",
        default=True,
        help="Process subdirectories recursively"
    )
    
    parser.add_argument(
        "--max-workers",
        type=int,
        default=4,
        help="Maximum number of parallel workers"
    )
    
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Number of documents to process per batch"
    )
    
    parser.add_argument(
        "--progress",
        action="store_true",
        default=True,
        help="Show progress information"
    )
    
    parser.add_argument(
        "--deduplicate",
        action="store_true",
        help="Enable concept deduplication"
    )
    
    parser.add_argument(
        "--external-ontologies",
        action="store_true",
        help="Enable external ontology enrichment"
    )


def add_serve_arguments(parser: argparse.ArgumentParser) -> None:
    """Add arguments for the serve subcommand."""
    parser.add_argument(
        "--host",
        type=str,
        help="Host to bind web server to"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        help="Port to bind web server to"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode for web server"
    )
    
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development"
    )


def run_ingest(args: argparse.Namespace, settings: Settings) -> int:
    """Run the ingest command."""
    try:
        from src.optimization.batch_processor import BatchProcessor
        from src.knowledge.ontology import FinancialMathOntology
        
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
        
        # Create ontology and batch processor
        ontology = FinancialMathOntology()
        
        # Configure supported file types
        config = settings.to_dict()
        config['supported_file_types'] = args.file_types
        
        batch_processor = BatchProcessor(ontology, config)
        
        # Process directory
        def progress_callback(current, total):
            if not args.no_progress:
                percent = (current / total) * 100 if total > 0 else 0
                print(f"Progress: {current}/{total} ({percent:.1f}%)")
        
        results = batch_processor.process_directory(
            args.input_dir,
            recursive=True,
            progress_callback=progress_callback if not args.no_progress else None
        )
        
        # Display results
        summary = results['summary']
        print(f"\nProcessing complete:")
        print(f"  Total files: {summary['total_files']}")
        print(f"  Successful: {summary['successful']}")
        print(f"  Failed: {summary['failed']}")
        print(f"  Total concepts: {summary['total_concepts_extracted']}")
        print(f"  Processing time: {summary['total_processing_time']:.2f}s")
        print(f"  Throughput: {summary['throughput_docs_per_second']:.2f} docs/sec")
        
        batch_processor.shutdown()
        return 0
        
    except Exception as e:
        logging.error(f"Ingestion failed: {e}")
        return 1


def run_chunk(args: argparse.Namespace, settings: Settings) -> int:
    """Run the chunk command."""
    try:
        from src.ingestion.chunk_embed import DocumentChunkEmbedder
        
        # Update settings with command line arguments
        if args.input_dir:
            settings.text_dir = args.input_dir
        if args.chunk_size:
            settings.chunk_size = args.chunk_size
        if args.chunk_overlap:
            settings.chunk_overlap = args.chunk_overlap
        
        # Create and run chunker
        chunker = DocumentChunkEmbedder(settings.model_dump())
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


def run_graph(args: argparse.Namespace, settings: Settings) -> int:
    """Run the graph command."""
    try:
        import json
        import sys
        from src.knowledge.graph_integration import get_graph_integrated_ingestor, get_graph_query_interface
        
        if not args.graph_command:
            logging.error("Graph subcommand is required")
            return 1
        
        if args.graph_command == "ingest":
            return run_graph_ingest(args, settings)
        elif args.graph_command == "query":
            return run_graph_query(args, settings)
        elif args.graph_command == "search":
            return run_graph_search(args, settings)
        elif args.graph_command == "stats":
            return run_graph_stats(args, settings)
        elif args.graph_command == "export":
            return run_graph_export(args, settings)
        elif args.graph_command == "clear":
            return run_graph_clear(args, settings)
        elif args.graph_command == "analyze":
            return run_graph_analyze(args, settings)
        else:
            logging.error(f"Unknown graph command: {args.graph_command}")
            return 1
            
    except Exception as e:
        logging.error(f"Graph command failed: {e}")
        return 1


def run_graph_ingest(args: argparse.Namespace, settings: Settings) -> int:
    """Run graph ingest command."""
    try:
        from src.knowledge.graph_integration import get_graph_integrated_ingestor
        
        # Update settings with command line arguments
        if args.input_dir:
            settings.input_dir = args.input_dir
        if args.no_math:
            settings.extract_math = False
        if args.math_ocr:
            settings.math_ocr_fallback = True
        
        # Create and run graph-integrated ingestor
        ingestor = get_graph_integrated_ingestor(settings)
        ingestor.process_all()
        
        # Display statistics
        stats = ingestor.get_graph_statistics()
        print("\nGraph Database Statistics:")
        print(f"  Total concepts: {stats.get('total_concepts', 0)}")
        print(f"  Total relationships: {stats.get('total_relationships', 0)}")
        print(f"  Processed documents: {stats.get('processed_documents', 0)}")
        
        ingestor.close()
        return 0
        
    except Exception as e:
        logging.error(f"Graph ingest failed: {e}")
        return 1


def run_graph_query(args: argparse.Namespace, settings: Settings) -> int:
    """Run graph query command."""
    try:
        from src.knowledge.graph_integration import get_graph_query_interface
        import json
        import sys
        
        query_interface = get_graph_query_interface(settings)
        
        # Execute query
        results = query_interface.query_graph(args.query)
        
        # Format output
        if args.format == "json":
            output = json.dumps(results, indent=2, ensure_ascii=False)
        elif args.format == "table":
            if results:
                # Simple table format
                headers = results[0].keys()
                output = "\t".join(headers) + "\n"
                for row in results:
                    output += "\t".join(str(row.get(h, "")) for h in headers) + "\n"
            else:
                output = "No results found.\n"
        elif args.format == "csv":
            if results:
                import csv
                import io
                output_buffer = io.StringIO()
                writer = csv.DictWriter(output_buffer, fieldnames=results[0].keys())
                writer.writeheader()
                writer.writerows(results)
                output = output_buffer.getvalue()
            else:
                output = ""
        
        # Write output
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output)
            print(f"Results written to {args.output}")
        else:
            print(output)
        
        query_interface.close()
        return 0
        
    except Exception as e:
        logging.error(f"Graph query failed: {e}")
        return 1


def run_graph_search(args: argparse.Namespace, settings: Settings) -> int:
    """Run graph search command."""
    try:
        from src.knowledge.graph_integration import get_graph_query_interface
        import json
        
        query_interface = get_graph_query_interface(settings)
        
        # Search for concepts
        results = query_interface.search_concepts(args.term, args.limit)
        
        if not results:
            print(f"No concepts found for '{args.term}'")
            return 0
        
        print(f"Found {len(results)} concepts for '{args.term}':")
        print()
        
        for i, concept in enumerate(results, 1):
            print(f"{i}. {concept.get('name', 'Unknown')} ({concept.get('type', 'Unknown')})")
            if concept.get('description'):
                print(f"   Description: {concept['description'][:100]}...")
            print(f"   Confidence: {concept.get('confidence', 0):.2f}")
            
            # Show related concepts if requested
            if args.related:
                related = query_interface.get_concept_relationships(concept['id'])
                if related:
                    print(f"   Related concepts: {len(related)}")
                    for rel in related[:3]:  # Show first 3
                        rel_concept = rel.get('concept', {})
                        rel_type = rel.get('relationship', {}).get('type', 'unknown')
                        print(f"     - {rel_concept.get('name', 'Unknown')} ({rel_type})")
            print()
        
        query_interface.close()
        return 0
        
    except Exception as e:
        logging.error(f"Graph search failed: {e}")
        return 1


def run_graph_stats(args: argparse.Namespace, settings: Settings) -> int:
    """Run graph stats command."""
    try:
        from src.knowledge.graph_integration import get_graph_query_interface
        import json
        
        query_interface = get_graph_query_interface(settings)
        
        # Get statistics
        stats = query_interface.get_graph_statistics()
        
        print("Graph Database Statistics:")
        print("=" * 30)
        print(f"Total concepts: {stats.get('total_concepts', 0)}")
        print(f"Total relationships: {stats.get('total_relationships', 0)}")
        print(f"Documents processed: {stats.get('documents_processed', 0)}")
        print(f"Average degree: {stats.get('avg_degree', 0):.2f}")
        print(f"Network density: {stats.get('density', 0):.3f}")
        print(f"Connected components: {stats.get('strongly_connected_components', 0)}")
        
        if args.detailed:
            print("\nConcept Types:")
            for concept_type in stats.get('concepts_by_type', []):
                print(f"  {concept_type['type']}: {concept_type['count']}")
            
            print("\nRelationship Types:")
            for rel_type in stats.get('relationships_by_type', []):
                print(f"  {rel_type['type']}: {rel_type['count']}")
            
            print("\nMost Central Concepts:")
            for concept, centrality in stats.get('most_central_concepts', [])[:10]:
                print(f"  {concept}: {centrality:.3f}")
        
        query_interface.close()
        return 0
        
    except Exception as e:
        logging.error(f"Graph stats failed: {e}")
        return 1


def run_graph_export(args: argparse.Namespace, settings: Settings) -> int:
    """Run graph export command."""
    try:
        from src.knowledge.graph_integration import get_graph_integrated_ingestor
        
        ingestor = get_graph_integrated_ingestor(settings)
        
        if args.format == "json":
            success = ingestor.export_graph_data(args.output_file)
        else:
            # Other formats could be implemented here
            logging.error(f"Export format '{args.format}' not yet supported")
            return 1
        
        if success:
            print(f"Graph data exported to {args.output_file}")
        else:
            print("Export failed")
            return 1
        
        ingestor.close()
        return 0
        
    except Exception as e:
        logging.error(f"Graph export failed: {e}")
        return 1


def run_graph_clear(args: argparse.Namespace, settings: Settings) -> int:
    """Run graph clear command."""
    try:
        from src.knowledge.graph_integration import get_graph_integrated_ingestor
        
        if not args.confirm:
            response = input("Are you sure you want to clear all graph data? (y/N): ")
            if response.lower() != 'y':
                print("Operation cancelled")
                return 0
        
        ingestor = get_graph_integrated_ingestor(settings)
        success = ingestor.clear_graph_database()
        
        if success:
            print("Graph database cleared successfully")
        else:
            print("Failed to clear graph database")
            return 1
        
        ingestor.close()
        return 0
        
    except Exception as e:
        logging.error(f"Graph clear failed: {e}")
        return 1


def run_graph_analyze(args: argparse.Namespace, settings: Settings) -> int:
    """Run graph analyze command."""
    try:
        from src.knowledge.graph_integration import get_graph_query_interface
        import json
        
        query_interface = get_graph_query_interface(settings)
        
        if args.document:
            # Analyze document concepts
            analysis = query_interface.analyze_document_concepts(args.document)
        else:
            # Analyze specific concept
            analysis = query_interface.analyze_concept_network(args.concept, args.depth)
        
        print(json.dumps(analysis, indent=2, ensure_ascii=False))
        
        query_interface.close()
        return 0
        
    except Exception as e:
        logging.error(f"Graph analyze failed: {e}")
        return 1


def run_watch(args: argparse.Namespace, settings: Settings) -> int:
    """Run the watch command."""
    try:
        import asyncio
        from src.monitoring.file_watcher import FileWatcher, BatchFileWatcher
        from src.monitoring.incremental_processor import IncrementalProcessor
        from src.ingestion.extractors.document_detector import DocumentDetector
        from src.knowledge.ontology import FinancialMathOntology
        
        # Create ontology and incremental processor
        ontology = FinancialMathOntology()
        
        # Configure settings
        config = settings.to_dict()
        config.update({
            'recursive': args.recursive,
            'ignore_patterns': args.ignore_patterns,
            'batch_size': args.batch_size,
            'batch_timeout': args.batch_timeout,
        })
        
        incremental_processor = IncrementalProcessor(ontology, config)
        
        # Create file watcher
        if args.batch_mode:
            watcher = BatchFileWatcher(config)
            watcher.add_batch_callback(incremental_processor.process_batch_events)
        else:
            watcher = FileWatcher(config)
            watcher.add_callback(incremental_processor.process_file_event)
        
        # Set up supported extensions
        detector = DocumentDetector()
        supported_extensions = []
        for file_type in args.file_types:
            if file_type == "pdf":
                supported_extensions.append(".pdf")
            elif file_type == "html":
                supported_extensions.extend([".html", ".htm"])
            elif file_type == "docx":
                supported_extensions.append(".docx")
            elif file_type == "xml":
                supported_extensions.append(".xml")
            elif file_type == "latex":
                supported_extensions.extend([".tex", ".latex"])
        
        watcher.set_supported_extensions(supported_extensions)
        
        # Add watch directories
        for watch_dir in args.watch_dirs:
            if not watch_dir.exists():
                logging.error(f"Watch directory does not exist: {watch_dir}")
                return 1
            watcher.add_watch_path(watch_dir, args.recursive)
        
        print(f"Starting file watcher...")
        print(f"Watching {len(args.watch_dirs)} directories:")
        for watch_dir in args.watch_dirs:
            print(f"  - {watch_dir} ({'recursive' if args.recursive else 'non-recursive'})")
        print(f"Monitoring file types: {', '.join(args.file_types)}")
        print(f"Batch mode: {'enabled' if args.batch_mode else 'disabled'}")
        print("Press Ctrl+C to stop watching...")
        
        async def run_watchers():
            await incremental_processor.start()
            watcher.start()
            
            try:
                # Keep running until interrupted
                while True:
                    await asyncio.sleep(1)
                    
                    # Display periodic statistics
                    stats = incremental_processor.get_processing_stats()
                    if stats['documents_processed'] > 0:
                        print(f"Processed: {stats['documents_processed']} documents, "
                              f"Queue: {stats['queue_size']}, "
                              f"Errors: {stats['processing_errors']}")
                    
            except KeyboardInterrupt:
                print("\nShutting down file watcher...")
            finally:
                watcher.stop()
                await incremental_processor.stop()
        
        # Run the async event loop
        asyncio.run(run_watchers())
        
        return 0
        
    except Exception as e:
        logging.error(f"Watch command failed: {e}")
        return 1


def run_batch(args: argparse.Namespace, settings: Settings) -> int:
    """Run the batch command."""
    try:
        from src.optimization.batch_processor import BatchProcessor
        from src.optimization.concept_deduplicator import DocumentTypeAwareDedupicator
        from src.knowledge.ontology import FinancialMathOntology
        
        # Create ontology
        ontology = FinancialMathOntology()
        
        # Configure settings
        config = settings.to_dict()
        config.update({
            'max_workers': args.max_workers,
            'batch_size': args.batch_size,
            'use_external_ontologies': args.external_ontologies,
            'supported_file_types': args.file_types,
        })
        
        batch_processor = BatchProcessor(ontology, config)
        
        # Progress callback
        def progress_callback(current, total):
            if args.progress:
                percent = (current / total) * 100 if total > 0 else 0
                print(f"Progress: {current}/{total} ({percent:.1f}%)")
        
        print(f"Starting batch processing of {args.input_dir}")
        print(f"File types: {', '.join(args.file_types)}")
        print(f"Workers: {args.max_workers}, Batch size: {args.batch_size}")
        print(f"Recursive: {args.recursive}")
        print(f"Deduplication: {'enabled' if args.deduplicate else 'disabled'}")
        print(f"External ontologies: {'enabled' if args.external_ontologies else 'disabled'}")
        
        # Process directory
        results = batch_processor.process_directory(
            args.input_dir,
            recursive=args.recursive,
            progress_callback=progress_callback if args.progress else None
        )
        
        # Apply deduplication if requested
        if args.deduplicate:
            print("\nApplying concept deduplication...")
            deduplicator = DocumentTypeAwareDedupicator(config)
            
            # Get all concepts from ontology
            all_concepts = ontology.get_all_concepts()
            deduplicated_concepts = deduplicator.deduplicate_concepts(all_concepts)
            
            # Update ontology with deduplicated concepts
            ontology.replace_concepts(deduplicated_concepts)
            
            dedup_stats = deduplicator.get_statistics()
            print(f"Deduplication results:")
            print(f"  Original concepts: {dedup_stats['concepts_processed']}")
            print(f"  Duplicates found: {dedup_stats['duplicates_found']}")
            print(f"  Concepts merged: {dedup_stats['concepts_merged']}")
            print(f"  Final concepts: {len(deduplicated_concepts)}")
        
        # Display final results
        summary = results['summary']
        print(f"\nBatch processing complete:")
        print(f"  Total files: {summary['total_files']}")
        print(f"  Successful: {summary['successful']}")
        print(f"  Failed: {summary['failed']}")
        print(f"  Total concepts: {summary['total_concepts_extracted']}")
        print(f"  Processing time: {summary['total_processing_time']:.2f}s")
        print(f"  Throughput: {summary['throughput_docs_per_second']:.2f} docs/sec")
        print(f"  Memory usage: {summary['memory_usage_mb']:.1f} MB")
        
        # Show failed files if any
        if results['failed_files']:
            print(f"\nFailed files ({len(results['failed_files'])}):")
            for failed_file in results['failed_files'][:10]:  # Show first 10
                print(f"  - {failed_file['file_path']}: {failed_file['error']}")
            if len(results['failed_files']) > 10:
                print(f"  ... and {len(results['failed_files']) - 10} more")
        
        batch_processor.shutdown()
        return 0
        
    except Exception as e:
        logging.error(f"Batch processing failed: {e}")
        return 1


def run_serve(args: argparse.Namespace, settings: Settings) -> int:
    """Run the serve command."""
    try:
        # Update settings with command line arguments
        if args.host:
            settings.web_host = args.host
        if args.port:
            settings.web_port = args.port
        if args.debug:
            settings.web_debug = args.debug
        
        # Import FastAPI app
        from src.frontend.app import create_app
        
        # Create the FastAPI application
        app = create_app(settings)
        
        # Run with uvicorn
        import uvicorn
        
        print(f"Starting web server on {settings.web_host}:{settings.web_port}")
        print(f"Debug mode: {settings.web_debug}")
        print(f"Open your browser to: http://{settings.web_host}:{settings.web_port}")
        
        uvicorn.run(
            app,
            host=settings.web_host,
            port=settings.web_port,
            debug=settings.web_debug,
            reload=args.reload if hasattr(args, 'reload') else False,
            log_level="debug" if settings.web_debug else "info"
        )
        
        return 0
        
    except Exception as e:
        logging.error(f"Web server failed: {e}")
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
        # Validate configuration first
        try:
            validated_config = validate_and_transform_config(
                config_path=str(args.config),
                schema_path="config_schema.json",
                exit_on_error=True
            )
        except ConfigValidationError as e:
            print(f"Configuration validation failed: {e}", file=sys.stderr)
            return 1
        
        # Load settings with validated config
        settings = Settings.from_env_and_yaml(args.config)
        
        # Override log level based on verbosity
        if args.verbose:
            settings.log_level = "DEBUG"
        elif args.quiet:
            settings.log_level = "ERROR"
        
        # Setup logging
        setup_logging(settings)
        
        # Log successful configuration validation
        logging.info("Configuration validation successful")
        
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
        elif args.command == "graph":
            return run_graph(args, settings)
        elif args.command == "watch":
            return run_watch(args, settings)
        elif args.command == "batch":
            return run_batch(args, settings)
        elif args.command == "serve":
            return run_serve(args, settings)
        else:
            logging.error(f"Unknown command: {args.command}")
            return 1
            
    except Exception as e:
        logging.error(f"CLI execution failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())