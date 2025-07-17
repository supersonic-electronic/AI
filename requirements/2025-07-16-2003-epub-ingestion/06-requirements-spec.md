# EPUB Ingestion Requirements Specification

**Date:** 2025-07-16  
**Requirement ID:** epub-ingestion  
**Priority:** Medium  
**Complexity:** Medium  

## Problem Statement

The current document ingestion system supports PDF, HTML, DOCX, XML, and LaTeX formats but lacks support for EPUB files. EPUB is a common format for technical and academic documents that often contain mathematical formulas and structured content. Adding EPUB support will enhance the system's document processing capabilities and allow ingestion of ebooks and digital publications.

## Solution Overview

Implement a new EPUBExtractor following the existing pluggable extractor architecture pattern. The extractor will leverage the ebooklib library to parse EPUB files, extract text content with chapter structure preservation, handle mathematical formulas through MathML-to-LaTeX conversion, and integrate seamlessly with the existing document processing pipeline.

## Functional Requirements

### FR1: EPUB File Processing
- **Description:** Extract text content from EPUB files while preserving chapter structure
- **Details:** 
  - Process each chapter individually to maintain document structure
  - Support both EPUB2 and EPUB3 format specifications
  - Handle multi-chapter documents with proper chapter boundaries
  - Extract content from XHTML files within the EPUB archive
- **Acceptance Criteria:**
  - EPUB files are automatically detected by file extension (.epub)
  - Text content is extracted with chapter separation markers
  - Both EPUB2 and EPUB3 formats are successfully processed

### FR2: Mathematical Content Extraction
- **Description:** Extract and preserve mathematical formulas from EPUB files
- **Details:**
  - Parse inline MathML content found in EPUB chapters
  - Convert MathML expressions to LaTeX format using existing MathDetector patterns
  - Integrate with existing mathematical content detection pipeline
  - Preserve mathematical symbols and complex equations
- **Acceptance Criteria:**
  - MathML content is detected and extracted from EPUB chapters
  - Mathematical expressions are converted to LaTeX format
  - Existing math detection confidence scoring applies to EPUB content

### FR3: Metadata Extraction
- **Description:** Extract comprehensive metadata from EPUB files
- **Details:**
  - Extract Dublin Core metadata (title, creator, subject, description, publisher, date, language)
  - Extract EPUB-specific metadata (identifier, coverage, rights)
  - Extract and preserve table of contents structure
  - Include chapter count and reading order information
- **Acceptance Criteria:**
  - All available Dublin Core metadata fields are extracted
  - Table of contents structure is preserved in metadata
  - Chapter information is included in extraction results

### FR4: Automatic Format Detection
- **Description:** Integrate EPUB detection into the existing DocumentDetector system
- **Details:**
  - Add EPUB MIME type detection (`application/epub+zip`)
  - Add file extension detection for `.epub` files
  - Add content-based detection using ZIP signature and EPUB structure markers
  - Follow existing multi-layered detection pattern (extension, MIME, content)
- **Acceptance Criteria:**
  - EPUB files are automatically detected by DocumentDetector
  - Detection works through extension, MIME type, and content analysis
  - False positives are minimized through proper signature detection

### FR5: Pipeline Integration
- **Description:** Integrate EPUB processing with existing document pipeline
- **Details:**
  - Follow existing chunking and embedding pipeline
  - Support same configuration options as other extractors
  - Enable mathematical concept extraction from EPUB content
  - Preserve text quality for downstream processing
- **Acceptance Criteria:**
  - EPUB text flows through existing chunking system
  - Mathematical concepts are extracted from EPUB content
  - Text quality matches other extractor outputs

## Technical Requirements

### TR1: Library Dependencies
- **Primary Dependency:** Add `ebooklib>=0.18` to pyproject.toml dependencies
- **Existing Dependencies:** Leverage BeautifulSoup (already available) for HTML/XML parsing
- **Standard Libraries:** Use zipfile for archive handling (built-in)

### TR2: Extractor Implementation
- **File Location:** `src/ingestion/extractors/epub.py`
- **Class Name:** `EPUBExtractor`
- **Base Class:** Inherit from `BaseExtractor` following existing pattern
- **Interface Methods:** Implement `can_handle()`, `extract_text()`, `extract_metadata()`
- **Properties:** Define `supported_extensions = ['.epub']` and appropriate extractor name

### TR3: Registration Integration
- **Entry Point:** Add `epub = "src.ingestion.extractors.epub:EPUBExtractor"` to pyproject.toml
- **Import Statement:** Add EPUBExtractor import to `src/ingestion/extractors/__init__.py`
- **DocumentDetector:** Add EPUB detection logic to `src/ingestion/extractors/document_detector.py`

