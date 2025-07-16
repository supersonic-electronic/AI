# External Knowledge Base Integration

This document describes the external knowledge base integration system that enriches extracted concepts with information from external ontologies like DBpedia and Wikidata.

## Overview

The external knowledge base integration system automatically enriches concepts extracted from documents with additional information from external sources. This provides:

- Enhanced concept descriptions
- Additional aliases and synonyms
- Semantic relationships and properties
- External identifiers and links
- Improved confidence scores

## Architecture

The system consists of four main components:

1. **External Ontology Connectors** (`src/knowledge/external_ontologies.py`)
2. **Concept Caching Layer** (`src/knowledge/concept_cache.py`)
3. **Extended Ontology Framework** (`src/knowledge/ontology.py`)
4. **Enhanced Concept Extractor** (`src/knowledge/concept_extractor.py`)

## Configuration

### Enabling External Ontologies

External ontology integration is controlled by settings in `config.yaml`:

```yaml
# External Ontology Integration
enable_external_ontologies: true      # Master switch for external enrichment
enable_dbpedia: true                   # Enable DBpedia integration
enable_wikidata: true                  # Enable Wikidata integration
external_ontology_timeout: 10.0       # Timeout for external API calls (seconds)
external_ontology_max_retries: 3      # Maximum retry attempts
external_ontology_retry_delay: 1.0    # Delay between retries (seconds)

# Concept Caching Configuration
cache_dir: "./data/cache"              # Directory for cache storage
max_cache_size: 10000                  # Maximum cached concepts
cache_ttl_hours: 168                   # Cache TTL (1 week default)
enable_cache_cleanup: true             # Enable automatic cleanup
```

### Environment Variables

You can also configure via environment variables:

```bash
export PORTFOLIO_OPTIMIZER_ENABLE_EXTERNAL_ONTOLOGIES=true
export PORTFOLIO_OPTIMIZER_ENABLE_DBPEDIA=true
export PORTFOLIO_OPTIMIZER_ENABLE_WIKIDATA=true
export PORTFOLIO_OPTIMIZER_EXTERNAL_ONTOLOGY_TIMEOUT=15.0
```

## Usage

### Basic Usage

The external enrichment happens automatically during concept extraction:

```python
from src.knowledge.concept_extractor import get_concept_extractor
from src.settings import get_settings

# Load settings and create extractor
settings = get_settings()
extractor = get_concept_extractor(settings)

# Extract and enrich concepts from text
concepts, relationships = extractor.extract_concepts_from_text(
    "The Sharpe ratio measures risk-adjusted return.",
    document_name="example.pdf",
    page_number=1
)

# Concepts are automatically enriched with external data
```

### Manual Enrichment

You can also manually enrich concepts:

```python
from src.knowledge.ontology import FinancialMathOntology, Concept, ConceptType

# Create ontology with external integration
ontology = FinancialMathOntology(settings)

# Create a concept
concept = Concept(
    id="sharpe_ratio",
    name="Sharpe Ratio",
    concept_type=ConceptType.METRIC,
    description="A measure of risk-adjusted return"
)

# Enrich with external ontologies
enriched_concept = ontology.enrich_concept_with_external_ontologies(concept)

# Check the enriched properties
print(enriched_concept.description)  # Enhanced description
print(enriched_concept.aliases)      # Additional aliases
print(enriched_concept.properties)   # External properties
```

### Searching External Ontologies

You can search external ontologies directly:

```python
# Search all external ontologies
results = ontology.search_external_ontologies("portfolio optimization")

# Results contain data from each ontology
for source, concepts in results.items():
    print(f"Results from {source}:")
    for concept in concepts:
        print(f"  - {concept.label}: {concept.description}")
```

## External Ontology Connectors

### DBpedia Connector

The DBpedia connector integrates with the DBpedia knowledge base:

**Features:**
- DBpedia Lookup API for concept search
- SPARQL queries for detailed concept information
- Automatic concept type mapping
- Related concept discovery

**Example Usage:**
```python
from src.knowledge.external_ontologies import DBpediaConnector
from src.knowledge.concept_cache import get_concept_cache

cache = get_concept_cache(settings)
connector = DBpediaConnector(settings, cache)

# Search for concepts
results = connector.search_concept("portfolio theory")
for result in results:
    print(f"Found: {result.label} - {result.description}")
```

### Wikidata Connector

The Wikidata connector integrates with Wikidata:

**Features:**
- Wikidata API search
- SPARQL queries for structured data
- Entity relationship discovery
- Multilingual support (English focus)

**Example Usage:**
```python
from src.knowledge.external_ontologies import WikidataConnector

connector = WikidataConnector(settings, cache)

# Search for concepts
results = connector.search_concept("modern portfolio theory")
for result in results:
    print(f"Wikidata ID: {result.external_id}")
    print(f"Label: {result.label}")
    print(f"Description: {result.description}")
```

