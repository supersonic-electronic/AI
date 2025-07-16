# Requirements Specification - Graphical Web Frontend

## Executive Summary

Create a professional, interactive web-based visualization system for the knowledge graph database, featuring real-time node manipulation, concept search, and document source integration. The system will be implemented as a standalone FastAPI web application with Cytoscape.js frontend, seamlessly integrated with existing CLI patterns and data structures.

## Technical Architecture

### Backend: FastAPI Web Server
- **Framework**: FastAPI with async/await support
- **Integration**: New `serve` command in existing `src/cli.py` pattern
- **Data Layer**: Extend `FinancialMathOntology.export_ontology()` with Cytoscape.js format conversion
- **Caching**: In-memory caching of knowledge graph data for performance
- **Configuration**: Extend existing `src/settings.py` Pydantic settings

### Frontend: Interactive Graph Visualization
- **Library**: Cytoscape.js for high-performance graph rendering
- **UI Framework**: Modern responsive design with professional styling
- **Interactivity**: Real-time node dragging, zooming, filtering
- **Search**: Full-text search across concepts and relationships

## Functional Requirements

### Core Features
1. **Interactive Graph Visualization**
   - Drag and drop nodes for custom layouts
   - Zoom and pan controls with smooth animations
   - Node selection with detailed information panels
   - Edge highlighting for relationship exploration

2. **Search and Filtering**
   - Real-time concept search by name and type
   - Relationship filtering by type and confidence
   - Document-based filtering to show concepts from specific sources
   - Advanced filters for concept properties

3. **Information Display**
   - Concept details panel showing type, frequency, source documents
   - Relationship information with confidence scores and context
   - Document source integration with page references
   - Concept hierarchy navigation

4. **Professional UI Design**
   - Enhanced color scheme building on existing palette
   - Clean, modern interface with intuitive controls
   - Responsive layout for desktop and tablet use
   - Professional typography and spacing

### API Endpoints
```
GET /api/graph                    - Full knowledge graph data
GET /api/concepts                 - List concepts with pagination/filtering
GET /api/concepts/{id}            - Individual concept details
GET /api/concepts/{id}/neighbors  - Related concepts and relationships
GET /api/search?q={query}         - Search concepts by name/content
GET /api/documents                - List source documents
GET /api/documents/{name}/concepts - Concepts from specific document
```

## Technical Implementation

### File Structure
```
src/frontend/
├── app.py                 # FastAPI application
├── api/
│   ├── __init__.py
│   ├── graph.py          # Graph data endpoints
│   ├── concepts.py       # Concept CRUD operations
│   └── search.py         # Search functionality
├── static/
│   ├── css/
│   │   └── main.css      # Professional styling
│   ├── js/
│   │   ├── main.js       # Application logic
│   │   └── graph.js      # Cytoscape.js configuration
│   └── lib/              # External libraries
└── templates/
    └── index.html        # Single-page application
```

### Enhanced Color Scheme
**Current colors** (from `graph_viz.py`) will be refined for web use:
- Portfolio: `#FF8A50` (warmer orange)
- Risk: `#E91E63` (material design pink)
- Return: `#4CAF50` (material design green)
- Optimization: `#9C27B0` (material design purple)
- Mathematical: `#2196F3` (material design blue)
- Semantic: `#607D8B` (material design blue grey)

### Data Flow
1. **Startup**: Load and cache knowledge graph JSON data
2. **Client Request**: Browser requests graph visualization page
3. **API Calls**: Frontend fetches graph data via REST API
4. **Rendering**: Cytoscape.js renders interactive graph
5. **Interaction**: User selections trigger detail panel updates

### Caching Strategy
- **Graph Data**: Cache full knowledge graph in memory on startup
- **Concept Details**: Cache individual concept data with 1-hour TTL
- **Search Results**: Cache search queries with 30-minute TTL
- **Cache Invalidation**: Manual cache clear endpoint for development

## Integration Points

