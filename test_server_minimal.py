#!/usr/bin/env python3
"""
Minimal test server to verify DBpedia integration.
"""

import os
import uvicorn
from src.settings import get_settings
from src.frontend.app import create_app

def main():
    # Skip config validation for testing
    os.environ['SKIP_CONFIG_VALIDATION'] = '1'
    
    # Load settings and create app
    settings = get_settings()
    app = create_app(settings)
    
    print(f"Starting test server on {settings.web_host}:{settings.web_port}")
    print(f"DBpedia integration enabled: {settings.enable_dbpedia}")
    print(f"Routes registered: {len(app.routes)}")
    
    # Run server
    uvicorn.run(
        app,
        host=settings.web_host,
        port=settings.web_port,
        log_level="info"
    )

if __name__ == "__main__":
    main()