# Expert Detail Questions

## Q6: Should the EPUB extractor process chapters individually (maintaining chapter boundaries) or combine all chapters into a single text output like the PDF extractor?
**Default if unknown:** Process individually (EPUB files are inherently structured by chapters, and the DOCX extractor preserves similar structural elements like headings and sections)

## Q7: Should the EPUB extractor extract and preserve inline MathML content by converting it to LaTeX format using the existing MathDetector system?
**Default if unknown:** Yes (the system has sophisticated MathML handling capabilities, and EPUB technical documents commonly use MathML for mathematical expressions)

## Q8: Should the EPUB extractor add a new entry point in pyproject.toml following the existing pattern of "epub = src.ingestion.extractors.epub:EPUBExtractor"?
**Default if unknown:** Yes (all existing extractors use this entry point pattern for automatic discovery and registration)

## Q9: Should the EPUB extractor support both EPUB2 and EPUB3 formats, or focus only on EPUB3 given its better mathematical content support?
**Default if unknown:** Support both (ebooklib handles both formats seamlessly, and many technical documents exist in EPUB2 format)

## Q10: Should the EPUB extractor include table of contents (TOC) information in the extracted metadata following the same pattern as the DOCX extractor's heading extraction?
**Default if unknown:** Yes (TOC is valuable structural metadata, and the DOCX extractor already demonstrates the pattern for preserving document structure in metadata)