### CLI Extension
Add `serve` command to `src/cli.py`:
```python
@cli.command()
@click.option('--host', default='localhost', help='Host to bind to')
@click.option('--port', default=8000, help='Port to bind to')
@click.option('--debug', is_flag=True, help='Enable debug mode')
def serve(host: str, port: int, debug: bool):
    """Launch the web visualization server."""
    # Implementation details
```

### Settings Extension
Extend `src/settings.py`:
```python
class Settings(BaseSettings):
    # Existing settings...
    
    # Web server settings
    web_host: str = "localhost"
    web_port: int = 8000
    web_debug: bool = False
    web_cache_ttl: int = 3600
```

### Data Format Conversion
Extend `ontology.py` with Cytoscape.js export:
```python
def export_for_cytoscape(self) -> Dict[str, List[Dict]]:
    """Export ontology in Cytoscape.js format."""
    return {
        "nodes": [
            {"data": {"id": c.id, "name": c.name, "type": c.concept_type.value, 
                     "frequency": c.properties.get("frequency", 0)}}
            for c in self.concepts.values()
        ],
        "edges": [
            {"data": {"source": r.source_concept_id, "target": r.target_concept_id,
                     "type": r.relationship_type.value, "confidence": r.confidence}}
            for r in self.relationships
        ]
    }
```

## Dependencies

### New Python Packages
```toml
[tool.poetry.dependencies]
fastapi = "^0.104.0"
uvicorn = "^0.24.0"
jinja2 = "^3.1.2"
python-multipart = "^0.0.6"
aiofiles = "^23.2.0"
```

### Frontend Libraries
- Cytoscape.js v3.26.0
- Modern CSS framework (custom design)
- Font Awesome for icons

## Performance Requirements

### Response Times
- Graph data loading: < 2 seconds for 20,000+ nodes
- Search results: < 500ms for concept queries
- Node interaction: < 100ms for selection/hover

### Scalability
- Support graphs up to 50,000 concepts
- Handle 10+ concurrent users
- Efficient memory usage with data streaming for large graphs

## User Experience

### Navigation Flow
1. **Landing**: Full graph view with overview statistics
2. **Exploration**: Click nodes to see details and related concepts
3. **Search**: Use search bar to find specific concepts
4. **Filtering**: Apply filters to focus on specific concept types
5. **Deep Dive**: Follow relationship paths to explore connections

### Responsive Design
- **Desktop**: Full-featured interface with side panels
- **Tablet**: Collapsed panels with modal details
- **Mobile**: Basic view mode (nice-to-have, not required)

## Quality Assurance

### Testing Strategy
- Unit tests for API endpoints
- Integration tests for data format conversion
- Frontend functionality testing with Cypress
- Performance testing with large graph datasets

### Accessibility
- Keyboard navigation support
- Screen reader compatibility
- High contrast mode support
- Semantic HTML structure

## Deployment

### Development
```bash
# Start development server
poetry run python -m src.cli serve --host 0.0.0.0 --port 8000 --debug
```

### Production Considerations
- WSGI deployment with Gunicorn
- Static file serving with CDN
- Environment-based configuration
- Logging and monitoring integration

## Success Metrics

### Functional Success
- ✅ All 20 existing concepts render correctly
- ✅ All 262 relationships display properly
- ✅ Search finds concepts within 500ms
- ✅ Graph interactions are smooth (<100ms response)

### User Experience Success
- ✅ Professional, modern visual design
- ✅ Intuitive navigation and controls
- ✅ Informative concept details and relationships
- ✅ Responsive performance with real data

## Timeline and Milestones

### Phase 1: Backend Foundation (2-3 days)
- FastAPI setup and CLI integration
- API endpoints implementation
- Data format conversion
- Caching implementation

### Phase 2: Frontend Core (2-3 days)
- Cytoscape.js integration
- Basic graph rendering
- Node/edge styling with enhanced colors
- Search functionality

### Phase 3: Polish and Integration (1-2 days)
- Professional UI styling
- Detail panels and information display
- Performance optimization
- Testing and bug fixes

**Total Estimated Timeline: 5-8 days**