# Context Findings

## Architecture Overview

The system is a **FastAPI-based web application** with comprehensive external knowledge integration capabilities. It processes financial mathematics documents and creates an interactive knowledge graph visualization.

**Technology Stack:**
- Backend: FastAPI, SQLite caching, Pydantic settings
- Frontend: Cytoscape.js graph visualization, vanilla JavaScript
- External APIs: DBpedia Lookup/SPARQL, Wikidata SPARQL
- Data Processing: Text chunking, concept extraction, relationship mapping

## Current Implementation Status

### 1. **External Ontology System** (`src/knowledge/external_ontologies.py`)

**Strengths:**
- Complete DBpedia and Wikidata connector implementation
- Sophisticated caching with ConceptCache
- Domain-aware matching with financial keyword boosting
- Error handling and retry mechanisms
- SPARQL query support for relationship discovery

**Gaps:**
- Limited relationship enrichment from external sources
- Cache serialization issues with ExternalConceptData objects
- No automated related concept pulling into graph
- Basic domain filtering that needs enhancement

### 2. **Web Application Integration**

**Current Features:**
- Full DBpedia API endpoints (`src/frontend/api/dbpedia.py`)
- Enhanced tooltips with external metadata (`src/frontend/static/js/main.js` lines 313-452)
- Visual indicators for external sources (`src/frontend/static/css/main.css` lines 897-1085)
- Search integration with external sources

**Missing Elements:**
- CSS classes for source badges (referenced but not defined)
- Related concept display in UI
- Dynamic relationship visualization from external sources
- Rich metadata fields not shown in tooltips

### 3. **Relationship System** (`src/knowledge/relationship_mapper.py`)

**Advanced Capabilities:**
- 24+ relationship types (DEPENDS_ON, MEASURES, OPTIMIZES, etc.)
- Sophisticated scoring algorithm with 5 components
- Mathematical dependency analysis
- Semantic pattern recognition
- Graph-based relationship validation

**Critical Gap:**
- Current knowledge graph only uses "co_occurs" relationships
- Advanced relationship types not populated in actual data
- No external relationship enrichment integration

### 4. **Tooltip Implementation** (`src/frontend/static/js/main.js`)

**Well-Implemented:**
- Comprehensive metadata display (16+ fields)
- DBpedia integration with clickable URIs
- Performance optimizations with caching
- Responsive positioning and animations

**Missing Fields in Tooltips:**
- `examples` - Usage examples
- `related_formulas` - Mathematical formulas
- `applications` - Real-world applications  
- `categories` - DBpedia categories
- `properties` - Extended external properties
- `related_concepts` - External related concepts

## Specific Files Requiring Modification

### Backend Files
1. **`src/knowledge/external_ontologies.py`** (Lines 441-555)
   - Fix cache serialization issues
   - Enhance domain filtering algorithm
   - Add relationship discovery from external sources
   - Implement related concept pulling

2. **`src/frontend/api/graph.py`** (Lines 146-206, 270-355)
   - Integrate relationship enrichment in graph loading
   - Add related concept nodes from external sources
   - Fix concept type mapping issues

3. **`src/knowledge/relationship_mapper.py`** (Lines 267-295)
   - Integrate external relationship discovery
   - Add cross-reference relationship types
   - Enhance confidence scoring with external evidence

### Frontend Files
4. **`src/frontend/static/js/main.js`** (Lines 313-452)
   - Add missing metadata fields to tooltips
   - Implement related concept display
   - Fix missing CSS class references

5. **`src/frontend/static/css/main.css`** (Lines 897-1085)
   - Add missing source badge CSS classes
   - Style related concept sections
   - Enhance external metadata display

6. **`src/frontend/static/js/graph.js`** (Lines 599-610, 175-237)
   - Enhance node styling for external concepts
   - Add relationship visualization for external edges
   - Implement related concept node clustering

## Integration Points

1. **Graph Loading Pipeline**: `enrich_concepts_with_dbpedia()` needs relationship enrichment
2. **Tooltip System**: Missing metadata field integration points
3. **Search API**: Cross-reference and related concept integration
4. **Concept Details**: Related concept display integration
5. **Visualization**: External relationship edge rendering

## Performance Considerations

- **Caching**: ConceptCache needs serialization fix for ExternalConceptData
- **API Efficiency**: Batch relationship queries for external sources
- **Frontend**: Lazy loading for related concepts to prevent UI overwhelm
- **Memory**: Pagination for large related concept sets

## Similar Features Analysis

The system already has excellent foundations in:
- Domain-specific concept matching
- External source visual indicators  
- Tooltip metadata integration
- Search functionality across sources

Missing features can leverage existing patterns:
- Tooltip field rendering patterns for new metadata
- Visual styling patterns for related concepts
- API endpoint patterns for relationship data
- Caching patterns for external relationship data