### Adding New Connectors

To add a new external ontology connector:

1. **Create Connector Class:**
```python
from src.knowledge.external_ontologies import ExternalOntologyConnector

class MyOntologyConnector(ExternalOntologyConnector):
    def search_concept(self, concept_name, concept_type=None):
        # Implement search logic
        pass
    
    def get_concept_details(self, external_id):
        # Implement detail retrieval
        pass
    
    def get_related_concepts(self, external_id):
        # Implement relationship discovery
        pass
```

2. **Register in Manager:**
```python
# In ExternalOntologyManager.__init__
if getattr(settings, 'enable_my_ontology', False):
    self.connectors['my_ontology'] = MyOntologyConnector(settings, cache)
```

3. **Add Configuration:**
```yaml
# In config.yaml
enable_my_ontology: true
```

## Caching System

### Cache Architecture

The caching system uses SQLite for persistent storage:

**Features:**
- **Persistent Storage**: Survives application restarts
- **TTL Support**: Automatic expiration of old entries
- **LRU Eviction**: Removes least recently used entries
- **Statistics**: Comprehensive cache performance metrics
- **Source Tracking**: Tracks which ontology provided each cached entry

### Cache Configuration

```yaml
cache_dir: "./data/cache"              # Cache directory
max_cache_size: 10000                  # Maximum entries
cache_ttl_hours: 168                   # Time to live (hours)
enable_cache_cleanup: true             # Automatic cleanup
```

### Cache Management

```python
# Get cache statistics
stats = ontology.get_external_ontology_stats()
print(f"Cache hit rate: {stats['hit_rate']:.2%}")
print(f"Total entries: {stats['total_entries']}")
print(f"Cache size: {stats['total_size_bytes']} bytes")

# Clean up expired entries
ontology.cleanup_external_cache()

# Clear cache for specific source
ontology.cleanup_external_cache(source="dbpedia")
```

## Performance Considerations

### Optimization Strategies

1. **Caching**: All external API calls are cached to reduce latency
2. **Timeouts**: Configurable timeouts prevent hanging requests
3. **Retries**: Automatic retry logic with exponential backoff
4. **Batch Processing**: Efficient processing of multiple concepts
5. **Lazy Loading**: External enrichment only when needed

### Monitoring

Monitor performance using built-in statistics:

```python
# Get performance stats
stats = extractor.get_external_ontology_stats()

# Monitor cache efficiency
if stats['hit_rate'] < 0.5:
    print("Consider increasing cache size or TTL")

# Monitor API usage
if stats['total_requests'] > 1000:
    print("High API usage - check caching configuration")
```

## Error Handling

The system includes comprehensive error handling:

### Common Error Scenarios

1. **Network Timeouts**: Graceful fallback to cached data
2. **API Rate Limits**: Automatic retry with backoff
3. **Invalid Responses**: Robust parsing with fallback
4. **Cache Corruption**: Automatic cache rebuild
5. **Configuration Errors**: Clear error messages

### Error Recovery

```python
try:
    enriched_concept = ontology.enrich_concept_with_external_ontologies(concept)
except Exception as e:
    logger.error(f"External enrichment failed: {e}")
    # Fallback to original concept
    enriched_concept = concept
```

## Integration with Concept Extraction

### Automatic Enrichment

The concept extractor automatically enriches concepts during processing:

```python
# Enable enrichment during extraction
concepts, relationships = extractor.process_document(
    document_text="Your text here",
    document_name="document.pdf",
    enable_external_enrichment=True  # Default: True
)
```

### Enrichment Pipeline

The enrichment pipeline follows these steps:

1. **Concept Extraction**: Extract concepts from text
2. **Cache Lookup**: Check for cached external data
3. **External Search**: Query external ontologies if not cached
4. **Data Enrichment**: Apply external data to concepts
5. **Cache Storage**: Store results for future use
6. **Ontology Integration**: Add enriched concepts to ontology

### Custom Enrichment

You can customize the enrichment process:

```python
# Extract concepts without enrichment
concepts = extractor.extract_concepts_from_text(text)

# Apply custom enrichment
enriched_concepts = []
for concept in concepts:
    # Custom enrichment logic
    if concept.concept_type == ConceptType.METRIC:
        enriched = ontology.enrich_concept_with_external_ontologies(concept)
        enriched_concepts.append(enriched)
    else:
        enriched_concepts.append(concept)
```

## Troubleshooting

### Common Issues

1. **No External Data**: Check network connectivity and API endpoints
2. **Cache Corruption**: Delete cache directory and restart
3. **High Memory Usage**: Reduce cache size or enable cleanup
4. **Slow Performance**: Increase timeout values or check network
5. **Missing Dependencies**: Install requests and SPARQLWrapper

### Debug Mode

