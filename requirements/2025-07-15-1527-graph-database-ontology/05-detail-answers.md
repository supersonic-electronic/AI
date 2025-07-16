# Expert Requirements Answers

## Q1: Should we extend the existing FinancialMathOntology class in src/knowledge/ontology.py to include external ontology connectors?
**Answer:** Yes

## Q2: Will the new document types (HTML, DOCX, etc.) follow the same extraction pattern as PDFIngestor in src/ingestion/pdf2txt.py?
**Answer:** Yes

## Q3: Should real-time graph updates use a file system watcher or a message queue system?
**Answer:** Yes (file system watcher)

## Q4: Do you want to integrate with specific external knowledge bases like DBpedia or Wikidata?
**Answer:** Yes

## Q5: Should the external ontology integration cache results locally to avoid repeated API calls?
**Answer:** Yes