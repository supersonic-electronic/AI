# AI Portfolio Optimization Project Context

## Project Overview
This is an AI-powered portfolio optimization system that processes financial research documents and uses them for intelligent investment decisions. The system combines advanced document processing with mathematical formula extraction and vector-based knowledge retrieval.

## Core Architecture

### Current Implementation Status
- ✅ **Document Ingestion**: Advanced PDF processing with mathematical formula detection
- ✅ **Text Processing**: Chunking and embedding pipeline with vector store integration
- ✅ **CLI Interface**: Comprehensive command-line interface with subcommands
- ✅ **Configuration**: Pydantic-based settings with YAML and environment variable support
- ❌ **Portfolio Optimization**: Core business logic - NOT YET IMPLEMENTED
- ❌ **Knowledge Management**: Semantic search and insight extraction - NOT YET IMPLEMENTED  
- ❌ **Web Frontend**: User interface - NOT YET IMPLEMENTED

### Key Components
1. **src/ingestion/**: PDF processing, mathematical detection, chunking, embedding
2. **src/cli.py**: Unified CLI with ingest, chunk, embed, test commands
3. **src/settings.py**: Centralized configuration management
4. **tests/**: Comprehensive test suite with pytest fixtures
5. **docs/**: Technical documentation and guides

### Technology Stack
- **Core**: Python 3.9+, Pydantic, PyYAML
- **PDF Processing**: PyMuPDF, advanced mathematical formula detection
- **AI/ML**: OpenAI API, Langchain, vector databases (Chroma, Pinecone)
- **OCR**: Mathpix SDK, OpenAI Vision for mathematical formulas
- **Testing**: pytest with extensive fixtures and mocking
- **Code Quality**: Black, isort, flake8, pre-commit hooks

## Development Patterns

### Code Style
- Line length: 88 characters (Black formatting)
- Type hints: Required for all public APIs
- Docstrings: Google style for all public methods
- Error handling: Comprehensive with proper exception hierarchies

### Testing Strategy
- Unit tests for individual components
- Integration tests for cross-component functionality
- Property-based tests for mathematical algorithms
- Mocking for external API dependencies

### Configuration Management
- YAML-based configuration with environment variable overrides
- Pydantic models for validation and type safety
- Separate configs for development/production environments

## Current Priorities
1. **Implement portfolio optimization engine** in src/optimizer/
2. **Build knowledge management system** in src/knowledge/
3. **Create web frontend** in src/frontend/
4. **Enhance test coverage** and add performance benchmarks
5. **Add async processing** for better scalability

## Domain Knowledge
- **Financial Mathematics**: Portfolio theory, Black-Litterman model, risk metrics
- **Document Processing**: Academic paper structure, mathematical notation
- **Vector Databases**: Semantic search, embedding strategies
- **Research Workflow**: Academic literature processing and insight extraction