Enable debug logging for detailed information:

```python
import logging
logging.getLogger('src.knowledge.external_ontologies').setLevel(logging.DEBUG)
logging.getLogger('src.knowledge.concept_cache').setLevel(logging.DEBUG)
```

### Health Check

```python
# Check external ontology health
results = ontology.search_external_ontologies("test")
if not results:
    print("External ontologies not responding")
else:
    print(f"External ontologies working: {list(results.keys())}")
```

## API Reference

### ExternalOntologyConnector (Abstract Base Class)

```python
class ExternalOntologyConnector(ABC):
    def search_concept(self, concept_name: str, concept_type: Optional[ConceptType] = None) -> List[ExternalConceptData]
    def get_concept_details(self, external_id: str) -> Optional[ExternalConceptData]
    def get_related_concepts(self, external_id: str) -> List[ExternalConceptData]
    def enrich_concept(self, concept: Concept) -> Concept
```

### FinancialMathOntology Extended Methods

```python
def enrich_concept_with_external_ontologies(self, concept: Concept) -> Concept
def search_external_ontologies(self, concept_name: str, concept_type: Optional[ConceptType] = None) -> Dict[str, Any]
def add_concept_with_enrichment(self, concept: Concept, enable_enrichment: bool = True) -> None
def get_external_ontology_stats(self) -> Dict[str, Any]
def cleanup_external_cache(self, source: Optional[str] = None) -> None
```

### ConceptCache

```python
class ConceptCache:
    def get(self, key: str) -> Optional[Any]
    def set(self, key: str, value: Any, ttl_hours: Optional[int] = None, source: Optional[str] = None) -> None
    def delete(self, key: str) -> bool
    def clear(self, source: Optional[str] = None) -> None
    def cleanup_expired(self) -> None
    def get_stats(self) -> Dict[str, Any]
```

## Examples

### Complete Integration Example

```python
from src.settings import get_settings
from src.knowledge.concept_extractor import get_concept_extractor

def process_document_with_enrichment():
    # Load configuration
    settings = get_settings()
    
    # Create extractor with external enrichment
    extractor = get_concept_extractor(settings)
    
    # Process document
    with open("document.txt", "r") as f:
        text = f.read()
    
    concepts, relationships = extractor.process_document(
        text, 
        "document.pdf",
        enable_external_enrichment=True
    )
    
    # Display enriched concepts
    for concept in concepts:
        print(f"Concept: {concept.name}")
        print(f"Type: {concept.concept_type}")
        print(f"Description: {concept.description}")
        
        # Show external enrichment
        if 'external_source' in concept.properties:
            print(f"External Source: {concept.properties['external_source']}")
            print(f"External ID: {concept.properties['external_id']}")
        
        print("-" * 50)
    
    # Show cache statistics
    stats = extractor.get_external_ontology_stats()
    print(f"Cache hit rate: {stats['hit_rate']:.2%}")
    print(f"Total cache entries: {stats['total_entries']}")

if __name__ == "__main__":
    process_document_with_enrichment()
```

### Custom Connector Example

```python
from src.knowledge.external_ontologies import ExternalOntologyConnector, ExternalConceptData

class CustomFinanceOntology(ExternalOntologyConnector):
    def __init__(self, settings, cache):
        super().__init__(settings, cache)
        self.api_endpoint = "https://api.finance-ontology.com"
    
    def search_concept(self, concept_name, concept_type=None):
        # Custom search implementation
        response = self.session.get(
            f"{self.api_endpoint}/search",
            params={"query": concept_name, "type": concept_type}
        )
        
        results = []
        for item in response.json():
            result = ExternalConceptData(
                external_id=item["id"],
                source="finance_ontology",
                label=item["label"],
                description=item["description"],
                confidence=item.get("confidence", 0.7)
            )
            results.append(result)
        
        return results
    
    def get_concept_details(self, external_id):
        # Implementation for detailed concept information
        pass
    
    def get_related_concepts(self, external_id):
        # Implementation for related concepts
        pass
```

## Best Practices

1. **Configuration**: Use environment variables for sensitive settings
2. **Caching**: Monitor cache hit rates and adjust TTL as needed
3. **Error Handling**: Always handle external API failures gracefully
4. **Performance**: Use batch processing for large document sets
5. **Monitoring**: Track external API usage and costs
6. **Testing**: Test with external APIs disabled for unit tests
7. **Documentation**: Document custom connectors thoroughly

## Future Enhancements

Potential future improvements:

1. **Additional Ontologies**: Integration with domain-specific ontologies
2. **Machine Learning**: Use ML to improve concept matching
3. **Semantic Reasoning**: Advanced reasoning over external data
4. **Federated Search**: Parallel querying of multiple ontologies
5. **Quality Scoring**: Automatic quality assessment of external data
6. **Conflict Resolution**: Handle conflicting information from sources