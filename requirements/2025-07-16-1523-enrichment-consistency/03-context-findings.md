# Context Findings - Phase 3

## Root Cause Analysis

The enrichment inconsistency issues stem from several interconnected problems in the enrichment pipeline:

### **1. Cache Key Normalization Mismatch**
- **File**: `src/knowledge/external_ontologies.py:106`
- **Issue**: Cache key uses raw concept name without normalization
- **Problem**: Different casings create separate cache entries (CAPM vs capm vs Capm)

### **2. Deduplication Logic Uses Different Normalization**
- **File**: `src/knowledge/concept_extractor.py:410`
- **Issue**: Concept extraction normalizes to lowercase, but cache doesn't
- **Problem**: Mismatch between extraction and enrichment systems

### **3. Relationship Lookup Inconsistency**
- **File**: `src/knowledge/concept_extractor.py:444,452-453`
- **Issue**: Relationship extraction normalizes all lookups to lowercase
- **Problem**: Cache and concept storage may use different casings

### **4. Financial Acronym Expansion Case Sensitivity**
- **File**: `src/knowledge/external_ontologies.py:683`
- **Issue**: Acronym expansion is case-sensitive in lookup
- **Problem**: Cache key uses original case, creating inconsistencies

### **5. Missing Cache Invalidation for Similar Concepts**
- **Issue**: No mechanism to invalidate related concept variants
- **Problem**: Clearing "CAPM" cache doesn't affect "capm" cache

### **6. DBpedia Search Term Expansion Logic**
- **File**: `src/knowledge/external_ontologies.py:679-696`
- **Issue**: Multiple search terms cached separately
- **Problem**: Different results for same conceptual entity

## Technical Constraints
1. **Rate Limiting**: 500ms delays may cause timing inconsistencies
2. **Cache TTL**: 7-day TTL preserves inconsistent data
3. **External API Variability**: DBpedia results may vary between requests
4. **Concurrent Access**: No locking for cache updates

## Files Requiring Modification
1. `src/knowledge/external_ontologies.py` - Cache key normalization, match scoring
2. `src/knowledge/concept_extractor.py` - Consistent normalization
3. `src/knowledge/concept_cache.py` - Cache validation and repair
4. `config.yaml` - Cache TTL and consistency settings

## Similar Patterns in Codebase
- Text normalization in document processing uses consistent lowercasing
- Search functionality has case-insensitive matching
- API endpoints use standardized response formatting

## Integration Points
- FastAPI endpoints that trigger enrichment
- Batch processing workflows
- Graph database population
- Frontend visualization data preparation