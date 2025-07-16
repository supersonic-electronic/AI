# AI Knowledge Graph System

A comprehensive system for extracting, processing, and visualizing knowledge from academic documents using advanced AI techniques. Features an interactive web-based visualization with Phase 3 enhancements including performance monitoring, export capabilities, and advanced user interactions.

## 🚀 Quick Start

```bash
# Install dependencies
poetry install

# Test the complete workflow  
poetry run python main.py test

# Launch the interactive web application
poetry run python main.py server
# Visit: http://localhost:8000
```

## ✨ Key Features

### 📊 Interactive Web Visualization
- **Real-time Knowledge Graph** - Interactive visualization with Cytoscape.js
- **Dynamic Search** - Real-time concept search with intelligent suggestions
- **Multiple Layouts** - 6 layout algorithms (force-directed, circular, grid, hierarchical, concentric, directed)
- **Export Options** - PNG, SVG, and JSON export with high-resolution support
- **Interactive Tooltips** - Enhanced metadata display on graph node hover

### 🎨 Phase 3 Enhancements (Production Ready)
- **Performance Monitoring** - Real-time metrics, memory usage tracking, API performance
- **Advanced UI/UX** - Material Design, responsive layout, dark mode support
- **Accessibility** - Full ARIA compliance, keyboard navigation, high contrast support
- **Help System** - Interactive help modal with comprehensive keyboard shortcuts
- **Error Handling** - Robust error boundaries with user-friendly recovery options

### 🔧 Development & DevOps Features
- **Comprehensive CI/CD** - GitHub Actions workflows with quality gates, testing, and deployment
- **Configuration Validation** - JSON Schema validation with startup error checking
- **Plugin Architecture** - Entry point-based plugin discovery for extensible document processing
- **Pre-commit Hooks** - Automated code quality, security, and testing checks
- **Documentation** - Sphinx-based API documentation with GitHub Pages deployment
- **Type Safety** - mypy type checking with comprehensive coverage

### 🧠 Enhanced Graph Metadata (Latest)
- **Complexity Analysis** - Automatic extraction of beginner/intermediate/advanced levels
- **Prerequisite Mapping** - Identifies concept dependencies from document context
- **Domain Classification** - Categorizes concepts by mathematics, finance, economics domains
- **Advanced Search Filtering** - Filter by complexity, domain, and prerequisite relationships
- **Expanded Symbol Support** - 150+ mathematical notation mappings including financial notation

## Features

### Document Processing
- **Multi-Format Document Support**: Extract content from PDF, HTML, DOCX, XML, and LaTeX documents
- **Automatic Document Type Detection**: Intelligent format detection using extension, MIME type, and content analysis
- **Advanced Mathematical Formula Detection**: High-precision mathematical content detection with 97.5% false positive reduction
- **Enhanced DOI Detection**: Robust regex-based DOI extraction from academic papers
- **OCR Integration**: Optional Mathpix and OpenAI Vision OCR for complex mathematical formulas

### Real-Time Processing
- **File System Monitoring**: Watch directories for document changes with real-time processing
- **Incremental Updates**: Efficient incremental graph updates for modified documents
- **Batch Processing**: Optimized batch processing with parallel execution and progress tracking
- **Concept Deduplication**: Intelligent deduplication across different document types

### Knowledge Management
- **External Knowledge Base Integration**: Automatic concept enrichment with DBpedia and Wikidata ontologies
- **Graph Database Support**: Neo4j integration for concept relationship mapping and ontology storage
- **Intelligent Caching**: High-performance concept caching with TTL and LRU eviction
- **Document Chunking and Embedding**: Advanced text chunking with mathematical content preservation and vector store integration

