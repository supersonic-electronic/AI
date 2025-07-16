# Requirements Specification: Enrichment Consistency Fix

## Problem Statement
The knowledge graph system exhibits inconsistent enrichment behavior where some nodes receive external enrichment (DBpedia/Wikidata badges and metadata) while similar concepts do not. This inconsistency persists even after cache clearing and system restarts, indicating systematic issues in the enrichment pipeline.

## Solution Overview
Implement a unified concept normalization system with cache validation and repair mechanisms to ensure consistent enrichment across all nodes that should legitimately have external data.

## Functional Requirements

### FR1: Unified Concept Normalization
- **Requirement**: All systems (cache, extraction, enrichment) must use the same concept normalization function
- **Behavior**: Concept names are consistently normalized to lowercase, trimmed, and standardized
- **Files**: `src/knowledge/external_ontologies.py:106`, `src/knowledge/concept_extractor.py:410`

### FR2: Normalized Cache Keys
- **Requirement**: Cache keys must use normalized concept names to prevent duplicate entries
- **Behavior**: "CAPM", "capm", and "Capm" share the same cache entry
- **Files**: `src/knowledge/external_ontologies.py:106`, `src/knowledge/concept_cache.py`

### FR3: Cache Validation and Repair
- **Requirement**: System must detect and fix inconsistent enrichment data automatically
- **Behavior**: Cache validation runs on startup and during normal operations
- **Files**: `src/knowledge/concept_cache.py`, new validation module

### FR4: Enhanced Enrichment Logging
- **Requirement**: Detailed logging of enrichment failures and decisions
- **Behavior**: Track when/why concepts fail to get enriched with specific error details
- **Files**: `src/knowledge/external_ontologies.py`, logging configuration

### FR5: Consistent Relationship Matching
- **Requirement**: Relationship lookup must use same normalization as enrichment system
- **Files**: `src/knowledge/concept_extractor.py:444,452-453`

## Technical Requirements

### TR1: Normalization Function Implementation
- **Location**: `src/knowledge/utils.py` (new utility module)
- **Function**: `normalize_concept_name(name: str) -> str`
- **Logic**: Lowercase, strip whitespace, handle special characters
- **Usage**: Import and use across all concept-handling modules

### TR2: Cache Key Strategy Update
- **Location**: `src/knowledge/external_ontologies.py:106`
- **Change**: Replace `concept.name` with `normalize_concept_name(concept.name)`
- **Backward Compatibility**: Implement cache migration for existing entries

### TR3: Cache Validation Module
- **Location**: `src/knowledge/cache_validation.py` (new module)
- **Functions**: 
  - `validate_cache_consistency()`
  - `repair_inconsistent_entries()`
  - `find_orphaned_variants()`

### TR4: Enhanced Logging Configuration
- **Location**: `src/knowledge/external_ontologies.py`
- **Add**: Structured logging for enrichment decisions
- **Include**: Concept name, match scores, threshold checks, failure reasons

### TR5: Concept Extractor Normalization
- **Location**: `src/knowledge/concept_extractor.py:410,444,452-453`
- **Change**: Use shared normalization function instead of inline `.lower().strip()`

## Implementation Hints and Patterns

### Pattern 1: Utility Function Pattern
Follow existing patterns in the codebase for shared utilities:
```python
# Similar to how Settings class is used across modules
from src.knowledge.utils import normalize_concept_name
```

### Pattern 2: Cache Management Pattern
Follow existing cache patterns in `src/knowledge/concept_cache.py`:
- Use similar error handling and logging
- Maintain existing TTL and size limits
- Follow existing serialization patterns

### Pattern 3: Logging Pattern
Follow existing logging patterns in the codebase:
- Use module-level loggers
- Include structured data in log messages
- Follow existing log level conventions

## Acceptance Criteria

### AC1: Normalization Consistency
- [ ] All concept names are normalized using the same function across all modules
- [ ] Cache keys are generated using normalized names
- [ ] Relationship matching uses normalized names

### AC2: Cache Behavior
- [ ] Similar concept variants (CAPM/capm/Capm) share the same cache entry
- [ ] Cache validation detects and reports inconsistencies
- [ ] Cache repair fixes orphaned entries automatically

