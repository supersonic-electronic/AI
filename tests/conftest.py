"""
Pytest configuration and fixtures for the portfolio optimizer tests.

This module provides shared fixtures and test configuration for all test modules.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch
import yaml

from src.settings import Settings


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def test_settings(temp_dir):
    """Create test settings with temporary directories."""
    return Settings(
        input_dir=temp_dir / "input",
        text_dir=temp_dir / "text",
        meta_dir=temp_dir / "meta",
        math_dir=temp_dir / "math",
        log_file=temp_dir / "logs" / "test.log",
        chroma_persist_directory=temp_dir / "chroma",
        log_level="DEBUG",
        parallel_workers=2,
        chunk_size=500,
        chunk_overlap=50,
        extract_math=True,
        math_ocr_fallback=False
    )


@pytest.fixture
def sample_config_data():
    """Sample configuration data for testing."""
    return {
        "log_level": "INFO",
        "parallel_workers": 4,
        "chunk_size": 500,
        "chunk_overlap": 50,
        "extract_math": True,
        "math_ocr_fallback": False,
        "input_dir": "./data/papers",
        "text_dir": "./data/text",
        "meta_dir": "./data/metadata",
        "math_dir": "./data/math",
        "openai_api_key": "test-openai-key",
        "pinecone_api_key": "test-pinecone-key"
    }


@pytest.fixture
def config_file(temp_dir, sample_config_data):
    """Create a temporary config file for testing."""
    config_path = temp_dir / "test_config.yaml"
    with open(config_path, 'w') as f:
        yaml.dump(sample_config_data, f)
    return config_path


@pytest.fixture
def sample_pdf_content():
    """Sample PDF text content for testing."""
    return """
    Portfolio Optimization Theory
    
    The expected return of a portfolio is given by:
    E(R_p) = w'μ
    
    Where:
    - w is the weight vector
    - μ is the mean return vector
    
    The portfolio variance is:
    σ²_p = w'Σw
    
    Where Σ is the covariance matrix.
    
    The Sharpe ratio is defined as:
    SR = (E(R_p) - R_f) / σ_p
    
    This is some regular text without mathematical content.
    """


@pytest.fixture
def sample_math_blocks():
    """Sample mathematical blocks for testing."""
    return [
        {
            "page": 1,
            "block": {
                "block_id": "math_p1_l1_1234",
                "page_num": 1,
                "bbox": [100, 200, 300, 220],
                "raw_text": "E(R_p) = w'μ",
                "latex": "$E(R_p) = w'\\mu$",
                "confidence": 0.85,
                "char_position": {"start": 45, "end": 58},
                "line_position": {"start": 3, "end": 3},
                "semantic_group": "portfolio_theory",
                "related_blocks": ["math_p1_l2_5678"],
                "context": {
                    "before": "The expected return of a portfolio is given by:",
                    "after": "Where:"
                }
            }
        },
        {
            "page": 1,
            "block": {
                "block_id": "math_p1_l2_5678",
                "page_num": 1,
                "bbox": [100, 250, 300, 270],
                "raw_text": "σ²_p = w'Σw",
                "latex": "$\\sigma^2_p = w'\\Sigma w$",
                "confidence": 0.90,
                "char_position": {"start": 120, "end": 131},
                "line_position": {"start": 8, "end": 8},
                "semantic_group": "portfolio_theory",
                "related_blocks": ["math_p1_l1_1234"],
                "context": {
                    "before": "The portfolio variance is:",
                    "after": "Where Σ is the covariance matrix."
                }
            }
        }
    ]


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing."""
    mock_client = Mock()
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = "\\frac{x}{y}"
    mock_client.chat.completions.create.return_value = mock_response
    return mock_client


@pytest.fixture
def mock_mathpix_client():
    """Mock Mathpix client for testing."""
    mock_client = Mock()
    mock_client.latex.return_value = {'latex_simplified': '\\int f(x) dx'}
    return mock_client


@pytest.fixture
def mock_pdf_document():
    """Mock PyMuPDF document for testing."""
    mock_doc = Mock()
    mock_doc.__len__ = Mock(return_value=3)  # 3 pages
    mock_doc.metadata = {
        'title': 'Test Document',
        'author': 'Test Author',
        'subject': 'Test Subject',
        'keywords': 'test, keywords',
        'creator': 'Test Creator',
        'producer': 'Test Producer',
        'creationDate': 'D:20230101000000',
        'modDate': 'D:20230101000000'
    }
    
    # Mock pages
    mock_pages = []
    for i in range(3):
        mock_page = Mock()
        mock_page.get_text.return_value = f"Page {i+1} content with some mathematical expressions like x = y + z"
        mock_page.get_text.return_value = sample_pdf_content if i == 0 else f"Page {i+1} content"
        mock_pages.append(mock_page)
    
    mock_doc.load_page.side_effect = lambda x: mock_pages[x]
    return mock_doc