### System Features
- **YAML-based Configuration**: Centralized settings management with smart defaults
- **Enhanced CLI**: Comprehensive command-line interface with watch, batch, and monitoring commands
- **Parallel Processing**: Multi-threaded document processing for improved performance
- **Global Logging**: Comprehensive logging with file output and structured formatting
- **Plugin Architecture**: Extensible document format support
- **Large File Support**: Memory-efficient streaming for very large documents
- **Progress Tracking**: Real-time progress reporting for long-running operations

## Installation

### Prerequisites
- Python 3.9 or higher
- Poetry (recommended) or pip

### Using Poetry (Recommended)
```bash
git clone <repository-url>
cd AI
poetry install
```

**Note: This project uses Poetry for dependency management. All commands should be run with `poetry run` or within the Poetry environment (`poetry shell`).**

### Using pip (Alternative)
```bash
git clone <repository-url>
cd AI
pip install pymupdf pyyaml tqdm jsonschema
```

### Additional Dependencies
The system requires the following key packages:
- **PyMuPDF** (`pymupdf`): PDF text extraction and metadata processing
- **python-docx**: DOCX document processing
- **beautifulsoup4**: HTML document parsing and extraction
- **lxml**: XML document processing and parsing
- **watchdog**: File system monitoring for real-time processing
- **PyYAML** (`pyyaml`): YAML configuration file parsing
- **tqdm**: Progress bar display for batch operations
- **jsonschema**: Configuration validation (optional but recommended)
- **Pillow** (`pillow`): Image processing for mathematical formula extraction
- **openai**: OpenAI API integration for advanced mathematical OCR and embeddings
- **langchain-text-splitters**: Advanced text chunking with mathematical content awareness
- **pinecone-client**: Cloud vector database integration (optional)
- **chromadb**: Local vector database integration (optional)
- **neo4j**: Graph database driver for concept relationship storage (optional)
- **requests**: HTTP client for external ontology API calls
- **SPARQLWrapper**: SPARQL query support for semantic web ontologies (optional)

## Usage

The system provides a unified CLI with subcommands for different operations. All commands support global options for configuration and logging.

### Global Options

```bash
# Use custom configuration file
poetry run python -m src.cli --config custom-config.yaml <command>

# Enable verbose logging
poetry run python -m src.cli --verbose <command>

# Enable quiet mode (errors only)
poetry run python -m src.cli --quiet <command>
```

### Ingest Command

Process documents from multiple formats (PDF, HTML, DOCX, XML, LaTeX):

```bash
# Basic usage with defaults from config.yaml (all supported formats)
poetry run python -m src.cli ingest

# Process specific document types only
poetry run python -m src.cli ingest --file-types pdf html docx

# Custom directories
poetry run python -m src.cli ingest --input-dir ./research-papers --text-dir ./output

# Disable mathematical formula extraction
poetry run python -m src.cli ingest --no-math

# Enable math OCR fallback (requires API keys)
poetry run python -m src.cli ingest --math-ocr

# Use parallel processing
poetry run python -m src.cli ingest --parallel-workers 8

# Skip files that already have output
poetry run python -m src.cli ingest --skip-existing
```

### Chunk Command

Split extracted text into chunks with mathematical content preservation:

```bash
# Basic chunking with defaults
poetry run python -m src.cli chunk

# Custom chunk parameters
poetry run python -m src.cli chunk --chunk-size 1000 --chunk-overlap 100

# Preserve mathematical content boundaries
poetry run python -m src.cli chunk --preserve-math

# Custom input and output directories
poetry run python -m src.cli chunk --input-dir ./custom/text --output-dir ./custom/chunks
```

### Embed Command

Generate embeddings and store in vector databases:

```bash
# Use local Chroma database (default)
poetry run python -m src.cli embed --local

# Use Pinecone cloud database
poetry run python -m src.cli embed --vectorstore pinecone --namespace research-docs

# Custom embedding parameters
poetry run python -m src.cli embed --batch-size 50 --embedding-model text-embedding-3-large

# Custom input directory
poetry run python -m src.cli embed --input-dir ./custom/chunks
```

### Test Command

Run the test suite with various options:

