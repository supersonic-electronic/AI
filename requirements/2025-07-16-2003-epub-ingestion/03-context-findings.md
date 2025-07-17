# Context Findings

## Current Ingestion Architecture

### Extractor System Pattern
The system uses a sophisticated pluggable extractor architecture with these key components:

1. **BaseExtractor Abstract Class** (`src/ingestion/extractors/base.py`)
   - Defines standard interface: `can_handle()`, `extract_text()`, `extract_metadata()`
   - Properties: `supported_extensions`, `extractor_name`
   - All extractors must inherit from this base class

2. **Document Detection System** (`src/ingestion/extractors/document_detector.py`)
   - Automatic document type detection using extension, MIME type, and content analysis
   - Currently supports: PDF, HTML, DOCX, XML, LaTeX
   - Extensible registration system for new extractors
   - Multi-layered detection with fallback mechanisms

3. **Entry Points Configuration** (pyproject.toml)
   - Plugin system using `[project.entry-points."project.plugins"]`
   - Current entries: pdf, html, docx, xml, latex
   - Easy registration of new extractors without code changes

### Existing Extractors Analysis

#### PDF Extractor (`src/ingestion/extractors/pdf.py`)
- Uses PyMuPDF (fitz) library
- Handles mathematical content extraction with MathDetector integration
- Configurable options for reading order, DOI extraction, formula processing
- Supports metadata extraction including creation dates, authors, etc.

#### DOCX Extractor (`src/ingestion/extractors/docx.py`) 
- Uses python-docx library
- Comprehensive structure preservation (paragraphs, tables, headers/footers)
- Multiple table formatting options (grid, simple, CSV)
- Rich metadata extraction (core properties, statistics, document structure)
- Style information preservation and heading extraction

#### HTML Extractor (`src/ingestion/extractors/html.py`)
- Uses BeautifulSoup with configurable parsers (lxml, html.parser)
- Content cleaning and unwanted element removal
- Main content extraction vs full text extraction modes
- Encoding detection with fallback mechanisms

### Mathematical Content Support

#### MathDetector Integration (`src/ingestion/math_detector.py`)
- Precompiled regex patterns for mathematical symbols and expressions
- LaTeX symbol mapping (150+ symbols for financial mathematics)
- Greek letters, mathematical operators, subscripts/superscripts
- Font-based detection using mathematical fonts (Computer Modern, AMS, etc.)
- Configurable confidence thresholds and scoring algorithms

#### Current Mathematical Processing Pipeline
1. Text extraction from documents
2. Mathematical content detection and scoring
3. LaTeX conversion and formula preservation
4. Integration with concept extraction for mathematical concepts
5. Support for complex formulas, integrals, summations, derivatives

### Processing Pipeline Integration

#### CLI Integration (`src/cli.py`)
- Uses DocumentDetector for automatic format detection
- Unified processing interface for all document types
- Batch processing capabilities with progress tracking

#### Configuration System (`config.yaml`)
- Document chunking parameters: `chunk_size: 500`, `chunk_overlap: 50`
- Mathematical detection threshold: `math_detection_threshold: 0.3`
- Encoding, processing options, and extractor-specific settings

#### Knowledge Extraction Pipeline
- Extracted text feeds into concept extraction (`src/knowledge/concept_extractor.py`)
- Mathematical formulas are processed for concept identification
- Text chunking and embedding generation for vector stores
- Metadata preservation throughout the pipeline

## EPUB Format Analysis

### EPUB Structure Characteristics
- ZIP-based archive format containing XHTML documents
- META-INF/container.xml points to content.opf (package file)
- content.opf contains metadata, manifest, and spine
- XHTML files contain actual content (can include MathML)
- Navigation Document (nav.xhtml) provides table of contents
- Optional resources: images, CSS, fonts, etc.

### Technical Requirements for EPUB Support

#### Library Dependencies
- **ebooklib**: Primary Python library for EPUB manipulation (most popular, well-maintained)
- **BeautifulSoup**: Already available for HTML/XML parsing (will reuse existing dependency)
- **zipfile**: Built-in Python library for ZIP archive handling

#### EPUB vs HTML Processing Similarities
- EPUB content is XHTML-based, can leverage existing HTML extractor patterns
- Similar content cleaning and text extraction approaches
- Mathematical content in EPUB often uses MathML (compatible with existing math detection)
- Both require structured metadata extraction

#### Key Differences from Current Formats
- Multi-file archive structure (vs single file)
- Standardized metadata format (Dublin Core)
- Chapter/spine structure navigation
- Embedded resource handling (images, stylesheets)

### Integration Points

#### DocumentDetector Extensions Needed
- Add EPUB MIME type: `application/epub+zip`
- Extension detection: `.epub`
- Content detection: ZIP signature + specific EPUB structure markers

#### Mathematical Content Handling
- MathML parsing and conversion to LaTeX
- Integration with existing MathDetector for formula identification
- Preservation of mathematical structure across EPUB chapters

#### Metadata Extraction Requirements
- Dublin Core metadata (title, creator, subject, description, publisher, date, language)
- EPUB-specific metadata (identifier, coverage, rights)
- Chapter structure and table of contents extraction
- Reading order preservation from spine

## Related Features and Patterns

### Similar Processing Features
1. **Multi-part Document Handling**: DOCX extractor handles headers/footers/tables separately
2. **Structure Preservation**: HTML extractor maintains content hierarchy
3. **Metadata Enrichment**: All extractors provide rich metadata extraction
4. **Mathematical Content**: PDF extractor has sophisticated formula handling

### Code Patterns to Follow
1. **Extractor Registration**: Follow entry points pattern in pyproject.toml
2. **Error Handling**: Comprehensive try/catch with logging (consistent across extractors)
3. **Configuration**: Use config dict for all extractor options
4. **Text Cleaning**: Implement `_clean_text()` method with configurable options
5. **Metadata Structure**: Return dictionary with standardized keys and optional fields

### Performance Considerations
- EPUB files can be large with many chapters
- Should process chapters sequentially or in batches
- Memory management for large archives
- Existing system handles large PDFs efficiently, similar patterns applicable

## Dependencies Required

### New Dependencies
- `ebooklib>=0.18`: Primary EPUB processing library
- No additional dependencies needed (BeautifulSoup, zipfile already available)

### Configuration Extensions
- New EPUB-specific settings in config.yaml
- Integration with existing math detection and chunking settings
- Chapter processing options (individual vs combined extraction)

## Files Requiring Modification

### Core Implementation Files
1. **NEW**: `src/ingestion/extractors/epub.py` - Main EPUB extractor implementation
2. **MODIFY**: `src/ingestion/extractors/__init__.py` - Add EPUBExtractor import
3. **MODIFY**: `src/ingestion/extractors/document_detector.py` - Add EPUB detection logic
4. **MODIFY**: `pyproject.toml` - Add ebooklib dependency and entry point
5. **MODIFY**: `config.yaml` - Add EPUB-specific configuration options

### Integration Points
- CLI system will automatically detect and process EPUB files via DocumentDetector
- Mathematical content will be processed via existing MathDetector
- Text chunks will flow through existing embedding and vector store pipeline
- Knowledge extraction will work with EPUB content automatically