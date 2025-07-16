# Context Findings - Phase 3

## Current System Architecture

### Data Storage
- **Knowledge Graph**: JSON format stored in `data/knowledge_graph.json` with concepts and relationships
- **Vector Database**: Pickle/NumPy format in `data/vector_database.*` with TF-IDF vectors
- **Raw Data**: 15 PDF documents processed into 20,821 text chunks

### Existing Visualization Component
- **File**: `src/knowledge/graph_viz.py` - Basic matplotlib/networkx visualization
- **Capabilities**: Static network plots, document concept visualization, export to GEXF/GraphML
- **Limitations**: No web interface, no interactivity, requires matplotlib/networkx

### Current Technology Stack
- **Backend**: Python 3.9+, Poetry dependency management
- **Dependencies**: PyMuPDF, Pydantic, FastAPI components available, scikit-learn
- **Data Processing**: Comprehensive PDF-to-knowledge pipeline implemented
- **CLI Interface**: Full command-line interface in `src/cli.py`

### Knowledge Graph Structure
```json
{
  "concepts": {
    "concept_id": {
      "id": "unique_id",
      "name": "Portfolio",
      "type": "investment_vehicle",
      "frequency": 7492,
      "context": "Found 135 times in document.txt",
      "source_docs": ["doc1.txt", "doc2.txt"]
    }
  },
  "relationships": [
    {
      "source": "concept_id_1",
      "target": "concept_id_2", 
      "type": "co_occurs",
      "confidence": 0.3
    }
  ]
}
```

## Best Practices Research - 2025 Web Technologies

### Backend Framework Recommendation: FastAPI
- **Performance**: Fastest Python web framework (after Starlette/Uvicorn)
- **Modern Standards**: OAuth 2.0, OpenAPI, JSON Schema compatibility
- **Async Support**: Native async/await for concurrent requests
- **Auto Documentation**: Built-in Swagger UI and ReDoc
- **Validation**: Automatic request validation with Python type hints
- **Trend**: 20% usage in 2025, growing rapidly

### Frontend Visualization Library Recommendation: Cytoscape.js
- **Performance**: Highly optimized for large-scale graphs
- **Features**: Built-in graph algorithms, automatic positioning, stylesheet-based styling
- **License**: MIT (open source)
- **Academic Backing**: University of Toronto, published in Oxford Bioinformatics
- **Use Case**: Perfect for knowledge graphs with concepts and relationships

### Alternative Options Considered
- **D3.js**: Maximum customization but steep learning curve
- **Vis.js**: Deprecated/community-maintained, limited algorithms
- **Commercial**: Ogma, KeyLines (expensive, overkill for this use case)

## Integration Points Identified

### API Endpoints Needed
1. `GET /api/graph` - Full knowledge graph data
2. `GET /api/concepts` - List all concepts with filtering
3. `GET /api/concepts/{id}` - Individual concept details
4. `GET /api/search` - Search concepts by name/type
5. `GET /api/relationships/{id}` - Get concept relationships

### Data Format Requirements
- Convert current JSON format to Cytoscape.js format
- Node structure: `{data: {id, name, type, frequency, source_docs}}`
- Edge structure: `{data: {source, target, type, confidence}}`

## File Modifications Required

### New Files to Create
- `src/frontend/` - New directory structure
- `src/frontend/app.py` - FastAPI application
- `src/frontend/api/` - API route handlers
- `src/frontend/static/` - HTML, CSS, JavaScript files
- `src/frontend/templates/` - HTML templates

### Files to Modify
- `pyproject.toml` - Add FastAPI, Jinja2, static file serving dependencies
- `src/cli.py` - Add new `serve` command to launch web server
- `src/knowledge/ontology.py` - Add JSON export format methods

## Similar Patterns in Codebase
- **CLI Command Structure**: Follow pattern in `src/cli.py` for new `serve` command
- **Settings Management**: Use existing `src/settings.py` for configuration
- **JSON Handling**: Follow pattern in knowledge graph storage
- **Error Handling**: Follow logging patterns from existing modules

## Technical Constraints
- **Python Version**: >=3.9 (compatible with FastAPI)
- **Dependencies**: Must work with existing Poetry setup
- **Data Access**: Read-only access to knowledge graph JSON files
- **Port Management**: Need configurable port for web server
- **Static Files**: Need to serve HTML/CSS/JS from Python backend

## Professional Design Requirements
- **Responsive**: Mobile-friendly layout
- **Modern UI**: Clean, professional styling with CSS framework
- **Performance**: Efficient rendering of large graphs
- **Accessibility**: Proper semantic HTML and ARIA labels
- **User Experience**: Intuitive navigation and controls