### TR4: Configuration Extensions
- **File:** Add EPUB-specific settings to `config.yaml`
- **Options:** Include chapter processing options, MathML handling settings
- **Integration:** Use existing math_detection_threshold and chunking parameters

### TR5: Mathematical Content Handling
- **MathML Parsing:** Implement MathML-to-LaTeX conversion functionality
- **Integration:** Use existing MathDetector for formula identification and scoring
- **Pattern Matching:** Apply existing mathematical symbol recognition to EPUB content

## Implementation Hints and Patterns

### Code Structure Pattern (Based on DOCXExtractor)
```python
class EPUBExtractor(BaseExtractor):
    def __init__(self):
        """Initialize the EPUB extractor."""
        self.book = None
    
    def can_handle(self, file_path: Path) -> bool:
        """Check if file has .epub extension."""
        return file_path.suffix.lower() == '.epub'
    
    def extract_text(self, file_path: Path, config: Dict[str, Any]) -> str:
        """Extract text with chapter processing."""
        # Load EPUB using ebooklib
        # Process chapters individually
        # Handle MathML content
        # Apply text cleaning
    
    def extract_metadata(self, file_path: Path, config: Dict[str, Any]) -> Dict[str, Any]:
        """Extract EPUB metadata and TOC."""
        # Extract Dublin Core metadata
        # Build table of contents structure
        # Include chapter statistics
```

### DocumentDetector Integration Pattern
```python
# In _detect_by_extension method - add .epub handling
# In _detect_by_mime_type method - add application/epub+zip
# In _detect_by_content method - add ZIP signature + EPUB structure detection
```

### Error Handling Pattern (Follow Existing Extractors)
```python
try:
    # EPUB processing logic
    return result
except Exception as e:
    import logging
    logger = logging.getLogger(__name__)
    logger.error(f"Error extracting from {file_path}: {e}")
    raise
```

## Acceptance Criteria

### AC1: File Format Support
- [ ] EPUB files with .epub extension are detected and processed
- [ ] Both EPUB2 and EPUB3 formats work correctly
- [ ] Multi-chapter EPUB files are processed with chapter boundaries preserved
- [ ] Empty or corrupted EPUB files are handled gracefully with appropriate error messages

### AC2: Mathematical Content
- [ ] MathML expressions in EPUB chapters are detected and converted to LaTeX
- [ ] Mathematical symbols and formulas preserve their meaning through conversion
- [ ] Existing MathDetector confidence scoring applies to EPUB mathematical content
- [ ] Complex equations (integrals, summations, fractions) are handled correctly

### AC3: Metadata Extraction
- [ ] Dublin Core metadata fields (title, author, subject, etc.) are extracted when present
- [ ] Table of contents structure is preserved and accessible in metadata
- [ ] Chapter count and reading order information is included
- [ ] EPUB-specific metadata (identifier, publisher, rights) is extracted

### AC4: System Integration
- [ ] EPUB files are automatically detected by DocumentDetector without manual configuration
- [ ] EPUB text content flows through existing chunking and embedding pipeline
- [ ] Mathematical concepts are successfully extracted from EPUB content
- [ ] CLI interface processes EPUB files using standard ingest command

### AC5: Performance and Quality
- [ ] Large EPUB files (>50MB) are processed without memory issues
- [ ] Processing speed is comparable to similar-sized documents in other formats
- [ ] Text quality is preserved through extraction and cleaning processes
- [ ] No regression in existing extractor functionality

## Test Plan

### Unit Tests (New Test File: `tests/test_epub_extractor.py`)

#### Test Cases for EPUBExtractor
1. **test_can_handle_epub_files()** - Verify .epub extension detection
2. **test_can_handle_non_epub_files()** - Verify other extensions are rejected
3. **test_extract_text_basic_epub()** - Test text extraction from simple EPUB
4. **test_extract_text_multi_chapter()** - Test chapter boundary preservation
5. **test_extract_text_with_mathml()** - Test mathematical content extraction
6. **test_extract_metadata_dublin_core()** - Test metadata extraction
7. **test_extract_metadata_table_of_contents()** - Test TOC structure preservation
8. **test_error_handling_corrupted_epub()** - Test error handling for invalid files
9. **test_epub2_format_support()** - Test EPUB2 specific features
10. **test_epub3_format_support()** - Test EPUB3 specific features

#### Test Cases for DocumentDetector Integration
1. **test_detect_epub_by_extension()** - Test extension-based detection
2. **test_detect_epub_by_mime_type()** - Test MIME type detection
3. **test_detect_epub_by_content()** - Test content-based detection
4. **test_epub_detection_confidence()** - Test detection confidence scoring

#### Test Cases for Mathematical Content
1. **test_mathml_to_latex_conversion()** - Test MathML parsing and conversion
2. **test_mathematical_symbol_preservation()** - Test symbol recognition
3. **test_complex_formula_handling()** - Test complex mathematical expressions