```bash
# Run all tests
poetry run python -m src.cli test

# Run with coverage reporting
poetry run python -m src.cli test --coverage

# Run specific test markers
poetry run python -m src.cli test --markers unit
poetry run python -m src.cli test --markers integration

# Run specific test file or directory
poetry run python -m src.cli test --test-path tests/test_math_detector.py

# Stop after N failures
poetry run python -m src.cli test --maxfail 3
```

### Watch Command

Monitor directories for real-time document processing:

```bash
# Watch single directory for HTML and PDF files
poetry run python -m src.cli watch --watch-dirs ./documents --file-types html pdf

# Watch multiple directories recursively
poetry run python -m src.cli watch --watch-dirs ./docs ./papers ./reports --recursive

# Use batch mode for high-volume scenarios
poetry run python -m src.cli watch --watch-dirs ./documents --batch-mode --batch-size 5

# Custom ignore patterns
poetry run python -m src.cli watch --watch-dirs ./documents --ignore-patterns "*.tmp" "*.bak" ".*"

# Monitor all supported formats
poetry run python -m src.cli watch --watch-dirs ./documents --file-types pdf html docx xml latex
```

### Batch Command

Efficient batch processing with optimization features:

```bash
# Basic batch processing
poetry run python -m src.cli batch --input-dir ./documents

# Process specific file types with parallel workers
poetry run python -m src.cli batch --input-dir ./documents --file-types pdf docx --max-workers 8

# Enable concept deduplication
poetry run python -m src.cli batch --input-dir ./documents --deduplicate

# Use external ontology enrichment
poetry run python -m src.cli batch --input-dir ./documents --external-ontologies

# Custom batch size and progress reporting
poetry run python -m src.cli batch --input-dir ./documents --batch-size 20 --progress

# Comprehensive processing with all features
poetry run python -m src.cli batch --input-dir ./documents --deduplicate --external-ontologies --max-workers 4
```

### Complete Workflow Examples

Process documents end-to-end:

```bash
# Full pipeline with custom settings
poetry run python -m src.cli --config production-config.yaml ingest --parallel-workers 8
poetry run python -m src.cli --config production-config.yaml chunk --chunk-size 800
poetry run python -m src.cli --config production-config.yaml embed --vectorstore pinecone --namespace prod-docs

# Development workflow with testing
poetry run python -m src.cli ingest --verbose --no-math
poetry run python -m src.cli chunk --preserve-math
poetry run python -m src.cli embed --local
poetry run python -m src.cli test --coverage

# Real-time processing workflow
poetry run python -m src.cli watch --watch-dirs ./incoming-docs --file-types pdf html docx --batch-mode

# Batch processing with optimization
poetry run python -m src.cli batch --input-dir ./archive-docs --deduplicate --external-ontologies --progress

# Multi-format processing
poetry run python -m src.cli ingest --file-types html xml latex --input-dir ./mixed-formats
poetry run python -m src.cli batch --input-dir ./mixed-formats --file-types html xml latex --deduplicate
```

## Configuration

The system uses YAML files for centralized configuration. Two configurations are provided:

- **`config.yaml`**: Standard configuration with original math detection
- **`config-improved-math.yaml`**: Enhanced configuration with improved mathematical detection (recommended)

### Using the Improved Configuration

For best results with mathematical content detection, use the improved configuration:

```bash
python -m src.cli --config config-improved-math.yaml ingest
```

Key settings:

### Directory Configuration
- **`input_dir`**: Source directory containing PDF files to process
- **`text_dir`**: Output directory for extracted text files (.txt)
- **`meta_dir`**: Output directory for metadata JSON files
- **`math_dir`**: Output directory for mathematical formula files (.math, .refs)

### Processing Options
- **`parallel_workers`**: Number of parallel processing threads (default: 4)
- **`skip_existing`**: Skip files that already have output files (useful for resuming)
- **`show_progress`**: Display progress bar during batch operations
- **`pdf_chunk_size`**: Pages per chunk for large PDF streaming (0 = no chunking)

