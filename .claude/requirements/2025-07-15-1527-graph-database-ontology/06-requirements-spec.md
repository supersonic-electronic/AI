# Requirements Specification: Enhanced Graph Database and Ontology Functionality

**Project:** AI Portfolio Optimization System  
**Feature:** Enhanced Graph Database and Ontology Functionality  
**Date:** 2025-07-15  
**Status:** Ready for Implementation

## Problem Statement

The current AI Portfolio Optimization system already has graph database and ontology functionality implemented in the `src/knowledge/` module, but it needs to be enhanced with:

1. **External Knowledge Base Integration** - Connect with DBpedia, Wikidata, and other external ontologies
2. **Multi-format Document Support** - Extend beyond PDF to support HTML, DOCX, XML, LaTeX, etc.
3. **Real-time Processing** - Enable real-time graph updates as documents are processed
4. **Performance Optimization** - Add caching and optimized processing pipelines

## Solution Overview

Enhance the existing graph database functionality by:
- Extending the `FinancialMathOntology` class with external ontology connectors
- Creating new document type ingestors following the existing PDFIngestor pattern
- Implementing a file system watcher for real-time processing
- Adding caching mechanisms for external API calls
- Maintaining single-user architecture (no multi-user support needed)

## Functional Requirements

### FR1: External Knowledge Base Integration
- **FR1.1**: Extend `FinancialMathOntology` class to connect with DBpedia and Wikidata
- **FR1.2**: Map internal concepts to external knowledge base entities
- **FR1.3**: Enrich extracted concepts with external definitions and relationships
- **FR1.4**: Cache external API results locally to improve performance
- **FR1.5**: Configure external API endpoints and authentication in settings

### FR2: Multi-format Document Support
- **FR2.1**: Create document type abstraction following existing extractor pattern
- **FR2.2**: Implement HTML document ingestor with mathematical content detection
- **FR2.3**: Implement DOCX document ingestor with formula extraction
- **FR2.4**: Implement XML document ingestor for structured mathematical content
- **FR2.5**: Implement LaTeX document ingestor for mathematical expressions
- **FR2.6**: Add automatic document type detection
- **FR2.7**: Extend CLI to support new document types

### FR3: Real-time Graph Updates
- **FR3.1**: Implement file system watcher for document directories
- **FR3.2**: Add incremental graph update capabilities
- **FR3.3**: Detect document modifications and trigger re-processing
- **FR3.4**: Add CLI commands for starting/stopping real-time monitoring
- **FR3.5**: Implement change detection to avoid unnecessary re-processing

### FR4: Performance and Caching
- **FR4.1**: Implement local caching for external ontology API calls
- **FR4.2**: Add batch processing optimization for large document sets
- **FR4.3**: Implement concept deduplication across document types
- **FR4.4**: Add progress tracking and status reporting for long-running operations

## Technical Requirements

### TR1: External Ontology Integration
- **Files to Modify**:
  - `src/knowledge/ontology.py` - Extend FinancialMathOntology class
  - `src/knowledge/concept_extractor.py` - Add external enrichment pipeline
  - `src/settings.py` - Add external API configuration
- **New Files**:
  - `src/knowledge/external_ontologies.py` - External ontology connectors
  - `src/knowledge/concept_cache.py` - Caching layer for external data
- **Dependencies**: Add `requests`, `SPARQLWrapper` for external API calls

### TR2: Document Type Support
- **Files to Modify**:
  - `src/ingestion/` - Add new document type ingestors
  - `src/knowledge/graph_integration.py` - Extend beyond PDF processing
  - `src/cli.py` - Add support for new document types
- **New Files**:
  - `src/ingestion/html_ingestor.py` - HTML document processing
  - `src/ingestion/docx_ingestor.py` - DOCX document processing
  - `src/ingestion/xml_ingestor.py` - XML document processing
  - `src/ingestion/latex_ingestor.py` - LaTeX document processing
  - `src/ingestion/document_detector.py` - Automatic type detection
- **Dependencies**: Add `python-docx`, `beautifulsoup4`, `lxml` for document parsing

### TR3: Real-time Processing
- **Files to Modify**:
  - `src/knowledge/graph_integration.py` - Add streaming capabilities
  - `src/knowledge/graph_db.py` - Add incremental update methods
  - `src/cli.py` - Add watch/monitor commands
- **New Files**:
  - `src/knowledge/file_watcher.py` - File system monitoring
  - `src/knowledge/incremental_processor.py` - Incremental processing logic
