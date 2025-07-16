# Discovery Questions

## Q1: Should the enhanced metadata be automatically extracted from financial mathematics documents (PDFs) during ingestion?
**Default if unknown:** Yes (the system already has PDF ingestion via `src/ingestion/pdf.py` and math detection via `math_detector.py`, suggesting automatic extraction is the expected pattern)

## Q2: Do users need to manually add or edit concept descriptions and mathematical formulas through the web interface?
**Default if unknown:** No (based on the automated document processing architecture and lack of obvious admin/edit UI components, this appears to be primarily a read-only visualization system)

## Q3: Should mathematical formulas support complex notation beyond basic LaTeX (like matrices, multi-line equations, chemical formulas)?
**Default if unknown:** Yes (financial mathematics involves complex formulas, and the system already uses MathJax which supports advanced LaTeX)

## Q4: Will users need to search or filter concepts based on the enhanced metadata (complexity level, mathematical notation, etc.)?
**Default if unknown:** Yes (the existing search functionality in `src/frontend/api/search.py` suggests rich search capabilities are valued)

## Q5: Should the enhanced concept details include external links or references to academic papers and sources?
**Default if unknown:** Yes (academic/research context evident from financial mathematics focus and document processing suggests source attribution is important)