### AC3: Enrichment Reliability
- [ ] Concepts that previously had inconsistent enrichment now consistently get enriched
- [ ] System behavior is deterministic after cache clearing
- [ ] Similar concept names get consistent enrichment results

### AC4: Logging and Monitoring
- [ ] Enrichment failures are logged with detailed information
- [ ] Cache validation results are logged
- [ ] Debug information is available for troubleshooting

### AC5: No Regression
- [ ] Existing enriched concepts continue to work correctly
- [ ] Performance is not significantly impacted
- [ ] All tests continue to pass

## Assumptions
- Existing cache data can be migrated to new normalized keys
- External API responses remain stable during normalization changes
- Current enrichment thresholds (0.12) remain appropriate
- Financial acronym mappings in the system are comprehensive

## Test Plan

### Unit Tests
1. **Normalization Function Tests** (`tests/test_normalization.py`)
   - Test edge cases: special characters, whitespace, unicode
   - Test consistency across different input formats
   - Test performance with large concept sets

2. **Cache Key Tests** (`tests/test_cache_consistency.py`)
   - Test normalized cache key generation
   - Test cache retrieval with different input casings
   - Test cache migration logic

3. **Cache Validation Tests** (`tests/test_cache_validation.py`)
   - Test inconsistency detection
   - Test repair mechanisms
   - Test validation performance

### Integration Tests
1. **End-to-End Enrichment Tests** (`tests/test_enrichment_e2e.py`)
   - Test enrichment consistency for concept variants
   - Test enrichment after cache clearing
   - Test enrichment in batch vs individual processing

2. **API Integration Tests** (`tests/test_api_enrichment.py`)
   - Test enrichment through API endpoints
   - Test frontend enrichment display consistency
   - Test search result consistency

### Manual Testing
1. **Known Problem Cases**
   - Test Markowitz, Black-Scholes, Beta, Alpha concepts
   - Test CAPM vs capm vs Capm variants
   - Test concepts with special characters

2. **Regression Testing**
   - Verify all previously working enrichment still works
   - Check performance impact on large concept sets
   - Validate frontend display consistency

## Documentation Updates

### Code Documentation
- Add docstrings to new normalization functions
- Update existing function docstrings that change behavior
- Add inline comments explaining normalization logic

### API Documentation
- Update API endpoint documentation if behavior changes
- Document new logging and monitoring capabilities

### System Documentation
- Update architecture documentation with normalization flow
- Document cache validation and repair processes
- Update troubleshooting guides with new logging information

## Git & Github Commit Instructions

### Commit Structure
1. **First Commit**: Add normalization utility function
   ```
   feat: Add unified concept normalization utility
   
   - Implement normalize_concept_name() function
   - Add comprehensive test coverage
   - Prepare foundation for cache consistency fixes
   ```

2. **Second Commit**: Update cache key generation
   ```
   fix: Use normalized concept names for cache keys
   
   - Update external ontology cache key generation
   - Implement cache migration for existing entries
   - Ensure backward compatibility
   ```

3. **Third Commit**: Add cache validation and repair
   ```
   feat: Add cache validation and repair mechanisms
   
   - Implement cache consistency validation
   - Add automatic repair for orphaned entries
   - Include validation in startup process
   ```

4. **Fourth Commit**: Enhance logging and monitoring
   ```
   feat: Add detailed enrichment logging and debugging
   
   - Log enrichment decisions and failures
   - Add structured logging for troubleshooting
   - Include cache validation logging
   ```

5. **Final Commit**: Update concept extraction normalization
   ```
   fix: Ensure consistent normalization in concept extraction
   
   - Use shared normalization function
   - Fix relationship matching consistency
   - Complete enrichment consistency implementation
   ```

### Branch Strategy
- Create feature branch: `fix/enrichment-consistency`
- Use conventional commits format
- Include tests in each commit
- Ensure each commit is atomic and testable

### Pull Request
- Title: "Fix enrichment consistency across all nodes"
- Include before/after examples showing the fix
- Document performance impact
- Include manual testing results