# AI-Powered Portfolio Optimization

An AI-driven portfolio optimization system that ingests research documents, processes them with advanced text extraction, and uses them for generating high-quality methodology and code. The end goal is a web-based application allowing user input and intelligent portfolio optimization recommendations.

## Features

- **PDF Document Ingestion**: Advanced PDF text and metadata extraction with parallel processing
- **Improved Mathematical Formula Detection**: High-precision mathematical content detection with 97.5% false positive reduction
- **Document Chunking and Embedding**: Advanced text chunking with mathematical content preservation and vector store integration
- **YAML-based Configuration**: Centralized settings management with smart defaults
- **Interactive CLI**: User-friendly command-line interface with configurable prompts
- **Enhanced DOI Detection**: Robust regex-based DOI extraction from academic papers
- **Parallel Processing**: Multi-threaded document processing for improved performance
- **Global Logging**: Comprehensive logging with file output and structured formatting
- **Plugin Architecture**: Extensible document format support
- **Large File Support**: Memory-efficient streaming for very large PDFs
- **OCR Integration**: Optional Mathpix and OpenAI Vision OCR for complex mathematical formulas

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
- **PyYAML** (`pyyaml`): YAML configuration file parsing
- **tqdm**: Progress bar display for batch operations
- **jsonschema**: Configuration validation (optional but recommended)
- **Pillow** (`pillow`): Image processing for mathematical formula extraction
- **openai**: OpenAI API integration for advanced mathematical OCR and embeddings
- **langchain-text-splitters**: Advanced text chunking with mathematical content awareness
- **pinecone-client**: Cloud vector database integration (optional)
- **chromadb**: Local vector database integration (optional)

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

Convert PDFs to text and metadata with mathematical formula extraction:

```bash
# Basic usage with defaults from config.yaml
poetry run python -m src.cli ingest

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
│   └── ingestion/
│       ├── pdf2txt.py       # Main ingestion script
│       ├── chunk_embed.py   # Document chunking and embedding pipeline
│       ├── config_schema.py # Configuration validation
│       ├── extractor_registry.py # Plugin management
│       └── extractors/      # Document format extractors
├── data/
│   ├── papers/             # Input PDFs (default)
│   ├── text/               # Extracted text output with mathematical markers
│   ├── metadata/           # JSON metadata output
│   ├── math/               # Mathematical formula files (.math, .refs)
│   └── chroma_db/          # Local Chroma vector database (optional)
├── logs/                   # Processing logs
├── tests/                  # Unit tests
├── examples/               # Usage examples and demonstrations
└── docs/
    └── Claude.md           # Detailed technical documentation
```

## Output Format

For each processed PDF `document.pdf`, the system generates:

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

### Running Tests
```bash
# Run all tests
poetry run pytest tests/ -v

# Run with coverage
poetry run pytest tests/ -v --cov=src --cov-report=html

# Run specific test file
poetry run pytest tests/test_math_detector.py -v
```

### Adding New Document Formats
1. Create a new extractor class inheriting from `BaseExtractor`
2. Implement required methods: `can_handle()`, `extract_text()`, `extract_metadata()`
3. Register via entry points in `pyproject.toml`

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

## Support

For detailed technical documentation, see [docs/Claude.md](docs/Claude.md).

For issues and feature requests, please use the project's issue tracker.