- **Dependencies**: Add `watchdog` for file system monitoring

### TR4: Database Schema Extensions
- **Neo4j Constraints**: Add constraints for external concept IDs
- **Indexes**: Add indexes for external ontology references
- **Properties**: Add external_id, external_source fields to concepts

## Implementation Hints and Patterns

### External Ontology Integration Pattern
```python
class ExternalOntologyConnector:
    def __init__(self, cache_manager):
        self.cache = cache_manager
    
    def enrich_concept(self, concept: Concept) -> Concept:
        # Check cache first
        if cached_data := self.cache.get(concept.name):
            return self.apply_enrichment(concept, cached_data)
        
        # Query external ontology
        external_data = self.query_external_ontology(concept.name)
        self.cache.set(concept.name, external_data)
        
        return self.apply_enrichment(concept, external_data)
```

### Document Type Abstraction Pattern
```python
class DocumentIngestor(ABC):
    @abstractmethod
    def extract_text(self, document_path: Path) -> str:
        pass
    
    @abstractmethod
    def extract_mathematical_content(self, document_path: Path) -> List[MathBlock]:
        pass
    
    def process_document(self, document_path: Path) -> ProcessingResult:
        # Common processing logic
        pass
```

### File Watcher Pattern
```python
class DocumentWatcher:
    def __init__(self, graph_processor):
        self.processor = graph_processor
        self.observer = Observer()
    
    def on_modified(self, event):
        if self.is_supported_document(event.src_path):
            self.processor.process_document_incrementally(event.src_path)
```

## Acceptance Criteria

### AC1: External Knowledge Base Integration
- [ ] System can connect to DBpedia and Wikidata APIs
- [ ] Extracted concepts are enriched with external definitions
- [ ] External API calls are cached locally
- [ ] Configuration allows enabling/disabling external integration
- [ ] Performance impact is minimal (< 20% processing time increase)

### AC2: Multi-format Document Support
- [ ] System can process HTML, DOCX, XML, and LaTeX documents
- [ ] Mathematical content is extracted from all document types
- [ ] Document type is automatically detected
- [ ] CLI commands work with all document types
- [ ] Processing quality is comparable to PDF processing

### AC3: Real-time Processing
- [ ] File system watcher detects new and modified documents
- [ ] Graph database is updated incrementally
- [ ] CLI commands can start/stop monitoring
- [ ] Change detection prevents unnecessary re-processing
- [ ] Real-time processing has minimal resource overhead

### AC4: Performance and Reliability
- [ ] External API caching reduces response time by > 50%
- [ ] Batch processing handles > 100 documents efficiently
- [ ] System handles document processing errors gracefully
- [ ] Memory usage remains stable during long-running operations
- [ ] All operations maintain existing logging and error handling

## Assumptions

1. **External APIs**: DBpedia and Wikidata APIs are available and stable
2. **Document Quality**: Input documents contain extractable mathematical content
3. **File System**: File system supports watching/monitoring capabilities
4. **Neo4j**: Neo4j database server is available and properly configured
5. **Dependencies**: All required Python packages can be installed via Poetry
6. **Performance**: External API calls have reasonable response times (< 5 seconds)

## Dependencies

### New Python Packages
- `requests` - HTTP requests for external APIs
- `SPARQLWrapper` - SPARQL queries for semantic web data
- `python-docx` - DOCX document processing
- `beautifulsoup4` - HTML parsing
- `lxml` - XML processing
- `watchdog` - File system monitoring

### External Services
- **DBpedia**: Public SPARQL endpoint
- **Wikidata**: Public SPARQL endpoint
- **Neo4j**: Local or remote Neo4j database instance

## Implementation Priority

1. **Phase 1 (High Priority)**: External knowledge base integration
2. **Phase 2 (High Priority)**: Multi-format document support
3. **Phase 3 (Medium Priority)**: Real-time processing capabilities
4. **Phase 4 (Low Priority)**: Performance optimizations and caching

## Success Metrics

- **Concept Enrichment**: > 80% of extracted concepts linked to external knowledge bases
- **Document Coverage**: Support for 4+ document types (HTML, DOCX, XML, LaTeX)
- **Processing Speed**: Real-time processing with < 30 second delay
- **Cache Hit Rate**: > 70% cache hit rate for external API calls
- **System Reliability**: < 5% error rate during document processing