### Logging Settings
- **`log_level`**: Logging verbosity (DEBUG, INFO, WARNING, ERROR)
- **`log_to_file`**: Enable file logging in addition to console output
- **`log_file`**: Path for log file output

### DOI Extraction
- **`doi_regex`**: Regular expression pattern for DOI detection
- **`doi_prefixes`**: List of DOI prefixes to search for in metadata

### Mathematical Formula Extraction
- **`extract_math`**: Enable advanced mathematical formula detection and extraction
- **`separate_math_files`**: Save mathematical formulas to separate .math files
- **`math_detection_threshold`**: Minimum confidence score for mathematical content (recommended: 3)
- **`math_ocr_fallback`**: Use Mathpix or OpenAI Vision OCR for complex mathematical formulas
- **`mathpix_app_id`**: Mathpix application ID for specialized mathematical OCR
- **`mathpix_app_key`**: Mathpix application key for specialized mathematical OCR
- **`openai_api_key`**: API key for OpenAI integration (required for OCR and embeddings)

#### Improved Mathematical Detection
The system now uses an enhanced mathematical content detector that:
- **Reduces false positives by 97.5%**: Eliminates detection of page numbers, citations, and regular text
- **Maintains high precision**: Only detects genuine mathematical expressions and formulas
- **Provides detailed confidence scoring**: Each detection includes confidence and breakdown analysis
- **Supports OCR fallback**: Optional integration with Mathpix and OpenAI Vision for complex formulas

### Document Chunking and Embedding
- **`chunk_size`**: Target size for text chunks in characters
- **`chunk_overlap`**: Overlap between adjacent chunks
- **`embedding_model`**: OpenAI embedding model to use
- **`embedding_batch_size`**: Number of texts to embed per batch
- **`pinecone_api_key`**: Pinecone API key for cloud vector storage
- **`chroma_persist_directory`**: Local Chroma database directory

### External Knowledge Base Integration
- **`enable_external_ontologies`**: Enable automatic concept enrichment with external ontologies
- **`enable_dbpedia`**: Enable DBpedia knowledge base integration
- **`enable_wikidata`**: Enable Wikidata knowledge base integration
- **`external_ontology_timeout`**: Timeout for external API calls in seconds
- **`external_ontology_max_retries`**: Maximum retry attempts for failed API calls
- **`cache_dir`**: Directory for caching external ontology data
- **`max_cache_size`**: Maximum number of cached concepts
- **`cache_ttl_hours`**: Time-to-live for cached entries in hours

### Graph Database Configuration
- **`enable_graph_db`**: Enable Neo4j graph database integration
- **`neo4j_uri`**: Neo4j database connection URI
- **`neo4j_username`**: Neo4j database username
- **`neo4j_password`**: Neo4j database password
- **`neo4j_database`**: Neo4j database name
- **`graph_concept_threshold`**: Minimum confidence for storing concepts in graph
- **`graph_relationship_threshold`**: Minimum confidence for storing relationships

### Text Processing
- **`preserve_reading_order`**: Maintain reading order during text extraction
- **`warn_empty_pages`**: Log warnings for empty pages in PDFs
- **`encoding`**: Text file encoding for output files
- **`json_indent`**: JSON formatting indentation for metadata files

## Logging

### Default Log Location
The system logs to `./logs/pdf_ingestion.log` by default, with entries formatted as:
```
2025-07-14 17:27:23,535 - INFO - Found 15 PDF files to process
2025-07-14 17:27:24,378 - INFO - Successfully processed: research-paper.pdf
2025-07-14 17:27:25,740 - WARNING - Empty page found: 7 in document.pdf
```

### Log Entry Types
- **INFO**: Processing progress, successful completions, file counts
- **WARNING**: Empty pages detected, non-critical processing issues
- **ERROR**: File processing failures, configuration errors
- **DEBUG**: Detailed processing information (verbose mode only)

