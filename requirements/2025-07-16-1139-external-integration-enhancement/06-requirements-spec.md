# Requirements Specification: External Integration Enhancement

**Project:** AI Knowledge Graph System  
**Feature:** Enhanced External Integration with Domain-Aware Enrichment  
**Date:** 2025-07-16  
**Version:** 1.0

## Problem Statement

The current external knowledge integration system has several critical limitations:

1. **Poor Domain Alignment**: External concept matching prioritizes generic matches over financial/mathematical domain concepts
2. **Incomplete Metadata Enrichment**: Available external metadata fields are not displayed in tooltips
3. **Missing Relationship Enrichment**: No integration of external relationship data to improve accuracy
4. **Cache Serialization Issues**: External enrichment fails due to object serialization problems
5. **Limited Related Concept Discovery**: SPARQL capabilities for related concepts are underutilized

## Solution Overview

Enhance the existing external ontology integration system to provide domain-aware concept enrichment, comprehensive metadata display, relationship accuracy improvements, and seamless integration of external knowledge into local concepts.

## Functional Requirements

### FR1: Domain-Aware Concept Matching
- **Description**: Prioritize financial/mathematical domain matches over generic concepts
- **Implementation**: Enhance `_calculate_match_score()` in `src/knowledge/external_ontologies.py` (lines 120-146)
- **Criteria**: Financial keywords boost scores by +0.5, category analysis adds +0.3
- **Example**: "Portfolio (finance)" ranks higher than "Atari Portfolio"

### FR2: Unified Concept Integration
- **Description**: Merge external data into local concepts rather than creating separate nodes
- **Implementation**: Enhance `_apply_enrichment()` method to prioritize local data and fill gaps with external data
- **Priority Order**: Local description > External description, Local aliases + External aliases
- **Visual**: Single nodes with enriched metadata, no visual distinction needed

### FR3: Comprehensive Tooltip Metadata
- **Description**: Display all available external metadata in tooltips
- **Implementation**: Extend tooltip rendering in `src/frontend/static/js/main.js` (lines 313-452)
- **New Fields**: 
  - DBpedia categories and properties
  - External related concepts
  - Usage examples and applications
  - Alternative names from external sources
- **Styling**: Add missing CSS classes for source badges

### FR4: Relationship Enrichment
- **Description**: Integrate external relationship evidence into local relationship scoring
- **Implementation**: 
  - Extend relationship scoring system in `src/knowledge/relationship_mapper.py` (lines 496-521)
  - Add 6th scoring component: "External Evidence" (10% weight)
  - Query external ontologies for relationship confirmation
- **Criteria**: External relationships boost confidence by up to 0.2 points

### FR5: Related Concept Discovery
- **Description**: Automatically discover and integrate related external concepts
- **Implementation**: Enhance `ExternalOntologyManager.enrich_concept()` to pull related concepts via SPARQL
- **Integration**: Add related concepts as enhanced metadata rather than separate nodes
- **Limits**: Maximum 5 related concepts per local concept to prevent overwhelm

## Technical Requirements

### TR1: Cache System Fix
- **File**: `src/knowledge/concept_cache.py`
- **Issue**: Fix ExternalConceptData serialization/deserialization
- **Solution**: Implement proper JSON serialization with dataclass support
- **Validation**: Add type checking in cache retrieval methods

### TR2: API Enhancement
- **Files**: 
  - `src/frontend/api/graph.py` (lines 146-206)
  - `src/frontend/api/dbpedia.py`
- **Changes**: 
  - Fix concept type mapping (line 153-158)
  - Add related concept fields to API responses
  - Enhance error handling for external API failures

### TR3: Frontend Integration
- **Files**:
  - `src/frontend/static/js/main.js` (lines 313-452)
  - `src/frontend/static/css/main.css` (lines 897-1085)
- **Changes**:
  - Add missing CSS classes: `.tooltip-source-badge`, `.dbpedia-badge`, `.enriched-badge`, `.local-badge`
  - Implement metadata field rendering for new fields
  - Add related concepts section to tooltips

### TR4: SPARQL Enhancement
- **File**: `src/knowledge/external_ontologies.py` (lines 188-340)
- **Enhancement**: Implement relationship discovery queries
- **Example Queries**:
  ```sparql
  SELECT ?related ?property WHERE {
    <http://dbpedia.org/resource/Portfolio_(finance)> ?property ?related .
    ?related rdf:type dbo:FinancialConcept .
  }
  ```

## Implementation Hints and Patterns

### Pattern 1: Concept Enrichment Enhancement
```python
# In src/knowledge/external_ontologies.py
def _apply_enrichment(self, concept: Concept, external_data: ExternalConceptData) -> Concept:
    # Prioritize local data, fill gaps with external
    if not concept.description and external_data.description:
        concept.description = external_data.description
    
    # Merge aliases (local + external)
    concept.aliases.update(external_data.aliases)
    
    # Add related concepts as metadata
    if external_data.related_concepts:
        concept.properties['related_external_concepts'] = external_data.related_concepts[:5]
```