@pytest.fixture
def mock_fitz(mock_pdf_document):
    """Mock PyMuPDF (fitz) module."""
    with patch('fitz.open') as mock_open:
        mock_open.return_value = mock_pdf_document
        yield mock_open


@pytest.fixture(scope="session")
def test_data_dir():
    """Path to test data directory."""
    return Path(__file__).parent / "data"


@pytest.fixture
def create_test_files(temp_dir):
    """Create test files for testing."""
    def _create_files(file_contents: dict):
        """Create test files with given contents."""
        created_files = []
        for filename, content in file_contents.items():
            file_path = temp_dir / filename
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            created_files.append(file_path)
        return created_files
    
    return _create_files


@pytest.fixture
def sample_text_chunks():
    """Sample text chunks for testing."""
    return [
        {
            "chunk_id": "chunk_1",
            "source_file": "test_document.pdf",
            "page": 1,
            "chunk_index": 0,
            "chunk_start": 0,
            "chunk_end": 250,
            "text": "Portfolio optimization is a fundamental concept in finance...",
            "math_block_count": 2,
            "math_block_ids": ["math_p1_l1_1234", "math_p1_l2_5678"],
            "has_mathematical_content": True,
            "metadata": {
                "title": "Portfolio Theory",
                "author": "Test Author"
            }
        },
        {
            "chunk_id": "chunk_2",
            "source_file": "test_document.pdf",
            "page": 1,
            "chunk_index": 1,
            "chunk_start": 200,
            "chunk_end": 450,
            "text": "The Sharpe ratio is a measure of risk-adjusted return...",
            "math_block_count": 1,
            "math_block_ids": ["math_p1_l3_9012"],
            "has_mathematical_content": True,
            "metadata": {
                "title": "Portfolio Theory",
                "author": "Test Author"
            }
        }
    ]


@pytest.fixture
def mock_logging():
    """Mock logging to avoid log output during tests."""
    with patch('logging.getLogger') as mock_get_logger:
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        yield mock_logger


# Additional fixtures for improved testing


@pytest.fixture
def mock_html_content():
    """Sample HTML content for testing HTML extractor."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Document</title>
        <meta name="author" content="Test Author">
        <meta name="description" content="Test Description">
    </head>
    <body>
        <h1>Main Title</h1>
        <p>This is a paragraph with some content.</p>
        <div class="math">E(R) = w'μ</div>
        <footer>Footer content</footer>
    </body>
    </html>
    """


@pytest.fixture
def mock_docx_content():
    """Mock DOCX document structure for testing."""
    mock_doc = Mock()
    
    # Mock paragraphs
    mock_paragraph1 = Mock()
    mock_paragraph1.text = "First paragraph content"
    mock_paragraph2 = Mock()
    mock_paragraph2.text = "Second paragraph with formula: E(R) = w'μ"
    mock_doc.paragraphs = [mock_paragraph1, mock_paragraph2]
    
    # Mock tables
    mock_table = Mock()
    mock_row = Mock()
    mock_cell = Mock()
    mock_cell.text = "Cell content"
    mock_row.cells = [mock_cell]
    mock_table.rows = [mock_row]
    mock_doc.tables = [mock_table]
    
    # Mock core properties
    mock_props = Mock()
    mock_props.title = "Test Document"
    mock_props.author = "Test Author"
    mock_props.subject = "Test Subject"
    mock_props.keywords = "test, keywords"
    mock_doc.core_properties = mock_props
    
    # Mock sections
    mock_section = Mock()
    mock_doc.sections = [mock_section]
    
    return mock_doc


@pytest.fixture
def mock_xml_content():
    """Sample XML content for testing XML extractor."""
    return """
    <?xml version="1.0" encoding="UTF-8"?>
    <document>
        <metadata>
            <title>Test XML Document</title>
            <author>Test Author</author>
        </metadata>
        <content>
            <section id="1">
                <heading>Introduction</heading>
                <paragraph>This is test content.</paragraph>
                <formula>σ²_p = w'Σw</formula>
            </section>
        </content>
    </document>
    """


