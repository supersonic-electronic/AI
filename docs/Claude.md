# PDF Ingestion System Documentation

This document describes the PDF text and metadata extraction system using `src/ingestion/pdf2txt.py`.

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

### File Handling
- **`encoding`**: Text file encoding (default: `"utf-8"`)
- **`json_indent`**: JSON file indentation for readability (default: `2`)
- **`overwrite_existing`**: Overwrite existing output files (default: `true`)

## Usage

### a) Non-interactive CLI (claude code …)

For batch processing or scripted usage, provide all directories via command-line flags:

```bash
python src/ingestion/pdf2txt.py --input-dir ./pdfs --text-dir ./output/text --meta-dir ./output/meta --non-interactive
```

**Available flags:**
- `--input-dir`: Directory containing PDF files to process
- `--text-dir`: Directory where extracted text files will be saved  
- `--meta-dir`: Directory where metadata JSON files will be saved
- `--config`: Path to configuration YAML file (default: `config.yaml`)
- `--non-interactive`: Run without interactive prompts

### b) Interactive mode (prompts with defaults)

Run the script without directory flags to enter interactive mode:

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

Press **Enter** to use the default values shown in brackets, or type a new path.

### c) Flag overrides

Command-line flags always take precedence over both config defaults and interactive input:

```bash
python src/ingestion/pdf2txt.py --input-dir /custom/path --text-dir ./output
```

This will:
1. Use `/custom/path` for input (overriding config and prompts)
2. Use `./output` for text output (overriding config and prompts)  
3. Prompt for metadata directory with config default

## Processing Features

### Parallel Processing
When `parallel_workers > 1` in config, the system processes multiple PDFs simultaneously using ThreadPoolExecutor, significantly reducing processing time for large batches.

### Progress Tracking
When `show_progress` is enabled, a progress bar displays current processing status using tqdm.

### Resume Capability
Set `skip_existing: true` in config to skip files that already have both .txt and .json outputs, enabling interrupted processing to resume efficiently.

### Enhanced DOI Detection
The system uses configurable regex patterns and multiple search strategies to extract DOIs from PDF metadata fields (title, subject, keywords, author).

### File Logging
Configure `log_to_file: true` to maintain persistent logs in addition to console output, useful for debugging and audit trails.

## Output Structure

For each processed PDF file `document.pdf`, the system generates:

- **Text file**: `{text_dir}/document.txt` - Extracted text content with preserved reading order
- **Metadata file**: `{meta_dir}/document.json` - JSON containing:
  - Basic file info (filename, file_size)
  - PDF metadata (title, author, subject, creator, producer)
  - Timestamps (creation_date, modification_date)
  - Keywords and extracted DOI
  - Only non-empty fields are included

## Dependencies

- **PyMuPDF** (`fitz`): PDF text extraction
- **PyYAML** (`yaml`): Configuration file parsing
- **tqdm**: Progress bar display
- **concurrent.futures**: Parallel processing (Python standard library)