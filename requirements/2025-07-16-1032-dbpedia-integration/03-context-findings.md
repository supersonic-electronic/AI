# Context Findings - DBpedia Integration

## Existing Technology Stack
- **Backend**: Python FastAPI application (`src/frontend/app.py`)
- **Frontend**: Interactive web interface with Cytoscape.js for graph visualization
- **Database**: ChromaDB for vector storage, Neo4j support for graph database
- **External APIs**: DBpedia and Wikidata connectors already implemented

## Current Visualization System
- **Framework**: Cytoscape.js with enhanced extensions (cose-bilkent, dagre)
- **Location**: `src/frontend/static/js/graph.js` - comprehensive GraphManager class
- **Features**: Multiple layouts, export capabilities (PNG, SVG, JSON), interactive controls
- **Styling**: Material Design color scheme with concept type differentiation

## Existing DBpedia Integration
- **Core Implementation**: `src/knowledge/external_ontologies.py` 
  - Complete DBpediaConnector class with SPARQL and Lookup API support
  - WikidataConnector also implemented
  - Caching system via ConceptCache
- **Demo/Test Files**: 
  - `run_dbpedia_workflow.py` - complete workflow demonstration
  - `demo_tooltip_data.py` - tooltip data demonstration
  - `test_enhanced_tooltips.html` - advanced tooltip testing

## Current Tooltip Implementation
- **Location**: `src/frontend/static/js/main.js:200-400`
- **Features**: 
  - 300ms hover delay
  - Enhanced metadata display (FR4 implementation)
  - MathJax LaTeX rendering
  - Responsive positioning to avoid viewport overflow
  - Performance optimized with caching and lazy loading
  - Color-coded complexity levels

## Integration Points Identified
- **API Endpoints**: Need `/api/dbpedia` endpoints in `src/frontend/api/`
- **Graph Data**: Existing `src/frontend/api/graph.py` needs DBpedia data integration
- **Search System**: `src/frontend/api/search.py` needs DBpedia search capability
- **Concept Management**: `src/knowledge/concept_extractor.py` for concept processing

## Similar Features Analysis
- **External Ontology Manager**: `src/knowledge/external_ontologies.py:441-487` 
- **Concept Cache**: `src/knowledge/concept_cache.py` for performance
- **Graph Visualization**: `src/knowledge/graph_viz.py` for backend graph generation

## Technical Patterns to Follow
- **Settings Management**: Centralized in `src/settings.py`
- **API Router Pattern**: FastAPI routers in `src/frontend/api/`
- **Error Handling**: Comprehensive logging and error management
- **Configuration**: YAML-based config system with validation

## Files That Need Modification
- `src/frontend/api/graph.py` - Add DBpedia data to graph endpoint
- `src/frontend/api/search.py` - Add DBpedia search functionality  
- `src/frontend/static/js/main.js` - Enhance tooltip for DBpedia metadata
- `src/frontend/static/js/graph.js` - Add DBpedia visual indicators
- `src/frontend/static/css/main.css` - Add DBpedia styling
- `src/settings.py` - Add DBpedia-specific settings

## Current External Ontology Config Options
```yaml
enable_external_ontologies: true
enable_dbpedia: true  
enable_wikidata: true
external_ontology_timeout: 10
external_ontology_max_retries: 3
cache_dir: "./data/cache"
max_cache_size: 1000
cache_ttl_hours: 24
```