# Expert Requirements Questions

## Q1: Should we extend the existing FinancialMathOntology class in src/knowledge/ontology.py to include external ontology connectors?
**Default if unknown:** Yes (maintains architectural consistency with existing ontology framework)

## Q2: Will the new document types (HTML, DOCX, etc.) follow the same extraction pattern as PDFIngestor in src/ingestion/pdf2txt.py?
**Default if unknown:** Yes (consistent with existing extractor architecture in src/ingestion/extractors/)

## Q3: Should real-time graph updates use a file system watcher or a message queue system?
**Default if unknown:** File system watcher (simpler implementation, no external dependencies)

## Q4: Do you want to integrate with specific external knowledge bases like DBpedia or Wikidata?
**Default if unknown:** Yes (most common external knowledge bases for concept enrichment)

## Q5: Should the external ontology integration cache results locally to avoid repeated API calls?
**Default if unknown:** Yes (improves performance and reduces API costs)