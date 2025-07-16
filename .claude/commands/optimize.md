# Portfolio Optimization Commands

## Create Complete Portfolio Optimizer

```bash
claude code "Create a comprehensive portfolio optimization module in src/optimizer/ that implements:

1. Base classes: BaseOptimizer, Portfolio, RiskModel, PerformanceMetrics
2. Optimizers: MeanVarianceOptimizer, BlackLittermanOptimizer, RiskParityOptimizer
3. Risk models: HistoricalRiskModel, ShrinkageRiskModel, FactorRiskModel
4. Constraints: weight, risk, and objective function constraints
5. Integration with existing Settings and logging systems
6. Async support for large-scale optimization
7. Comprehensive error handling and type hints

Use the existing code patterns, Pydantic for config validation, and include docstrings with examples."
```

## Create Knowledge Management System

```bash
claude code "Implement a knowledge management system in src/knowledge/ with:

1. SemanticSearchEngine for querying processed documents
2. InsightExtractor for extracting investment insights
3. KnowledgeGraph for building concept relationships
4. ResearchSummarizer for generating research summaries
5. Integration with existing vector stores (Chroma/Pinecone)
6. Support for mathematical content preservation
7. Async interfaces and caching for performance
8. Research-driven portfolio optimization views

Follow existing patterns and integrate with the document processing pipeline."
```

## Create Web Frontend

```bash
claude code "Create a modern web frontend in src/frontend/ using FastAPI and React:

1. FastAPI backend with RESTful API endpoints
2. React frontend with TypeScript
3. WebSocket support for real-time updates
4. Authentication and session management
5. Interactive portfolio optimization interface
6. Document processing monitoring
7. Research search and exploration
8. Performance visualization with charts

Include proper error handling, security measures, and responsive design."
```

## Fix Technical Debt

```bash
claude code "Address technical debt in the codebase:

1. Fix dependency management in pyproject.toml
2. Add comprehensive type hints throughout
3. Implement proper exception hierarchies
4. Add configuration validation with meaningful errors
5. Remove unused imports and dead code
6. Standardize docstring format
7. Add structured logging with correlation IDs
8. Implement or remove empty main.py

Maintain backward compatibility and include tests for all changes."
```

## Add Async Processing

```bash
claude code "Refactor the document processing pipeline for async operations:

1. Convert PDFIngestor to async with aiofiles
2. Implement async batch processing for embeddings
3. Add async vector database operations
4. Create async job queues for long-running tasks
5. Use asyncio.gather() for parallel processing
6. Add timeout and cancellation support
7. Maintain CLI compatibility with asyncio.run()
8. Include comprehensive async tests

Preserve existing synchronous interfaces while adding async alternatives."
```

## Enhance Testing

```bash
claude code "Expand the test suite for comprehensive coverage:

1. Add integration tests for complete workflows
2. Create performance benchmarks and load tests
3. Add property-based tests for algorithms
4. Implement contract tests for API integrations
5. Add mutation testing for test quality
6. Create automated test data generation
7. Add coverage reporting and tracking
8. Include async test support with pytest-asyncio

Target 90%+ code coverage with meaningful tests."
```