### Custom Log Path
Change the log file location by modifying `config.yaml`:
```yaml
log_file: "./custom/path/processing.log"
```

Or use a custom configuration file:
```bash
poetry run python src/ingestion/pdf2txt.py --config ./my-config.yaml
```

### Log Management
- Logs append to existing files (manual rotation recommended for large batches)
- No automatic size limits or cleanup (implement external log management as needed)
- Monitor disk usage for long-running or high-volume processing

## Project Structure

```
├── config.yaml              # Main configuration file
├── src/
│   ├── cli.py               # Enhanced command-line interface
│   ├── ingestion/
│   │   ├── pdf2txt.py       # Main ingestion script
│   │   ├── chunk_embed.py   # Document chunking and embedding pipeline
│   │   ├── config_schema.py # Configuration validation
│   │   ├── extractor_registry.py # Plugin management
│   │   └── extractors/      # Document format extractors
│   │       ├── base.py      # Base extractor interface
│   │       ├── pdf.py       # PDF document extractor
│   │       ├── html.py      # HTML document extractor
│   │       ├── docx.py      # DOCX document extractor
│   │       ├── xml.py       # XML document extractor
│   │       ├── latex.py     # LaTeX document extractor
│   │       └── document_detector.py # Automatic format detection
│   ├── knowledge/
│   │   ├── ontology.py      # Financial mathematics ontology framework
│   │   ├── concept_extractor.py # Concept extraction from documents
│   │   ├── external_ontologies.py # External knowledge base connectors
│   │   ├── concept_cache.py # Caching layer for external API calls
│   │   └── graph_db.py      # Neo4j graph database integration
│   ├── monitoring/          # Real-time processing components
│   │   ├── file_watcher.py  # File system monitoring
│   │   └── incremental_processor.py # Incremental graph updates
│   ├── optimization/        # Performance optimization
│   │   ├── batch_processor.py # Batch processing optimization
│   │   └── concept_deduplicator.py # Concept deduplication
│   └── settings.py          # Centralized configuration management
├── data/
│   ├── papers/             # Input documents (default)
│   ├── text/               # Extracted text output with mathematical markers
│   ├── metadata/           # JSON metadata output
│   ├── math/               # Mathematical formula files (.math, .refs)
│   ├── cache/              # External ontology cache storage
│   └── chroma_db/          # Local Chroma vector database (optional)
├── logs/                   # Processing logs
├── tests/                  # Comprehensive test suite
│   ├── test_extractors.py  # Document extractor tests
│   ├── test_monitoring.py  # Real-time processing tests
│   ├── test_optimization.py # Optimization component tests
│   └── test_integration.py # End-to-end integration tests
├── examples/               # Usage examples and demonstrations
└── docs/
    ├── Claude.md           # Detailed technical documentation
    └── external-knowledge-integration.md # External ontology integration guide
```

## Output Format

For each processed document (PDF, HTML, DOCX, XML, or LaTeX), the system generates:

### Text File (`./data/text/document.txt`)
- Plain text content with enhanced mathematical markers
- Bidirectional references to mathematical expressions
- Semantic annotations for mathematical content
- Preserved reading order when configured
- UTF-8 encoding by default

Example enhanced text with mathematical markers:
```
[MATHREF_math_p1_l15_3057] $x_{1} = Rx_{0} and x_{1} = (1 + r)x_{0} .$ @group:general_math @related:MATHREF_math_p1_l7_5023 @confidence:0.50
```

### Metadata File (`./data/metadata/document.json`)
```json
{
  "filename": "document.pdf",
  "file_size": 2048576,
  "title": "Research Paper Title",
  "author": "Author Name",
  "creation_date": "D:20231201120000",
  "doi": "10.1234/example.paper",
  "keywords": "portfolio, optimization, research",
  "math_blocks_count": 47,
  "has_mathematical_content": true,
  "semantic_groups": {
    "portfolio_theory": 15,
    "general_math": 25,
    "equation": 7
  }
}
```