### Pattern 2: Tooltip Metadata Enhancement
```javascript
// In src/frontend/static/js/main.js
function renderTooltipMetadata(nodeData) {
    // Add external categories section
    if (nodeData.categories && nodeData.categories.length > 0) {
        sections.push(createMetadataSection('Categories', nodeData.categories));
    }
    
    // Add related concepts section
    if (nodeData.related_external_concepts) {
        sections.push(createRelatedConceptsSection(nodeData.related_external_concepts));
    }
}
```

### Pattern 3: Relationship Scoring Enhancement
```python
# In src/knowledge/relationship_mapper.py
def _calculate_external_score(self, rel: Relationship, external_evidence: Dict) -> float:
    """Calculate external evidence score component"""
    if external_evidence.get('confirmed_by_dbpedia', False):
        return 0.8
    elif external_evidence.get('related_in_wikidata', False):
        return 0.6
    return 0.0
```

## Acceptance Criteria

### AC1: Domain Filtering
- [ ] Financial concepts rank higher than generic concepts in external matches
- [ ] "Portfolio (finance)" preferred over "Atari Portfolio" in test cases
- [ ] Category-based filtering rejects clearly unrelated concepts

### AC2: Unified Integration
- [ ] External metadata fills gaps in local concept data
- [ ] Local data takes precedence when both sources have same field
- [ ] No separate external nodes created in graph visualization

### AC3: Enhanced Tooltips
- [ ] All missing metadata fields display in tooltips
- [ ] DBpedia categories and properties render correctly
- [ ] Related external concepts show as clickable links
- [ ] Source badges display with proper CSS styling

### AC4: Relationship Accuracy
- [ ] External relationship evidence improves confidence scores
- [ ] Relationship mapper includes external evidence component
- [ ] Cross-validated relationships show higher confidence

### AC5: Related Concept Discovery
- [ ] SPARQL queries retrieve related concepts for each enriched concept
- [ ] Related concepts integrate as metadata rather than separate nodes
- [ ] Maximum 5 related concepts per concept maintained

### AC6: System Reliability
- [ ] Cache serialization issues resolved
- [ ] External enrichment works without "'str' object" errors
- [ ] Performance remains acceptable with enhanced functionality

## Assumptions

1. **Financial Domain Focus**: All filtering prioritizes finance/mathematics over general concepts
2. **Performance Tolerance**: Users accept slightly slower loading for enhanced metadata
3. **External API Availability**: DBpedia/Wikidata APIs remain accessible and responsive
4. **Graph Complexity**: Users can handle richer tooltips without UI overwhelm
5. **Cache Storage**: SQLite cache can handle enhanced object serialization

## Test Plan

### Unit Tests
- [ ] Test external concept domain filtering accuracy
- [ ] Test cache serialization/deserialization of ExternalConceptData
- [ ] Test relationship scoring with external evidence
- [ ] Test tooltip metadata rendering for all new fields

### Integration Tests
- [ ] Test complete enrichment pipeline from concept to visualization
- [ ] Test API responses include all enhanced metadata
- [ ] Test frontend renders enhanced tooltips correctly
- [ ] Test related concept discovery via SPARQL

### Performance Tests
- [ ] Test tooltip loading time with enhanced metadata
- [ ] Test cache performance with proper object serialization
- [ ] Test external API timeout handling and retry logic

### User Acceptance Tests
- [ ] Verify financial concepts show relevant external matches
- [ ] Verify tooltips display comprehensive external metadata
- [ ] Verify relationship accuracy improvements are noticeable
- [ ] Verify graph remains readable with enhanced data

## Documentation Updates

### Code Documentation
- [ ] Update docstrings in `external_ontologies.py` for new functionality
- [ ] Document new tooltip metadata fields in `main.js`
- [ ] Update API endpoint documentation for enhanced responses

### User Documentation
- [ ] Update `docs/external-knowledge-integration.md` with new features
- [ ] Document new tooltip fields and external integration
- [ ] Add examples of enhanced relationship discovery

### Configuration Documentation
- [ ] Document new external integration settings
- [ ] Update YAML configuration examples
- [ ] Document performance tuning parameters

## Git & GitHub Commit Instructions

### Commit Strategy
1. **Fix Cache Issues**: Separate commit for cache serialization fixes
2. **Domain Filtering**: Separate commit for enhanced concept matching
3. **Tooltip Enhancement**: Frontend changes for metadata display
4. **Relationship Integration**: Backend relationship scoring improvements
5. **Documentation**: Update all relevant documentation files

### Commit Messages
```
fix(cache): resolve ExternalConceptData serialization issues

feat(external): enhance domain-aware concept matching for finance

feat(ui): add comprehensive external metadata to tooltips  

feat(relationships): integrate external evidence in scoring system

docs: update external integration documentation
```

### Pull Request Structure
- Create feature branch: `feature/external-integration-enhancement`
- Separate PRs for major components to facilitate review
- Include comprehensive test coverage
- Update documentation in same PR as feature implementation

## Priority Implementation Order

1. **Critical**: Fix cache serialization issues (blocks other functionality)
2. **High**: Enhance domain filtering for accurate concept matching
3. **High**: Add missing tooltip metadata fields
4. **Medium**: Integrate relationship enrichment
5. **Medium**: Implement related concept discovery
6. **Low**: Performance optimizations and fine-tuning