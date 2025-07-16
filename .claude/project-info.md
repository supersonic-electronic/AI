# Project Information

This file contains project metadata that was previously stored in settings.json but moved here due to Claude CLI validation requirements.

## Project Details

- **Name**: AI-Powered Portfolio Optimization
- **Description**: AI-driven portfolio optimization system with advanced PDF processing and mathematical content detection
- **Version**: 1.0.0
- **Primary Language**: Python
- **Package Manager**: Poetry
- **Python Version**: 3.9+

## Key Features

- 97.5% false positive reduction in mathematical content detection
- Enhanced mathematical formula extraction with OCR integration
- Unified CLI with subcommands for ingest/chunk/embed/test
- Pydantic-based configuration management
- Comprehensive test suite with pytest
- Pre-commit hooks for code quality
- External knowledge base integration with DBpedia and Wikidata
- Graph database support with Neo4j
- Intelligent caching system

## Main Directories

- `src/` - Source code
- `tests/` - Test suite
- `scripts/` - Utility scripts
- `data/` - Data storage
- `.claude/` - Claude CLI configuration

## Configuration Files

- `config.yaml` - Standard configuration
- `config-improved-math.yaml` - Enhanced mathematical detection
- `config-with-external-ontologies.yaml` - External knowledge integration
- `pyproject.toml` - Poetry project configuration

## Development Commands

### Installation
```bash
poetry install
```

### Running Tests
```bash
poetry run pytest                          # Basic tests
poetry run pytest --cov=src               # With coverage
poetry run pytest tests/ -v               # Verbose output
```

### Code Quality
```bash
poetry run black src/ tests/              # Format code
poetry run isort src/ tests/              # Sort imports
poetry run flake8 src/ tests/             # Lint code
```

### Application Commands
```bash
poetry run python -m src.cli              # Main CLI
poetry shell                              # Activate environment
poetry add <package>                      # Add dependency
poetry add --group dev <package>          # Add dev dependency
```

## Common Tasks

### Project Setup
```bash
poetry install
poetry run pre-commit install
```

### Run Document Ingestion
```bash
poetry run python -m src.cli --config config-improved-math.yaml ingest
```

### Run Tests with Coverage
```bash
poetry run pytest tests/ -v --cov=src --cov-report=html
```

### Lint and Format
```bash
poetry run black src/ tests/
poetry run isort src/ tests/
poetry run flake8 src/ tests/
```

## Poetry Information

- **Project File**: `pyproject.toml`
- **Lock File**: `poetry.lock`
- **Virtual Environment**: Use `poetry env info` to locate
- **Test Command**: `poetry run pytest`
- **Lint Command**: `poetry run black . && poetry run isort . && poetry run flake8 .`
- **CLI Command**: `poetry run python -m src.cli`
- **Install Command**: `poetry install`
- **Update Command**: `poetry update`

## Documentation

### Main Technical Documentation
- `docs/Claude.md` - Comprehensive technical documentation
- `docs/external-knowledge-integration.md` - External ontology integration guide

### Specialized Documentation
- `docs/Mathematical_Detection_Improvements.md` - Math detection enhancements
- `docs/OCR_Configuration.md` - OCR setup and configuration

### User Documentation
- `README.md` - Main project documentation and usage guide