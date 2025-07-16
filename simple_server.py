#!/usr/bin/env python3
"""
Simple test web server for enhanced concept details functionality.
"""

import logging
from pathlib import Path
import uvicorn
from src.settings import Settings
from src.frontend.app import create_app

def main():
    # Setup basic logging
    logging.basicConfig(level=logging.INFO)
    
    # Create minimal settings with mock values
    class MockSettings:
        web_static_dir = Path("src/frontend/static")
        web_templates_dir = Path("src/frontend/templates")
        web_cache_ttl = 300
        web_debug = True
    
    settings = MockSettings()
    
    # Create and run the app
    app = create_app(settings)
    
    print("Starting web server on http://127.0.0.1:8001")
    print("Open your browser to test the enhanced concept details!")
    print("Press Ctrl+C to stop")
    
    uvicorn.run(app, host="127.0.0.1", port=8001, log_level="info")

if __name__ == "__main__":
    main()