### Integration Tests

#### Processing Pipeline Tests
1. **test_epub_cli_integration()** - Test EPUB processing through CLI interface
2. **test_epub_chunking_pipeline()** - Test text chunking with EPUB content
3. **test_epub_concept_extraction()** - Test concept extraction from EPUB content
4. **test_epub_mathematical_concept_detection()** - Test math concept extraction

#### Performance Tests
1. **test_large_epub_processing()** - Test processing of large EPUB files
2. **test_multi_chapter_performance()** - Test performance with many chapters
3. **test_memory_usage_epub_processing()** - Monitor memory usage during processing

### Test Data Requirements
- Sample EPUB2 and EPUB3 files with mathematical content
- EPUB files with complex table of contents structures
- EPUB files with various metadata configurations
- Corrupted/invalid EPUB files for error testing
- Large EPUB files for performance testing

## Documentation Updates

### Code Documentation
- [ ] Add comprehensive docstrings to EPUBExtractor class and methods
- [ ] Document configuration options in config.yaml comments
- [ ] Add type hints for all new functions and methods
- [ ] Include usage examples in docstrings

### User Documentation
- [ ] Update README.md to include EPUB in supported formats list
- [ ] Add EPUB-specific configuration options to documentation
- [ ] Include EPUB processing examples in user guide
- [ ] Document any EPUB-specific limitations or considerations

### Developer Documentation  
- [ ] Update `docs/modules/ingestion.rst` to include EPUB extractor
- [ ] Add EPUB extractor to architecture documentation
- [ ] Document mathematical content handling for EPUB
- [ ] Include EPUB in extractor development guide

## Git & GitHub Workflow

### Commit Strategy
1. **Initial Implementation Commit:**
   ```
   feat: Add EPUB extractor with chapter processing and MathML support
   
   - Implement EPUBExtractor class with ebooklib integration
   - Add Dublin Core metadata extraction
   - Support both EPUB2 and EPUB3 formats
   - Preserve chapter structure in text output
   
   🤖 Generated with [Claude Code](https://claude.ai/code)
   
   Co-Authored-By: Claude <noreply@anthropic.com>
   ```

2. **Integration Commit:**
   ```
   feat: Integrate EPUB extractor with document detection system
   
   - Add EPUB detection to DocumentDetector
   - Register EPUBExtractor entry point
   - Update pyproject.toml dependencies
   
   🤖 Generated with [Claude Code](https://claude.ai/code)
   
   Co-Authored-By: Claude <noreply@anthropic.com>
   ```

3. **Test Implementation Commit:**
   ```
   test: Add comprehensive test suite for EPUB extraction
   
   - Unit tests for EPUBExtractor functionality
   - Integration tests for DocumentDetector
   - Mathematical content extraction tests
   - Performance and error handling tests
   
   🤖 Generated with [Claude Code](https://claude.ai/code)
   
   Co-Authored-By: Claude <noreply@anthropic.com>
   ```

### Branch Strategy
- Create feature branch: `feature/epub-ingestion-support`
- Implement changes in incremental commits
- Ensure all tests pass before merging
- Consider breaking into smaller PRs if implementation becomes large

### Pull Request Guidelines
- Include demo with sample EPUB files
- Document any breaking changes (none expected)
- Verify all existing extractor tests still pass
- Include performance benchmarks for EPUB processing

## Risk Assessment

### Technical Risks
- **Medium:** MathML parsing complexity may require additional testing
- **Low:** ebooklib dependency stability (mature, well-maintained library)
- **Low:** Integration complexity (follows existing extractor patterns)

### Mitigation Strategies
- Implement comprehensive MathML test cases with various mathematical expressions
- Use specific ebooklib version pinning to ensure compatibility
- Follow existing extractor patterns closely to minimize integration issues
- Implement graceful fallbacks for unsupported EPUB features

## Assumptions

1. **EPUB Content Quality:** Assumes well-formed EPUB files with valid XHTML content
2. **Mathematical Content:** Assumes MathML is the primary mathematical notation in EPUB files
3. **Performance:** Assumes EPUB files will be similar in size to existing document types
4. **Integration:** Assumes existing mathematical content detection patterns apply to EPUB
5. **Dependencies:** Assumes ebooklib library provides sufficient EPUB parsing capabilities
6. **Configuration:** Assumes existing chunking and processing settings work well for EPUB content

## Success Metrics

- EPUB files process successfully through the ingestion pipeline
- Mathematical content extraction quality matches or exceeds PDF extraction
- Processing performance is within 20% of equivalent-sized PDF documents
- Zero regression in existing extractor functionality
- User documentation is clear and complete
- Test coverage exceeds 90% for new EPUB-related code