@pytest.fixture
def mock_latex_content():
    """Sample LaTeX content for testing LaTeX extractor."""
    return r"""
    \documentclass{article}
    \title{Portfolio Optimization}
    \author{Test Author}
    \date{\today}
    
    \begin{document}
    \maketitle
    
    \section{Introduction}
    This document discusses portfolio optimization theory.
    
    The expected return is given by:
    \begin{equation}
    E(R_p) = w'\mu
    \end{equation}
    
    Where $w$ is the weight vector and $\mu$ is the mean return vector.
    
    \subsection{Risk}
    The portfolio variance is:
    \begin{align}
    \sigma^2_p &= w'\Sigma w
    \end{align}
    
    \end{document}
    """


@pytest.fixture
def sample_extractors():
    """Create sample extractor instances for testing."""
    from src.ingestion.extractors.html import HTMLExtractor
    from src.ingestion.extractors.docx import DOCXExtractor
    from src.ingestion.extractors.xml import XMLExtractor
    from src.ingestion.extractors.latex import LaTeXExtractor
    
    return {
        'html': HTMLExtractor(),
        'docx': DOCXExtractor(),
        'xml': XMLExtractor(),
        'latex': LaTeXExtractor()
    }


@pytest.fixture
def sample_file_paths(temp_dir):
    """Create sample file paths for different document types."""
    return {
        'html': temp_dir / "test.html",
        'htm': temp_dir / "test.htm", 
        'docx': temp_dir / "test.docx",
        'xml': temp_dir / "test.xml",
        'tex': temp_dir / "test.tex",
        'latex': temp_dir / "test.latex",
        'pdf': temp_dir / "test.pdf",
        'unknown': temp_dir / "test.unknown"
    }


@pytest.fixture
def mock_extraction_result():
    """Sample extraction result structure."""
    return {
        'text': 'Sample extracted text content',
        'metadata': {
            'filename': 'test_document.pdf',
            'title': 'Test Document',
            'author': 'Test Author',
            'pages': 3,
            'words': 150,
            'extraction_time': 1.23
        },
        'math_blocks': [
            {
                'block_id': 'math_1',
                'raw_text': 'E(R) = w\'μ',
                'latex': '$E(R) = w\'\\mu$',
                'confidence': 0.85,
                'page': 1
            }
        ]
    }


@pytest.fixture(params=['html', 'docx', 'xml', 'latex'])
def extractor_type(request):
    """Parametrized fixture for different extractor types."""
    return request.param


@pytest.fixture
def registry_config():
    """Configuration for extractor registry testing."""
    return {
        'load_plugins': True,
        'fallback_enabled': True,
        'log_level': 'DEBUG'
    }


@pytest.fixture
def mock_entry_point():
    """Mock entry point for plugin testing."""
    mock_ep = Mock()
    mock_ep.name = "test_plugin"
    mock_ep.value = "test_plugins.extractors:TestExtractor"
    
    # Mock extractor class
    mock_extractor_class = Mock()
    mock_extractor_instance = Mock()
    mock_extractor_instance.extractor_name = "Test Plugin Extractor"
    mock_extractor_instance.supported_extensions = [".test"]
    mock_extractor_class.return_value = mock_extractor_instance
    
    mock_ep.load.return_value = mock_extractor_class
    return mock_ep


# Test markers for different test types
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "unit: mark test as unit test")
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "requires_api: mark test as requiring API keys")


# Pytest collection hook to set default markers
def pytest_collection_modifyitems(config, items):
    """Modify test items to add default markers."""
    for item in items:
        # Add 'unit' marker by default
        if not any(marker.name in ['integration', 'slow'] for marker in item.iter_markers()):
            item.add_marker(pytest.mark.unit)
        
        # Add 'requires_api' marker for tests that need API keys
        if 'openai' in item.name.lower() or 'mathpix' in item.name.lower():
            item.add_marker(pytest.mark.requires_api)


# Skip tests that require API keys unless explicitly enabled
def pytest_runtest_setup(item):
    """Setup for each test run."""
    if 'requires_api' in [marker.name for marker in item.iter_markers()]:
        if not item.config.getoption('--run-api-tests', default=False):
            pytest.skip("API tests disabled (use --run-api-tests to enable)")


def pytest_addoption(parser):
    """Add custom pytest options."""
    parser.addoption(
        "--run-api-tests",
        action="store_true",
        default=False,
        help="Run tests that require API keys"
    )
    parser.addoption(
        "--run-slow-tests",
        action="store_true",
        default=False,
        help="Run slow tests"
    )