# PDF Ingestion System Documentation

This document describes the enhanced PDF text and metadata extraction system using `src/ingestion/pdf2txt.py` with YAML-based configuration, interactive CLI, parallel processing, and comprehensive logging.

## Overview

The PDF ingestion system has evolved to include:
- **YAML-based configuration** (`config.yaml`) for centralized settings management
- **Interactive CLI** with smart defaults and override capabilities
- **Parallel processing** with configurable worker threads for improved performance
- **Enhanced DOI parsing** using robust regex patterns and multiple search strategies
- **Global logging mechanism** with file output and structured entry formatting
- **Plugin-style architecture** for extensible document format support
- **Large PDF streaming** support for memory-efficient processing

## Configuration

The system uses a YAML configuration file (`config.yaml`) to define default settings. All configuration keys and their descriptions:

### Directory Paths
- **`input_dir`**: Directory containing PDF files to process (default: `"./data/papers"`)
- **`text_dir`**: Directory for extracted text files (.txt) (default: `"./data/text"`)
- **`meta_dir`**: Directory for metadata JSON files (default: `"./data/metadata"`)

### Logging Configuration
- **`log_level`**: Logging verbosity level (default: `"INFO"`, options: DEBUG, INFO, WARNING, ERROR)
- **`log_to_file`**: Whether to log to file in addition to console (default: `true`)
- **`log_file`**: Log file path when file logging is enabled (default: `"./logs/pdf_ingestion.log"`)

### DOI Extraction
- **`doi_regex`**: Regular expression pattern for DOI extraction (default: `"10\\.[0-9]{4,}[-._;()/:a-zA-Z0-9]*"`)
- **`doi_prefixes`**: List of DOI prefixes to search for in metadata (default: `["doi:", "DOI:", "https://doi.org/", "http://dx.doi.org/"]`)

### Processing Options
- **`parallel_workers`**: Number of parallel workers for PDF processing (default: `4`)
- **`skip_existing`**: Skip files that already have output (.txt/.json) (default: `false`)
- **`show_progress`**: Show progress bar during processing (default: `true`)

### PyMuPDF Text Extraction Options
- **`preserve_reading_order`**: Use sort=True in get_text() for reading order (default: `true`)
- **`warn_empty_pages`**: Log warnings for empty pages (default: `true`)
- **`include_images`**: Extract image information - future feature (default: `false`)
- **`pdf_chunk_size`**: Pages per chunk for large PDFs (default: `0` - no chunking)

### File Handling
- **`encoding`**: Text file encoding (default: `"utf-8"`)
- **`json_indent`**: JSON file indentation for readability (default: `2`)
- **`overwrite_existing`**: Overwrite existing output files (default: `true`)

## Usage

### Interactive Mode (Recommended)

Run the script without directory flags to enter interactive mode with smart defaults:

```bash
python src/ingestion/pdf2txt.py
```

The system will prompt for directories with defaults from `config.yaml`:

```
PDF Ingestion Configuration
==============================
Enter input directory [./data/papers]: 
Enter text output directory [./data/text]: 
Enter metadata directory [./data/metadata]: 
```

**Interactive Behavior:**
- Press **Enter** to accept the default values shown in brackets
- Type a custom path to override the default
- Defaults are loaded from `config.yaml` automatically
- Validation occurs before processing begins

### Non-interactive CLI

For batch processing or scripted usage, provide the `--non-interactive` flag:

```bash
python src/ingestion/pdf2txt.py --non-interactive
```

This uses all defaults from `config.yaml` without prompting.

### Command-line Overrides

Override specific settings via command-line flags (takes precedence over config and prompts):

```bash
python src/ingestion/pdf2txt.py --input-dir ./pdfs --text-dir ./output/text --meta-dir ./output/meta --non-interactive
```

**Available flags:**
- `--input-dir`: Directory containing PDF files to process
- `--text-dir`: Directory where extracted text files will be saved  
- `--meta-dir`: Directory where metadata JSON files will be saved
- `--config`: Path to configuration YAML file (default: `config.yaml`)
- `--non-interactive`: Run without interactive prompts
- `--verbose`, `-v`: Enable DEBUG level logging
- `--quiet`, `-q`: Enable ERROR level logging only

### Verbosity Control

Control logging output with mutually exclusive flags:

```bash
# Verbose mode (DEBUG level)
python src/ingestion/pdf2txt.py --verbose

# Quiet mode (ERROR level only)
python src/ingestion/pdf2txt.py --quiet
```

