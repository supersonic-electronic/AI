"""
Tests for the CLI interface.

These tests verify argument parsing, command dispatch, and error handling.
"""

import pytest
import subprocess
from unittest.mock import Mock, patch, call
from pathlib import Path

from src.cli import create_parser, run_ingest, run_chunk, run_embed, run_test
from src.settings import Settings


class TestArgumentParsing:
    """Test CLI argument parsing."""
    
    def test_create_parser(self):
        """Test parser creation."""
        parser = create_parser()
        assert parser is not None
        
        # Test help includes subcommands
        help_text = parser.format_help()
        assert "ingest" in help_text
        assert "chunk" in help_text
        assert "embed" in help_text
        assert "test" in help_text
    
    def test_ingest_command_parsing(self):
        """Test ingest command argument parsing."""
        parser = create_parser()
        
        args = parser.parse_args([
            "ingest",
            "--input-dir", "/path/to/pdfs",
            "--text-dir", "/path/to/text",
            "--no-math",
            "--parallel-workers", "8"
        ])
        
        assert args.command == "ingest"
        assert args.input_dir == Path("/path/to/pdfs")
        assert args.text_dir == Path("/path/to/text")
        assert args.no_math is True
        assert args.parallel_workers == 8
    
    def test_chunk_command_parsing(self):
        """Test chunk command argument parsing."""
        parser = create_parser()
        
        args = parser.parse_args([
            "chunk",
            "--input-dir", "/path/to/text",
            "--chunk-size", "1000",
            "--chunk-overlap", "100",
            "--preserve-math"
        ])
        
        assert args.command == "chunk"
        assert args.input_dir == Path("/path/to/text")
        assert args.chunk_size == 1000
        assert args.chunk_overlap == 100
        assert args.preserve_math is True
    
    def test_embed_command_parsing(self):
        """Test embed command argument parsing."""
        parser = create_parser()
        
        args = parser.parse_args([
            "embed",
            "--vectorstore", "pinecone",
            "--namespace", "test-docs",
            "--batch-size", "50"
        ])
        
        assert args.command == "embed"
        assert args.vectorstore == "pinecone"
        assert args.namespace == "test-docs"
        assert args.batch_size == 50
    
    def test_test_command_parsing(self):
        """Test test command argument parsing."""
        parser = create_parser()
        
        args = parser.parse_args([
            "test",
            "--coverage",
            "--markers", "unit",
            "--maxfail", "3"
        ])
        
        assert args.command == "test"
        assert args.coverage is True
        assert args.markers == "unit"
        assert args.maxfail == 3
    
    def test_global_arguments(self):
        """Test global arguments parsing."""
        parser = create_parser()
        
        args = parser.parse_args([
            "--config", "test-config.yaml",
            "--verbose",
            "ingest"
        ])
        
        assert args.config == Path("test-config.yaml")
        assert args.verbose is True
        assert args.command == "ingest"


