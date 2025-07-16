"""
FastAPI application for knowledge graph visualization.

This module creates the main FastAPI application with all routes,
middleware, and static file serving configured.
"""

import logging
from pathlib import Path
from typing import Dict, Any

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

from src.settings import Settings
from .api.graph import router as graph_router
from .api.concepts import router as concepts_router
from .api.search import router as search_router
from .api.dbpedia import router as dbpedia_router


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        Configured FastAPI application
    """
    settings = Settings()
    
    # Create FastAPI app
    app = FastAPI(
        title="Knowledge Graph Visualizer",
        description="Interactive web interface for exploring knowledge graphs",
        version="1.0.0",
        debug=settings.web_debug
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, specify exact origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include API routers
    app.include_router(graph_router, prefix="/api", tags=["graph"])
    app.include_router(concepts_router, prefix="/api", tags=["concepts"])
    app.include_router(search_router, prefix="/api", tags=["search"])
    app.include_router(dbpedia_router, prefix="/api/dbpedia", tags=["dbpedia"])
    
    # Setup static files and templates
    static_dir = settings.web_static_dir
    templates_dir = settings.web_templates_dir
    
    # Ensure directories exist
    static_dir.mkdir(parents=True, exist_ok=True)
    templates_dir.mkdir(parents=True, exist_ok=True)
    
    # Mount static files
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    
    # Setup templates
    templates = Jinja2Templates(directory=str(templates_dir))
    
    # Store settings in app state
    app.state.settings = settings
    app.state.templates = templates
    
    @app.get("/", response_class=HTMLResponse)
    async def index(request: Request):
        """Serve the main application page."""
        return templates.TemplateResponse("index.html", {"request": request})
    
    @app.get("/health")
    async def health_check() -> Dict[str, Any]:
        """Health check endpoint."""
        return {
            "status": "healthy",
            "service": "knowledge-graph-visualizer",
            "version": "1.0.0"
        }
    
    # Setup logging
    logger = logging.getLogger(__name__)
    logger.info(f"FastAPI application created with debug={settings.web_debug}")
    
    return app