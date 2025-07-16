# Coding Guidelines for AI Portfolio Optimization Project

## Code Style and Standards

### Python Style
- **Formatting**: Use Black with 88-character line length
- **Imports**: Use isort with Black profile for consistent import ordering
- **Linting**: Follow flake8 rules with project-specific ignores
- **Type Hints**: Required for all public APIs and recommended for internal functions

### Documentation Standards
```python
def process_document(self, pdf_path: Path) -> Tuple[str, Dict[str, Any]]:
    """
    Process a PDF document with mathematical formula extraction.
    
    Args:
        pdf_path: Path to the PDF file to process
        
    Returns:
        Tuple of (extracted_text, document_metadata)
        
    Raises:
        PDFProcessingError: If the PDF cannot be processed
        MathDetectionError: If mathematical formula detection fails
    """
```

### Error Handling Patterns
```python
# Use specific exception types
class PortfolioOptimizationError(Exception):
    """Base exception for portfolio optimization errors."""
    pass

class InsufficientDataError(PortfolioOptimizationError):
    """Raised when insufficient data for optimization."""
    pass

# Implement proper error context
try:
    result = risky_operation()
except ExternalAPIError as e:
    logger.error(f"API call failed: {e}", extra={"operation": "embed_documents"})
    raise ProcessingError(f"Failed to process documents: {e}") from e
```

### Configuration Patterns
```python
# Use Pydantic for configuration validation
class OptimizerSettings(BaseSettings):
    risk_tolerance: float = Field(ge=0.0, le=1.0, description="Risk tolerance level")
    rebalance_frequency: str = Field(regex="^(daily|weekly|monthly|quarterly)$")
    
    class Config:
        env_prefix = "PORTFOLIO_OPTIMIZER_"
```

### Logging Standards
```python
# Use structured logging with context
logger.info(
    "Document processed successfully",
    extra={
        "document_id": doc_id,
        "processing_time": elapsed_time,
        "math_blocks_found": len(math_blocks)
    }
)
```

## Architecture Patterns

### Dependency Injection
```python
# Use protocol/interface definitions
class VectorStoreProtocol(Protocol):
    def store_embeddings(self, vectors: List[Vector]) -> None: ...
    def search_similar(self, query: Vector, k: int) -> List[SearchResult]: ...

# Inject dependencies through constructors
class DocumentProcessor:
    def __init__(self, vector_store: VectorStoreProtocol, embedder: EmbedderProtocol):
        self.vector_store = vector_store
        self.embedder = embedder
```

### Factory Patterns
```python
def create_optimizer(config: Settings) -> PortfolioOptimizer:
    """Factory function for creating configured optimizer instances."""
    if config.optimization_method == "mean_variance":
        return MeanVarianceOptimizer(config)
    elif config.optimization_method == "black_litterman":
        return BlackLittermanOptimizer(config)
    else:
        raise ValueError(f"Unknown optimization method: {config.optimization_method}")
```

### Async Patterns
```python
# Use async for I/O bound operations
async def process_documents_async(self, documents: List[Path]) -> List[ProcessingResult]:
    """Process multiple documents concurrently."""
    tasks = [self._process_single_document(doc) for doc in documents]
    return await asyncio.gather(*tasks, return_exceptions=True)
```

## Testing Guidelines

### Test Structure
```python
class TestPortfolioOptimizer:
    """Test portfolio optimization functionality."""
    
    @pytest.fixture
    def sample_returns_data(self):
        """Sample return data for testing."""
        return pd.DataFrame({
            'AAPL': [0.01, 0.02, -0.01],
            'GOOGL': [0.015, -0.005, 0.02],
            'MSFT': [0.008, 0.012, 0.005]
        })
    
    def test_mean_variance_optimization(self, sample_returns_data):
        """Test mean-variance optimization with sample data."""
        optimizer = MeanVarianceOptimizer()
        weights = optimizer.optimize(sample_returns_data)
        
        assert abs(sum(weights) - 1.0) < 1e-6  # Weights sum to 1
        assert all(w >= 0 for w in weights)    # Long-only constraint
```

### Mock Patterns
```python
@patch('src.external.openai_client.OpenAI')
def test_embedding_generation_with_api_failure(self, mock_openai):
    """Test graceful handling of API failures."""
    mock_openai.return_value.embeddings.create.side_effect = APIError("Rate limit")
    
    embedder = DocumentEmbedder(config)
    with pytest.raises(EmbeddingError):
        embedder.generate_embeddings(["test text"])
```

## File Organization

### Module Structure
```
src/
├── optimizer/           # Portfolio optimization logic
│   ├── __init__.py
│   ├── base.py         # Abstract base classes
│   ├── mean_variance.py
│   ├── black_litterman.py
│   └── risk_models.py
├── knowledge/          # Knowledge management
│   ├── __init__.py
│   ├── search.py       # Semantic search
│   ├── insights.py     # Insight extraction
│   └── graph.py        # Knowledge graph
└── frontend/           # Web interface
    ├── __init__.py
    ├── api/            # FastAPI routes
    ├── static/         # Static assets
    └── templates/      # Jinja2 templates
```

### Import Conventions
```python
# Standard library imports first
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional

# Third-party imports second
import numpy as np
import pandas as pd
from pydantic import BaseModel

# Local imports last
from src.settings import Settings
from src.optimizer.base import BaseOptimizer
```