## Processing Features

### Parallel Processing
When `parallel_workers > 1` in config (default: 4), the system processes multiple PDFs simultaneously using ThreadPoolExecutor. This significantly reduces processing time for large batches while maintaining thread safety.

**Benefits:**
- 2-4x faster processing for large document sets
- Configurable worker count based on system resources
- Automatic fallback to sequential processing for single files

### Progress Tracking
When `show_progress` is enabled (default: `true`), a progress bar displays current processing status using tqdm:

```
Processing PDFs: 60%|██████    | 9/15 [00:20<00:10, 1.69s/it]
```

**Features:**
- Real-time progress indication
- Processing rate (files/second)
- Estimated time remaining
- File count completion status

### Enhanced DOI Detection
The system uses configurable regex patterns and multiple search strategies to extract DOIs from PDF metadata fields:

**Search Strategy:**
1. Searches title, subject, keywords, and author fields
2. Looks for DOI prefixes first (doi:, DOI:, https://doi.org/, etc.)
3. Applies regex pattern to extract clean DOI
4. Falls back to direct regex search without prefixes

**Supported DOI Formats:**
- `10.1234/example.paper`
- `doi:10.1234/example.paper`
- `https://doi.org/10.1234/example.paper`
- Complex DOIs with special characters

### Large PDF Streaming
For memory-efficient processing of large PDFs, configure `pdf_chunk_size` to process pages in chunks:

```yaml
pdf_chunk_size: 10  # Process 10 pages at a time
```

**Benefits:**
- Reduced peak memory usage
- Graceful handling of very large files
- Explicit page cleanup between chunks

### Resume Capability
Set `skip_existing: true` in config to skip files that already have both .txt and .json outputs:

```yaml
skip_existing: true
```

This enables interrupted processing sessions to resume efficiently without reprocessing completed files.

## Global Logging Mechanism

### Default Log Configuration
- **Location**: `./logs/pdf_ingestion.log` (configurable via `log_file`)
- **Format**: `TIMESTAMP - LEVEL - MESSAGE`
- **Example**: `2025-07-14 17:27:23,535 - INFO - Found 15 PDF files to process`

### Log Entry Types
- **INFO**: Processing progress, file counts, successful completions
- **WARNING**: Empty pages detected, non-critical issues
- **ERROR**: File processing failures, configuration errors
- **DEBUG**: Detailed processing information (verbose mode only)

### Log Management
- **Rotation**: Logs append to existing files (manual rotation recommended)
- **Size**: No automatic size limits (monitor disk usage for large batches)
- **Retention**: No automatic cleanup (implement external log management as needed)

### Custom Log File
Override the default log file location:

```bash
python src/ingestion/pdf2txt.py --config custom-config.yaml
```

Or modify `config.yaml`:
```yaml
log_file: "./custom/path/ingestion.log"
```

## Output Structure

For each processed PDF file `document.pdf`, the system generates:

- **Text file**: `{text_dir}/document.txt` - Extracted text content with preserved reading order
- **Metadata file**: `{meta_dir}/document.json` - JSON containing:
  - Basic file info (filename, file_size)
  - PDF metadata (title, author, subject, creator, producer)
  - Timestamps (creation_date, modification_date)
  - Keywords and extracted DOI
  - Only non-empty fields are included

## Plugin Architecture

The system supports extensible document format processing through a plugin-style extractor architecture:

### Built-in Extractors
- **PDFExtractor**: Handles .pdf files using PyMuPDF

### Adding Custom Extractors
1. Inherit from `BaseExtractor` in `src/ingestion/extractors/base.py`
2. Implement required methods: `can_handle()`, `extract_text()`, `extract_metadata()`
3. Register via entry points in `pyproject.toml`:

```toml
[project.entry-points."ingestion.extractors"]
custom = "your.module:CustomExtractor"
```

## Dependencies

- **PyMuPDF** (`fitz`): PDF text extraction and metadata
- **PyYAML** (`yaml`): Configuration file parsing
- **tqdm**: Progress bar display
- **concurrent.futures**: Parallel processing (Python standard library)
- **jsonschema**: Configuration validation (optional)

## Error Handling

The system includes comprehensive error handling:
- **Configuration validation**: Schema-based validation of `config.yaml`
- **File access errors**: Graceful handling of permission issues
- **PDF corruption**: Individual file failures don't stop batch processing
- **Memory management**: Explicit cleanup for large file processing