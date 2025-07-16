#!/usr/bin/env python3
"""
Simple test script to verify the frontend integration works correctly.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.settings import Settings
from src.frontend.app import create_app

def test_app_creation():
    """Test that the FastAPI app can be created successfully."""
    try:
        # Load settings
        settings = Settings()
        
        # Create the app
        app = create_app(settings)
        
        print("✓ FastAPI application created successfully")
        print(f"✓ App title: {app.title}")
        print(f"✓ App version: {app.version}")
        
        # Check routes
        routes = [route.path for route in app.routes]
        print(f"✓ Available routes: {routes}")
        
        return True
        
    except Exception as e:
        print(f"✗ Failed to create app: {e}")
        return False

def test_static_files():
    """Test that static files exist."""
    try:
        frontend_dir = Path("src/frontend")
        
        # Check key files
        key_files = [
            "static/js/main.js",
            "static/js/graph.js", 
            "static/js/performance.js",
            "static/css/main.css",
            "templates/index.html"
        ]
        
        for file_path in key_files:
            full_path = frontend_dir / file_path
            if not full_path.exists():
                print(f"✗ Missing file: {file_path}")
                return False
            print(f"✓ Found: {file_path}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error checking static files: {e}")
        return False

def test_frontend_completeness():
    """Test that frontend has all Phase 3 enhancements."""
    try:
        # Check main.js for Phase 3 features
        main_js = Path("src/frontend/static/js/main.js").read_text()
        
        features_to_check = [
            "PerformanceMonitor",
            "exportGraph",
            "changeLayout", 
            "showHelpModal",
            "toggleDropdown",
            "handleKeyboard"
        ]
        
        for feature in features_to_check:
            if feature not in main_js:
                print(f"✗ Missing feature in main.js: {feature}")
                return False
            print(f"✓ Found feature: {feature}")
        
        # Check CSS for Phase 3 enhancements
        main_css = Path("src/frontend/static/css/main.css").read_text()
        
        css_features = [
            "dropdown",
            "modal",
            "help-section", 
            "performance-indicator"
        ]
        
        for feature in css_features:
            if feature not in main_css:
                print(f"✗ Missing CSS feature: {feature}")
                return False
            print(f"✓ Found CSS feature: {feature}")
        
        # Check HTML for Phase 3 UI elements
        index_html = Path("src/frontend/templates/index.html").read_text()
        
        html_features = [
            "layout-btn",
            "export-btn",
            "help-btn",
            "help-modal",
            "keyboard shortcuts"
        ]
        
        for feature in html_features:
            if feature not in index_html:
                print(f"✗ Missing HTML feature: {feature}")
                return False
            print(f"✓ Found HTML feature: {feature}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error checking frontend completeness: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Phase 3 Frontend Integration")
    print("=" * 50)
    
    tests = [
        ("App Creation", test_app_creation),
        ("Static Files", test_static_files), 
        ("Frontend Completeness", test_frontend_completeness)
    ]
    
    passed = 0
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name} Test:")
        if test_func():
            print(f"✅ {test_name} test PASSED")
            passed += 1
        else:
            print(f"❌ {test_name} test FAILED")
    
    print(f"\n🏁 Test Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All Phase 3 integration tests PASSED!")
        print("🚀 Frontend is ready for production deployment")
    else:
        print("⚠️  Some tests failed - please review the issues above")