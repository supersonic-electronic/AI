#!/usr/bin/env python3
"""
Main entry point for the AI Knowledge Graph system.

This module provides the main entry points for the system:
- CLI operations (ingest, chunk, embed, test)
- Web server startup
- Workflow testing
"""

import sys
import argparse
from pathlib import Path

# Add src to Python path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

def run_cli():
    """Run the CLI interface."""
    from src.cli import main as cli_main
    cli_main()

def run_server():
    """Run the web server."""
    import uvicorn
    from src.frontend.app import create_app
    from src.settings import Settings
    
    settings = Settings()
    app = create_app(settings)
    
    print("Starting Knowledge Graph Visualizer...")
    print(f"Server will be available at: http://localhost:{settings.web_port}")
    print("Frontend includes Phase 3 features: performance monitoring, export, layouts, help")
    
    uvicorn.run(
        app, 
        host=settings.web_host, 
        port=settings.web_port,
        reload=settings.web_debug
    )

def run_workflow_test():
    """Run the complete workflow test."""
    from test_complete_workflow import run_workflow_test
    return run_workflow_test()

def main():
    """Main entry point with subcommands."""
    parser = argparse.ArgumentParser(
        description="AI Knowledge Graph System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py cli --help           # Show CLI help
  python main.py server               # Start web server
  python main.py test                 # Run workflow test
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # CLI subcommand
    cli_parser = subparsers.add_parser('cli', help='Run CLI operations')
    cli_parser.add_argument('cli_args', nargs='*', help='Arguments to pass to CLI')
    
    # Server subcommand  
    server_parser = subparsers.add_parser('server', help='Start web server')
    
    # Test subcommand
    test_parser = subparsers.add_parser('test', help='Run workflow test')
    
    args = parser.parse_args()
    
    if args.command == 'cli':
        # Temporarily modify sys.argv for CLI
        original_argv = sys.argv
        sys.argv = ['cli.py'] + args.cli_args
        try:
            run_cli()
        finally:
            sys.argv = original_argv
    elif args.command == 'server':
        run_server()
    elif args.command == 'test':
        success = run_workflow_test()
        sys.exit(0 if success else 1)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()