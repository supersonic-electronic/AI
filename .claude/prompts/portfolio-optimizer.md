# Portfolio Optimization Module Prompts

## Create Portfolio Optimizer Base Classes

```
Create a comprehensive portfolio optimization module in src/optimizer/ that implements modern portfolio theory and advanced optimization techniques. The module should include:

1. **Base Classes and Interfaces**:
   - Abstract BaseOptimizer class with common interface
   - Portfolio class for representing portfolio allocations
   - RiskModel abstract class for different risk modeling approaches
   - PerformanceMetrics class for backtesting and evaluation

2. **Optimization Algorithms**:
   - MeanVarianceOptimizer: Classic Markowitz optimization
   - BlackLittermanOptimizer: Black-Litterman model with views
   - RiskParityOptimizer: Equal risk contribution approach
   - FactorBasedOptimizer: Multi-factor model optimization

3. **Risk Models**:
   - HistoricalRiskModel: Sample covariance estimation
   - ShrinkageRiskModel: Ledoit-Wolf shrinkage estimator
   - FactorRiskModel: Multi-factor risk decomposition

4. **Constraints and Objectives**:
   - Weight constraints (long-only, leverage, turnover)
   - Risk constraints (volatility, VaR, tracking error)
   - Multiple objective functions (Sharpe ratio, utility maximization)

5. **Integration Requirements**:
   - Use existing Settings class for configuration
   - Integrate with logging_config for structured logging
   - Support async operations for large-scale optimization
   - Include comprehensive error handling and validation
   - Add type hints throughout

6. **Data Integration**:
   - Interface with knowledge management system for research insights
   - Support for multiple data sources (market data, fundamental data)
   - Integration with document processing pipeline for research-driven views

Follow the existing code patterns in the project, use Pydantic for configuration validation, and include comprehensive docstrings with examples.
```

## Create Knowledge Management System

```
Implement a knowledge management system in src/knowledge/ that provides semantic search and insight extraction from processed research documents. The system should include:

1. **Core Components**:
   - SemanticSearchEngine: Query processed documents using vector similarity
   - InsightExtractor: Extract investment insights from research papers
   - KnowledgeGraph: Build relationships between financial concepts
   - ResearchSummarizer: Generate summaries of relevant research

2. **Search Capabilities**:
   - Semantic search over document chunks with mathematical content preservation
   - Multi-modal search (text + mathematical formulas)
   - Contextual search with portfolio optimization focus
   - Research paper recommendation based on current portfolio

3. **Insight Extraction**:
   - Extract quantitative insights (expected returns, risk estimates, correlations)
   - Identify investment themes and market trends
   - Extract factor exposures and risk characteristics
   - Generate Black-Litterman views from research consensus

4. **Knowledge Graph**:
   - Build graph of financial concepts, assets, and relationships
   - Track research paper citations and influence
   - Identify expert opinions and research quality metrics
   - Support graph-based queries and reasoning

5. **Integration Points**:
   - Use existing vector stores (Chroma/Pinecone) from chunk_embed.py
   - Integrate with portfolio optimizer for research-driven optimization
   - Support the existing mathematical content detection system
   - Use Settings class for configuration management

6. **API Design**:
   - Async interfaces for scalable search operations
   - Streaming results for large result sets
   - Caching for frequently accessed insights
   - Rate limiting and error handling for external APIs

Include comprehensive error handling, logging, and type hints. Design for extensibility and integration with the existing document processing pipeline.
```

## Create Web Frontend

```
Create a modern web frontend in src/frontend/ using FastAPI and React that provides an intuitive interface for portfolio optimization and research management. The frontend should include:

1. **Backend API (FastAPI)**:
   - RESTful API endpoints for all core functionality
   - WebSocket support for real-time updates during document processing
   - Authentication and session management
   - API documentation with OpenAPI/Swagger
   - Rate limiting and security middleware

2. **Frontend Components (React)**:
   - Dashboard with portfolio overview and performance metrics
   - Document upload and processing interface with progress tracking
   - Research search and exploration interface
   - Portfolio optimization configuration and results visualization
   - Mathematical formula rendering and editing

3. **Key Features**:
   - Interactive portfolio optimization with real-time constraint adjustment
   - Document processing pipeline monitoring with live status updates
   - Research paper search with semantic similarity and mathematical content
   - Portfolio backtesting with interactive charts and performance metrics
   - Configuration management for optimization parameters

4. **API Endpoints**:
   - /api/documents: Upload, process, and manage research documents
   - /api/search: Semantic search over processed documents
   - /api/optimize: Portfolio optimization with various algorithms
   - /api/backtest: Historical performance analysis
   - /api/insights: Extract and manage research insights

5. **Integration Requirements**:
   - Use existing CLI commands as backend services
   - Integrate with current Settings and logging systems
   - Support both Chroma and Pinecone vector stores
   - Maintain compatibility with existing document processing pipeline

6. **Technical Requirements**:
   - Responsive design for desktop and mobile
   - Real-time updates using WebSockets
   - Proper error handling and user feedback
   - Security best practices (CORS, input validation, authentication)
   - Performance optimization for large datasets

Include proper TypeScript types, comprehensive error handling, and follow modern React patterns with hooks and context.
```
