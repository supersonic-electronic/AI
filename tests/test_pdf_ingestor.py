"""
Unit tests for PDF ingestion functionality.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from src.ingestion.pdf2txt import PDFIngestor, load_config, get_interactive_input


class TestConfigLoading:
    """Test configuration loading functionality."""
    
    def test_load_config_success(self, tmp_path):
        """Test successful config loading."""
        config_data = {
            'input_dir': './data/papers',
            'text_dir': './data/text',
            'meta_dir': './data/metadata',
            'log_level': 'INFO'
        }
        
        config_file = tmp_path / "config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        with patch('src.ingestion.pdf2txt.Path') as mock_path:
            mock_path.return_value.exists.return_value = True
            with patch('builtins.open', mock_open_yaml(config_data)):
                config = load_config()
                assert config['input_dir'] == './data/papers'
                assert config['log_level'] == 'INFO'
    
    def test_load_config_file_not_found(self):
        """Test config loading when file doesn't exist."""
        with patch('src.ingestion.pdf2txt.Path') as mock_path:
            mock_path.return_value.exists.return_value = False
            
            with pytest.raises(FileNotFoundError):
                load_config()


class TestPDFIngestor:
    """Test PDFIngestor class functionality."""
    
    @pytest.fixture
    def sample_config(self):
        """Sample configuration for testing."""
        return {
            'input_dir': './test_input',
            'text_dir': './test_text',
            'meta_dir': './test_meta',
            'log_level': 'INFO',
            'log_to_file': False,
            'preserve_reading_order': True,
            'warn_empty_pages': True,
            'encoding': 'utf-8',
            'json_indent': 2,
            'parallel_workers': 1,
            'skip_existing': False,
            'show_progress': False,
            'doi_regex': r'10\.[0-9]{4,}[-._;()/:a-zA-Z0-9]*',
            'doi_prefixes': ['doi:', 'DOI:']
        }
    
    def test_ingestor_initialization(self, sample_config, tmp_path):
        """Test PDFIngestor initialization."""
        # Update config with temp paths
        sample_config.update({
            'input_dir': str(tmp_path / 'input'),
            'text_dir': str(tmp_path / 'text'),
            'meta_dir': str(tmp_path / 'meta')
        })
        
        ingestor = PDFIngestor(sample_config)
        
        assert ingestor.input_dir == Path(sample_config['input_dir'])
        assert ingestor.text_dir == Path(sample_config['text_dir'])
        assert ingestor.meta_dir == Path(sample_config['meta_dir'])
        
        # Check directories were created
        assert ingestor.input_dir.exists()
        assert ingestor.text_dir.exists()
        assert ingestor.meta_dir.exists()
    
    def test_extract_doi_with_prefix(self, sample_config):
        """Test DOI extraction with prefix."""
        ingestor = PDFIngestor(sample_config)
        
        metadata = {
            'title': 'Research Paper doi:10.1234/example.paper',
            'author': 'Test Author'
        }
        
        doi = ingestor._extract_doi(metadata)
        assert doi == '10.1234/example.paper'
    
    def test_extract_doi_without_prefix(self, sample_config):
        """Test DOI extraction without prefix."""
        ingestor = PDFIngestor(sample_config)
        
        metadata = {
            'title': 'Research Paper 10.5678/another.example',
            'author': 'Test Author'
        }
        
        doi = ingestor._extract_doi(metadata)
        assert doi == '10.5678/another.example'
    
    def test_extract_doi_not_found(self, sample_config):
        """Test DOI extraction when no DOI present."""
        ingestor = PDFIngestor(sample_config)
        
        metadata = {
            'title': 'Research Paper Without DOI',
            'author': 'Test Author'
        }
        
        doi = ingestor._extract_doi(metadata)
        assert doi == ''
    
    def test_should_skip_file_false(self, sample_config, tmp_path):
        """Test file skipping when skip_existing is False."""
        sample_config['skip_existing'] = False
        sample_config.update({
            'text_dir': str(tmp_path / 'text'),
            'meta_dir': str(tmp_path / 'meta')
        })
        
        ingestor = PDFIngestor(sample_config)
        
        # Create existing files
        (tmp_path / 'text' / 'test.txt').touch()
        (tmp_path / 'meta' / 'test.json').touch()
        
        pdf_path = Path('test.pdf')
        assert ingestor._should_skip_file(pdf_path) is False
    
    def test_should_skip_file_true(self, sample_config, tmp_path):
        """Test file skipping when skip_existing is True and files exist."""
        sample_config['skip_existing'] = True
        sample_config.update({
            'text_dir': str(tmp_path / 'text'),
            'meta_dir': str(tmp_path / 'meta')
        })
        
        ingestor = PDFIngestor(sample_config)
        
        # Create existing files
        (tmp_path / 'text' / 'test.txt').touch()
        (tmp_path / 'meta' / 'test.json').touch()
        
        pdf_path = Path('test.pdf')
        assert ingestor._should_skip_file(pdf_path) is True


class TestInteractiveInput:
    """Test interactive input functionality."""
    
    def test_get_interactive_input_with_defaults(self):
        """Test interactive input using defaults."""
        config = {
            'input_dir': './default_input',
            'text_dir': './default_text',
            'meta_dir': './default_meta'
        }
        
        # Mock user pressing Enter for all prompts (using defaults)
        with patch('builtins.input', side_effect=['', '', '']):
            result = get_interactive_input(config)
            
            assert result['input_dir'] == './default_input'
            assert result['text_dir'] == './default_text'
            assert result['meta_dir'] == './default_meta'
    
    def test_get_interactive_input_with_custom_values(self):
        """Test interactive input with custom values."""
        config = {
            'input_dir': './default_input',
            'text_dir': './default_text',
            'meta_dir': './default_meta'
        }
        
        # Mock user providing custom values
        with patch('builtins.input', side_effect=['./custom_input', './custom_text', './custom_meta']):
            result = get_interactive_input(config)
            
            assert result['input_dir'] == './custom_input'
            assert result['text_dir'] == './custom_text'
            assert result['meta_dir'] == './custom_meta'


def mock_open_yaml(data):
    """Mock open function for YAML data."""
    import io
    return lambda *args, **kwargs: io.StringIO(yaml.dump(data))


# Fixtures for test data
@pytest.fixture
def sample_pdf_metadata():
    """Sample PDF metadata for testing."""
    return {
        'title': 'Sample Research Paper',
        'author': 'Test Author',
        'subject': 'Academic Research',
        'creator': 'LaTeX',
        'producer': 'pdfTeX',
        'creationDate': 'D:20231201120000',
        'modDate': 'D:20231201120000',
        'keywords': 'research, testing'
    }


@pytest.fixture
def sample_text_content():
    """Sample text content for testing."""
    return "This is sample text content from a PDF.\n\nSecond paragraph with more content."