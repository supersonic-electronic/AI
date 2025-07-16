#!/usr/bin/env python3
"""
Enhanced test server to demonstrate the new concept details functionality.
"""

import json
import uvicorn
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware

# Create FastAPI app
app = FastAPI(title="Enhanced Knowledge Graph Test Server")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_dir = Path("src/frontend/static")
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Load test data
test_data_file = Path("test_data/knowledge_graph.json")
if test_data_file.exists():
    with open(test_data_file) as f:
        test_data = json.load(f)
else:
    test_data = {"concepts": {}, "relationships": [], "stats": {}}

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    """Serve the main HTML page."""
    template_file = Path("src/frontend/templates/index.html")
    if template_file.exists():
        return FileResponse(template_file)
    else:
        return HTMLResponse("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Enhanced Knowledge Graph Test</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .concept { border: 1px solid #ddd; margin: 20px 0; padding: 20px; border-radius: 8px; }
                .latex { background: #f8f9fa; padding: 10px; margin: 10px 0; border-radius: 4px; font-family: 'Times New Roman', serif; }
                .tag { background: #007bff; color: white; padding: 4px 8px; margin: 2px; border-radius: 12px; font-size: 12px; display: inline-block; }
            </style>
            <!-- MathJax for LaTeX rendering -->
            <script>
                MathJax = {
                    tex: {
                        inlineMath: [['$', '$'], ['\\\\(', '\\\\)']],
                        displayMath: [['$$', '$$'], ['\\\\[', '\\\\]']],
                        processEscapes: true
                    }
                };
            </script>
            <script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
            <script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
        </head>
        <body>
            <h1>Enhanced Knowledge Graph Test Server</h1>
            <p>The enhanced functionality includes:</p>
            <ul>
                <li>LaTeX mathematical formulas</li>
                <li>Detailed concept definitions</li>
                <li>Examples and applications</li>
                <li>Prerequisites and complexity levels</li>
                <li>External links and metadata</li>
            </ul>
            <p><strong>API Endpoints Available:</strong></p>
            <ul>
                <li><a href="/api/graph/data">GET /api/graph/data</a> - Graph data</li>
                <li><a href="/api/concepts">GET /api/concepts</a> - List concepts</li>
                <li>GET /api/concepts/{id} - Individual concept details</li>
            </ul>
            <div id="concepts"></div>
            <script>
                // Load and display concepts
                fetch('/api/concepts')
                    .then(response => response.json())
                    .then(data => {
                        const container = document.getElementById('concepts');
                        data.concepts.forEach(concept => {
                            const div = document.createElement('div');
                            div.className = 'concept';
                            div.innerHTML = `
                                <h3>${concept.name}</h3>
                                <p><strong>Type:</strong> ${concept.type}</p>
                                ${concept.definition ? `<p><strong>Definition:</strong> ${concept.definition}</p>` : ''}
                                ${concept.latex ? `<div class="latex">$$${concept.latex}$$</div>` : ''}
                                ${concept.examples && concept.examples.length > 0 ? `
                                    <p><strong>Examples:</strong></p>
                                    <ul>${concept.examples.map(ex => `<li>${ex}</li>`).join('')}</ul>
                                ` : ''}
                                ${concept.keywords && concept.keywords.length > 0 ? `
                                    <div>
                                        <strong>Keywords:</strong>
                                        ${concept.keywords.map(kw => `<span class="tag">${kw}</span>`).join('')}
                                    </div>
                                ` : ''}
                            `;
                            container.appendChild(div);
                        });
                        // Process LaTeX
                        if (typeof MathJax !== 'undefined') {
                            MathJax.typesetPromise();
                        }
                    })
                    .catch(error => console.error('Error loading concepts:', error));
            </script>
        </body>
        </html>
        """)

@app.get("/api/graph/data")
async def get_graph_data():
    """Get complete graph data."""
    return test_data

@app.get("/api/concepts")
async def get_concepts():
    """Get paginated list of concepts."""
    concepts_list = []
    for concept_id, concept_data in test_data["concepts"].items():
        concept_data_copy = concept_data.copy()
        concept_data_copy["id"] = concept_id
        concepts_list.append(concept_data_copy)
    
    return {
        "concepts": concepts_list,
        "total": len(concepts_list),
        "page": 1,
        "per_page": len(concepts_list)
    }

@app.get("/api/concepts/{concept_id}")
async def get_concept(concept_id: str):
    """Get detailed information about a specific concept."""
    if concept_id not in test_data["concepts"]:
        raise HTTPException(status_code=404, detail=f"Concept {concept_id} not found")
    
    concept_data = test_data["concepts"][concept_id].copy()
    concept_data["id"] = concept_id
    
    # Add some mock related concepts
    concept_data["related_concepts"] = [
        {
            "name": "Related Concept 1",
            "type": "formula",
            "relationship_type": "derives_from"
        },
        {
            "name": "Related Concept 2", 
            "type": "metric",
            "relationship_type": "applies_to"
        }
    ]
    
    return concept_data

@app.get("/api/search/types")
async def get_concept_types():
    """Get available concept types."""
    types = {}
    for concept_data in test_data["concepts"].values():
        concept_type = concept_data.get("type", "unknown")
        if concept_type not in types:
            types[concept_type] = 0
        types[concept_type] += 1
    
    return {
        "types": [
            {"type": type_name, "count": count}
            for type_name, count in types.items()
        ]
    }

@app.get("/api/search/suggestions")
async def get_search_suggestions(q: str, limit: int = 8):
    """Get search suggestions."""
    suggestions = []
    q_lower = q.lower()
    
    for concept_id, concept_data in test_data["concepts"].items():
        name = concept_data.get("name", "")
        if q_lower in name.lower():
            suggestions.append({
                "text": name,
                "type": concept_data.get("type", "unknown")
            })
    
    return {"suggestions": suggestions[:limit]}

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "enhanced-knowledge-graph-test",
        "concepts_loaded": len(test_data["concepts"])
    }

def main():
    print("Starting Enhanced Knowledge Graph Test Server...")
    print("🚀 Server will be available at: http://127.0.0.1:8002")
    print("📊 Enhanced concept data loaded with LaTeX support")
    print("🔬 Test concepts include:")
    
    for concept_id, concept_data in test_data["concepts"].items():
        name = concept_data.get("name", "Unknown")
        has_latex = "✓" if concept_data.get("latex") else "✗"
        has_definition = "✓" if concept_data.get("definition") else "✗"
        print(f"   - {name}: LaTeX={has_latex}, Definition={has_definition}")
    
    print("\nPress Ctrl+C to stop")
    
    uvicorn.run(app, host="127.0.0.1", port=8002, log_level="info")

if __name__ == "__main__":
    main()