class TestCommandExecution:
    """Test command execution functions."""
    
    @pytest.fixture
    def test_settings(self):
        """Create test settings."""
        return Settings(
            input_dir=Path("./test/input"),
            text_dir=Path("./test/text"),
            meta_dir=Path("./test/meta"),
            math_dir=Path("./test/math")
        )
    
    @patch('src.cli.PDFIngestor')
    def test_run_ingest_success(self, mock_ingestor_class, test_settings):
        """Test successful ingest command execution."""
        # Setup mock
        mock_ingestor = Mock()
        mock_ingestor_class.return_value = mock_ingestor
        
        # Create args
        args = Mock()
        args.input_dir = Path("./custom/input")
        args.text_dir = None
        args.meta_dir = None
        args.math_dir = None
        args.no_math = False
        args.math_ocr = True
        args.parallel_workers = 4
        args.skip_existing = True
        args.no_progress = False
        
        # Run command
        result = run_ingest(args, test_settings)
        
        # Verify
        assert result == 0
        assert test_settings.input_dir == Path("./custom/input")
        assert test_settings.math_ocr_fallback is True
        assert test_settings.parallel_workers == 4
        assert test_settings.skip_existing is True
        
        mock_ingestor_class.assert_called_once_with(test_settings)
        mock_ingestor.process_all.assert_called_once()
    
    @patch('src.cli.DocumentChunker')
    def test_run_chunk_success(self, mock_chunker_class, test_settings):
        """Test successful chunk command execution."""
        # Setup mock
        mock_chunker = Mock()
        mock_chunker_class.return_value = mock_chunker
        
        # Create args
        args = Mock()
        args.input_dir = Path("./custom/text")
        args.output_dir = Path("./custom/chunks")
        args.chunk_size = 800
        args.chunk_overlap = 80
        
        # Run command
        result = run_chunk(args, test_settings)
        
        # Verify
        assert result == 0
        assert test_settings.text_dir == Path("./custom/text")
        assert test_settings.chunk_size == 800
        assert test_settings.chunk_overlap == 80
        
        mock_chunker_class.assert_called_once_with(test_settings)
        mock_chunker.process_directory.assert_called_once_with(
            Path("./custom/text"),
            Path("./custom/chunks")
        )
    
    @patch('src.cli.EmbeddingPipeline')
    def test_run_embed_success(self, mock_pipeline_class, test_settings):
        """Test successful embed command execution."""
        # Setup mock
        mock_pipeline = Mock()
        mock_pipeline_class.return_value = mock_pipeline
        
        # Create args
        args = Mock()
        args.input_dir = Path("./custom/chunks")
        args.local = True
        args.vectorstore = "chroma"
        args.namespace = None
        args.batch_size = 30
        args.embedding_model = "text-embedding-3-large"
        
        # Run command
        result = run_embed(args, test_settings)
        
        # Verify
        assert result == 0
        assert test_settings.embedding_batch_size == 30
        assert test_settings.embedding_model == "text-embedding-3-large"
        
        mock_pipeline_class.assert_called_once_with(test_settings)
        mock_pipeline.embed_to_chroma.assert_called_once_with(Path("./custom/chunks"))
    
    @patch('subprocess.run')
    def test_run_test_success(self, mock_subprocess, test_settings):
        """Test successful test command execution."""
        # Setup mock
        mock_result = Mock()
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result
        
        # Create args
        args = Mock()
        args.test_path = Path("tests/unit")
        args.coverage = True
        args.markers = "unit"
        args.maxfail = 3
        
        # Run command
        result = run_test(args, test_settings)
        
        # Verify
        assert result == 0
        mock_subprocess.assert_called_once()
        
        # Check pytest command construction
        call_args = mock_subprocess.call_args[0][0]
        assert "pytest" in call_args
        assert "tests/unit" in call_args
        assert "--cov=src" in call_args
        assert "-m" in call_args
        assert "unit" in call_args
        assert "--maxfail=3" in call_args


class TestErrorHandling:
    """Test error handling in CLI commands."""
    
    @pytest.fixture
    def test_settings(self):
        """Create test settings."""
        return Settings()
    
    @patch('src.cli.PDFIngestor')
    def test_run_ingest_failure(self, mock_ingestor_class, test_settings):
        """Test ingest command failure handling."""
        # Setup mock to raise exception
        mock_ingestor_class.side_effect = Exception("Test error")
        
        # Create args
        args = Mock()
        args.input_dir = None
        args.text_dir = None
        args.meta_dir = None
        args.math_dir = None
        args.no_math = False
        args.math_ocr = False
        args.parallel_workers = None
        args.skip_existing = False
        args.no_progress = False
        
        # Run command
        result = run_ingest(args, test_settings)
        
        # Should return error code
        assert result == 1
    
    @patch('subprocess.run')
    def test_run_test_failure(self, mock_subprocess, test_settings):
        """Test test command failure handling."""
        # Setup mock to return error code
        mock_result = Mock()
        mock_result.returncode = 1
        mock_subprocess.return_value = mock_result
        
        # Create args
        args = Mock()
        args.test_path = Path("tests/")
        args.coverage = False
        args.markers = None
        args.maxfail = 5
        
        # Run command
        result = run_test(args, test_settings)
        
        # Should return error code
        assert result == 1


@pytest.mark.integration
class TestCLIIntegration:
    """Integration tests for CLI functionality."""
    
    def test_cli_help(self):
        """Test CLI help output."""
        result = subprocess.run(
            ["python", "-m", "src.cli", "--help"],
            capture_output=True,
            text=True,
            cwd=Path.cwd()
        )
        
        assert result.returncode == 0
        assert "ingest" in result.stdout
        assert "chunk" in result.stdout
        assert "embed" in result.stdout
        assert "test" in result.stdout
    
    def test_ingest_help(self):
        """Test ingest subcommand help."""
        result = subprocess.run(
            ["python", "-m", "src.cli", "ingest", "--help"],
            capture_output=True,
            text=True,
            cwd=Path.cwd()
        )
        
        assert result.returncode == 0
        assert "--input-dir" in result.stdout
        assert "--no-math" in result.stdout
        assert "--parallel-workers" in result.stdout
    
    def test_no_command_shows_help(self):
        """Test that running CLI without command shows help."""
        result = subprocess.run(
            ["python", "-m", "src.cli"],
            capture_output=True,
            text=True,
            cwd=Path.cwd()
        )
        
        # Should return error code and show help
        assert result.returncode == 1