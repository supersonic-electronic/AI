# Expert Detail Answers

## Q6: Should the EPUB extractor process chapters individually (maintaining chapter boundaries) or combine all chapters into a single text output like the PDF extractor?
**Answer:** Process individually

## Q7: Should the EPUB extractor extract and preserve inline MathML content by converting it to LaTeX format using the existing MathDetector system?
**Answer:** Yes

## Q8: Should the EPUB extractor add a new entry point in pyproject.toml following the existing pattern of "epub = src.ingestion.extractors.epub:EPUBExtractor"?
**Answer:** Yes

## Q9: Should the EPUB extractor support both EPUB2 and EPUB3 formats, or focus only on EPUB3 given its better mathematical content support?
**Answer:** Both

## Q10: Should the EPUB extractor include table of contents (TOC) information in the extracted metadata following the same pattern as the DOCX extractor's heading extraction?
**Answer:** Yes