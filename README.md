# AI-Powered Portfolio Optimization

An AI-driven portfolio optimization system that ingests research documents, processes them with advanced text extraction, and uses them for generating high-quality methodology and code. The end goal is a web-based application allowing user input and intelligent portfolio optimization recommendations.

## Features

- **PDF Document Ingestion**: Advanced PDF text and metadata extraction with parallel processing
- **YAML-based Configuration**: Centralized settings management with smart defaults
- **Interactive CLI**: User-friendly command-line interface with configurable prompts
- **Enhanced DOI Detection**: Robust regex-based DOI extraction from academic papers
- **Parallel Processing**: Multi-threaded document processing for improved performance
- **Global Logging**: Comprehensive logging with file output and structured formatting
- **Plugin Architecture**: Extensible document format support
- **Large File Support**: Memory-efficient streaming for very large PDFs

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

### Using pip
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

## Usage

### Interactive Mode (Recommended)

Run the PDF ingestion system with interactive prompts:

```bash
poetry run python src/ingestion/pdf2txt.py
```

The system will prompt for directories with defaults from `config.yaml`:
```
PDF Ingestion Configuration
==============================
Enter input directory [./data/papers]: 
Enter text output directory [./data/text]: 
Enter metadata directory [./data/metadata]: 
```

Press **Enter** to accept defaults or type custom paths.

### Non-Interactive Mode

For batch processing or scripted usage:

```bash
poetry run python src/ingestion/pdf2txt.py --non-interactive
```

### Custom Configuration with Logging

Process PDFs with custom settings and logging:

```bash
poetry run python src/ingestion/pdf2txt.py --non-interactive --verbose --config ./custom-config.yaml
```

### Override Specific Directories

Override individual settings while keeping other defaults:

```bash
poetry run python src/ingestion/pdf2txt.py --input-dir ./research-papers --text-dir ./output
# Will prompt for metadata directory with config default
```

### Verbosity Control

Control logging output levels:

```bash
# Verbose mode (DEBUG level logging)
poetry run python src/ingestion/pdf2txt.py --verbose

# Quiet mode (ERROR level only)
poetry run python src/ingestion/pdf2txt.py --quiet
```

## Configuration

The system uses `config.yaml` for centralized configuration. Key settings:

### Directory Configuration
- **`input_dir`**: Source directory containing PDF files to process
- **`text_dir`**: Output directory for extracted text files (.txt)
- **`meta_dir`**: Output directory for metadata JSON files

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
│       ├── config_schema.py # Configuration validation
│       ├── extractor_registry.py # Plugin management
│       └── extractors/      # Document format extractors
├── data/
│   ├── papers/             # Input PDFs (default)
│   ├── text/               # Extracted text output
│   └── metadata/           # JSON metadata output
├── logs/                   # Processing logs
├── tests/                  # Unit tests
└── docs/
    └── Claude.md           # Detailed technical documentation
```

## Output Format

For each processed PDF `document.pdf`, the system generates:

### Text File (`./data/text/document.txt`)
- Plain text content extracted from all pages
- Preserved reading order when configured
- UTF-8 encoding by default

### Metadata File (`./data/metadata/document.json`)
```json
{
  "filename": "document.pdf",
  "file_size": 2048576,
  "title": "Research Paper Title",
  "author": "Author Name",
  "creation_date": "D:20231201120000",
  "doi": "10.1234/example.paper",
  "keywords": "portfolio, optimization, research"
}
```

## Development

### Running Tests
```bash
poetry run pytest tests/ -v
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
4. Ensure all tests pass: `poetry run pytest`
5. Submit a pull request

## License

[Add your license information here]

## Support

For detailed technical documentation, see [docs/Claude.md](docs/Claude.md).

For issues and feature requests, please use the project's issue tracker.