### Mathematical Formula File (`./data/math/document.math`)
Detailed JSON containing all mathematical expressions with:
- Unique block identifiers for cross-referencing
- Character-level positioning in the document
- LaTeX representations of formulas
- Semantic grouping and confidence scores
- Related expression cross-references
- Context preservation (surrounding text)

### Reference Mapping File (`./data/math/document.refs`)
Bidirectional lookup tables enabling:
- Find text position from mathematical expression ID
- Find mathematical expression from text position
- Semantic group organization
- Efficient cross-referencing for downstream processing

### Vector Database Output
When using the chunk embedding pipeline, additional outputs are created:

**Local Chroma Database** (`./data/chroma_db/`):
- Persistent vector storage with mathematical content preservation
- Searchable embeddings with comprehensive metadata
- Bidirectional references to source documents and mathematical expressions

**Pinecone Cloud Index**:
- Scalable cloud vector storage
- Namespace organization for different document collections
- Enterprise-grade search and retrieval capabilities

**Usage Examples:**

```bash
# Process documents and create local vector database
python src/ingestion/chunk_embed.py --local --verbose

# Process with cloud Pinecone storage
python src/ingestion/chunk_embed.py --vectorstore pinecone --namespace research_docs

# Custom processing with configuration
python src/ingestion/chunk_embed.py --input-dir ./custom/text --config ./custom-config.yaml --local
```

## Development

### CI/CD Pipeline

The project includes comprehensive GitHub Actions workflows:

#### Continuous Integration (`.github/workflows/ci.yml`)
- **Code Quality**: Black, isort, flake8, mypy checks
- **Security Audit**: Safety dependency scanning
- **Multi-version Testing**: Python 3.9-3.12 compatibility
- **Coverage Reporting**: Codecov integration with 70% minimum coverage
- **Integration Tests**: Complete workflow validation
- **Documentation**: Automatic Sphinx documentation building

#### Release Automation (`.github/workflows/release.yml`)
- **Automated Releases**: Tag-based release creation
- **Build Artifacts**: Distribution packages and archives
- **GitHub Pages**: Documentation deployment

### Development Setup

1. **Install pre-commit hooks** (recommended):
   ```bash
   poetry install --with dev
   pre-commit install
   ```

2. **Run quality checks manually**:
   ```bash
   # Code formatting
   poetry run black src/ tests/
   poetry run isort src/ tests/
   
   # Linting
   poetry run flake8 src/ tests/
   poetry run mypy src/
   
   # Security scan
   poetry run bandit -r src/
   ```

3. **Build documentation**:
   ```bash
   cd docs/
   poetry run sphinx-build -b html . _build/html
   ```

### Configuration Validation

The system includes comprehensive configuration validation:

```bash
# Validate configuration at startup (automatic)
poetry run python -m src.cli --config config.yaml ingest

# Manual validation
poetry run python -c "from src.config_validator import validate_config_file; validate_config_file()"
```

**Configuration Schema Features:**
- JSON Schema validation for all configuration options
- Legacy configuration transformation for backward compatibility
- Detailed error messages with field-level validation
- Startup validation with clear error reporting

### Running Tests
```bash
# Run all tests
poetry run pytest tests/ -v

# Run with coverage
poetry run pytest tests/ -v --cov=src --cov-report=html

# Run specific test file
poetry run pytest tests/test_math_detector.py -v

# Run tests by marker
poetry run pytest -m unit tests/
poetry run pytest -m integration tests/

# CLI test runner
poetry run python -m src.cli test --coverage --markers unit
```

### Plugin System

The system uses entry points for plugin discovery, supporting both built-in and external extractors:

#### Built-in Extractors (via entry points)
All built-in extractors are registered in `pyproject.toml`:
```toml
[project.entry-points."project.plugins"]
pdf = "src.ingestion.extractors.pdf:PDFExtractor"
html = "src.ingestion.extractors.html:HTMLExtractor"
docx = "src.ingestion.extractors.docx:DOCXExtractor"
xml = "src.ingestion.extractors.xml:XMLExtractor"
latex = "src.ingestion.extractors.latex:LaTeXExtractor"
```

#### Adding New Document Formats

1. **Create Extractor Class**:
   ```python
   from src.ingestion.extractors.base import BaseExtractor
   
   class MyCustomExtractor(BaseExtractor):
       def can_handle(self, file_path: Path) -> bool:
           return file_path.suffix.lower() == '.mycustom'
       
       def extract_text(self, file_path: Path, config: Dict[str, Any]) -> str:
           # Implementation here
           pass
       
       def extract_metadata(self, file_path: Path, config: Dict[str, Any]) -> Dict[str, Any]:
           # Implementation here
           pass
       
       @property
       def supported_extensions(self) -> list[str]:
           return ['.mycustom']
       
       @property
       def extractor_name(self) -> str:
           return "My Custom Extractor"
   ```

2. **Register as Entry Point**:
   ```toml
   [project.entry-points."project.plugins"]
   mycustom = "my_package.extractors:MyCustomExtractor"
   ```

3. **Add Tests**:
   ```python
   # tests/test_my_extractor.py
   import pytest
   from my_package.extractors import MyCustomExtractor
   
   @pytest.mark.unit
   class TestMyCustomExtractor:
       @pytest.fixture
       def extractor(self):
           return MyCustomExtractor()
           
       def test_can_handle_mycustom_files(self, extractor, sample_file_paths):
           assert extractor.can_handle(sample_file_paths['mycustom'])
   ```

#### Plugin Discovery Features
- **Automatic Discovery**: Extractors loaded via `importlib.metadata.entry_points()`
- **Fallback Support**: Manual loading if entry points fail
- **Error Handling**: Graceful handling of missing or invalid plugins
- **Logging**: Comprehensive logging of plugin loading process

### Real-Time Processing Integration
The system supports real-time processing through file system monitoring:

1. **File Watching**: Monitor directories for document changes
2. **Incremental Processing**: Process only changed documents
3. **Batch Optimization**: Group multiple changes for efficient processing
4. **Concept Deduplication**: Remove duplicate concepts across document types

### Performance Optimization
- **Parallel Processing**: Configurable worker threads for batch operations
- **Memory Management**: Efficient handling of large documents
- **Caching**: Intelligent caching of external ontology data
- **Progress Tracking**: Real-time progress reporting for long operations

### Configuration Validation
The system includes JSON schema validation for `config.yaml`. Invalid configurations will be caught at startup with descriptive error messages.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass: `poetry run pytest tests/ -v`
5. Submit a pull request

## License

[Add your license information here]

## Documentation

### API Documentation
The project includes comprehensive Sphinx-based documentation:

```bash
# Build documentation locally
cd docs/
poetry run sphinx-build -b html . _build/html
open _build/html/index.html
```

**Documentation Features:**
- **Auto-generated API docs** from docstrings
- **Installation and setup guides**
- **Module-by-module documentation**
- **Configuration reference**
- **Development guidelines**

### Live Documentation
- **GitHub Pages**: Automatic deployment via GitHub Actions
- **URL**: `https://supersonic-electronic.github.io/AI/` (when deployed)

### Additional Resources
- [docs/Claude.md](docs/Claude.md) - Comprehensive technical documentation
- [docs/external-knowledge-integration.md](docs/external-knowledge-integration.md) - External ontology integration guide
- [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) - Deployment guidelines
- [docs/COMPLETE_WORKFLOW_GUIDE.md](docs/COMPLETE_WORKFLOW_GUIDE.md) - End-to-end workflow guide

## Support

For issues and feature requests, please use the project's issue tracker.