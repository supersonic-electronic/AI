# Enhanced Graph Database and Web App Metadata - Requirements Specification

**Project ID:** enhanced-graph-metadata  
**Date:** 2025-01-16  
**Status:** Enhancement to existing implementation

## Problem Statement and Solution Overview

### Current State
The knowledge graph system already has **comprehensive enhanced metadata functionality implemented**, including:
- Rich concept metadata schema with LaTeX math support
- Professional web visualization with MathJax rendering  
- Automated PDF document processing and concept extraction
- Search and filtering capabilities
- External links and source attribution

### Enhancement Requirements
Based on user feedback, four specific enhancements are needed to the existing robust implementation:

1. **Enhanced Automated Extraction** - Extract complexity levels and prerequisites from document context
2. **Expanded Symbol Detection** - Support additional mathematical notation systems  
3. **Advanced Search Filtering** - Filter by complexity, domain, and prerequisite relationships
4. **Interactive Graph Tooltips** - Display enhanced metadata directly on graph nodes

## Functional Requirements

### FR1: Enhanced Automated Metadata Extraction
**Priority:** High  
**File:** `src/knowledge/concept_extractor.py`

- **FR1.1** Extract complexity levels (beginner/intermediate/advanced) from document context
  - Identify educational indicators: "introduction to", "advanced", "requires knowledge of"
  - Analyze mathematical complexity: equation depth, symbol usage, derivation length
  - Default to "intermediate" for financial mathematics concepts

- **FR1.2** Extract prerequisite relationships from document text
  - Identify phrases: "assumes familiarity with", "requires understanding of", "builds on"
  - Map prerequisite concepts to existing ontology
  - Store as prerequisite lists in enhanced metadata

- **FR1.3** Extract domain classification from document structure
  - Analyze section headers, keywords, mathematical notation patterns
  - Classify as: mathematics, finance, economics, statistics, optimization
  - Default to "finance" for documents in financial mathematics corpus

### FR2: Expanded Mathematical Symbol Detection  
**Priority:** Medium  
**File:** `src/ingestion/math_detector.py`

- **FR2.1** Add support for advanced financial notation
  - Options pricing: Black-Scholes symbols (Δ, Γ, Θ, Ρ, Κ)
  - Portfolio theory: correlation matrices, covariance operators
  - Risk measures: VaR, CVaR, expected shortfall notation

- **FR2.2** Support multi-line equation environments
  - LaTeX environments: align, gather, split, cases
  - Matrix notations: pmatrix, bmatrix, vmatrix
  - System of equations detection

- **FR2.3** Enhanced LaTeX symbol mapping
  - Extend current 50+ symbol dictionary to 150+ symbols
  - Add financial-specific operators and functions
  - Support Unicode mathematical operators

### FR3: Advanced Search and Filtering
**Priority:** High  
**File:** `src/frontend/api/search.py`

- **FR3.1** Complexity level filtering
  - Add `/api/search/by-complexity/{level}` endpoint
  - Filter concepts by beginner/intermediate/advanced
  - Support multiple complexity levels in single query

- **FR3.2** Domain-based filtering  
  - Add `/api/search/by-domain/{domain}` endpoint
  - Filter by mathematics, finance, economics, etc.
  - Combine with existing type-based filtering

- **FR3.3** Prerequisite relationship filtering
  - Add `/api/search/prerequisites/{concept_id}` endpoint
  - Find concepts that require specific prerequisite knowledge
  - Support transitive prerequisite chains

- **FR3.4** Enhanced search suggestions
  - Include complexity level and domain in suggestions response
  - Rank suggestions by metadata richness
  - Support fuzzy matching on enhanced metadata fields

### FR4: Interactive Graph Node Tooltips
**Priority:** Medium  
**Files:** `src/frontend/static/js/main.js`, `src/frontend/static/css/main.css`

- **FR4.1** Hover tooltip implementation
  - Display tooltip on node hover with 300ms delay
  - Show: name, type, complexity level, domain
  - Include LaTeX preview for mathematical concepts

- **FR4.2** Tooltip content and styling
  - Professional tooltip design matching existing UI
  - MathJax rendering for LaTeX in tooltips
  - Responsive positioning to avoid viewport overflow

- **FR4.3** Performance optimization
  - Lazy-load tooltip content for large graphs
  - Cache tooltip data to avoid repeated API calls
  - Debounce hover events for smooth interaction

## Technical Requirements

### TR1: Database Schema Extensions
**File:** `src/knowledge/graph_db.py`
- No changes needed - enhanced metadata already supported
- Existing Neo4j schema accommodates all new metadata fields

### TR2: API Response Format Enhancements
**Files:** `src/frontend/api/concepts.py`, `src/frontend/api/search.py`  
- Extend existing search endpoints with new filter parameters
- Maintain backward compatibility with current API consumers
- Add pagination support for filtered results

### TR3: Frontend Performance Requirements
**Files:** `src/frontend/static/js/graph.js`, `src/frontend/static/js/main.js`
- Tooltip rendering must not impact graph performance (<16ms frame time)
- Support graphs with 1000+ nodes without performance degradation  
- Implement virtual scrolling for large search result sets

### TR4: Math Rendering Optimization
**File:** `src/frontend/templates/index.html`
- MathJax processing for tooltips must complete within 200ms
- Support concurrent LaTeX rendering for multiple tooltips
- Graceful fallback for complex expressions that fail to render

## Implementation Hints and Patterns

### Pattern 1: Enhanced Extraction (FR1)
```python
# Follow existing pattern in concept_extractor.py
class EnhancedMetadataExtractor:
    def extract_complexity_level(self, text: str, context: str) -> str:
        # Analyze educational indicators and mathematical complexity
        # Return: "beginner" | "intermediate" | "advanced"
        
    def extract_prerequisites(self, text: str, ontology: FinancialMathOntology) -> List[str]:
        # Identify prerequisite patterns and map to existing concepts
        # Return list of concept IDs that are prerequisites
```

### Pattern 2: Symbol Detection Extension (FR2)  
```python
# Extend existing math_detector.py symbol_to_latex dictionary
ENHANCED_SYMBOL_MAPPINGS = {
    # Financial notation
    'Δ': r'\Delta',  # Delta (options)
    'Γ': r'\Gamma',  # Gamma (options) 
    'Θ': r'\Theta',  # Theta (options)
    # Matrix environments
    '⎡': r'\begin{bmatrix}',
    '⎣': r'\begin{pmatrix}',
}
```

### Pattern 3: Search API Extension (FR3)
```python
# Follow existing search.py pattern, add new endpoints
@router.get("/search/by-complexity/{complexity_level}")
async def search_by_complexity(complexity_level: str, settings: Settings = Depends(get_settings)):
    # Filter concepts by complexity level
    # Return paginated ConceptListResponse
```

### Pattern 4: Tooltip Implementation (FR4)
```javascript
// Follow existing main.js event handling pattern
setupTooltipEvents() {
    this.graphManager.cy.on('mouseover', 'node', (event) => {
        this.showConceptTooltip(event.target);
    });
}
```

## Acceptance Criteria

### AC1: Enhanced Automated Extraction
- [ ] Complexity levels extracted with >80% accuracy on test document set
- [ ] Prerequisites identified and mapped to existing ontology concepts  
- [ ] Domain classification works for mathematics, finance, economics domains
- [ ] Extraction process completes within existing document processing timeframes

### AC2: Expanded Symbol Detection  
- [ ] Symbol dictionary expanded from 50+ to 150+ LaTeX mappings
- [ ] Multi-line equation environments properly detected and converted
- [ ] Financial notation (options pricing, portfolio theory) correctly identified
- [ ] Backward compatibility maintained for existing symbol detection

### AC3: Advanced Search and Filtering
- [ ] New search endpoints return accurate filtered results
- [ ] Pagination works correctly for filtered result sets
- [ ] Search suggestions include enhanced metadata fields
- [ ] API response times remain under 500ms for filtered queries

### AC4: Interactive Graph Tooltips
- [ ] Tooltips display within 300ms of hover event
- [ ] LaTeX expressions render correctly in tooltip context
- [ ] Tooltip positioning avoids viewport overflow  
- [ ] Graph performance maintains >30fps with tooltips enabled

## Test Plan

### Unit Tests
**Files to create/modify:**
- `tests/test_enhanced_concept_extractor.py` - Test metadata extraction
- `tests/test_expanded_math_detector.py` - Test symbol detection expansion  
- `tests/test_search_filtering.py` - Test new search endpoints
- `tests/test_tooltip_functionality.py` - Test frontend tooltip behavior

### Integration Tests  
- **Document Processing Pipeline:** Test end-to-end extraction with enhanced metadata
- **API Integration:** Test new search endpoints with existing frontend
- **Graph Visualization:** Test tooltip integration with Cytoscape.js
- **MathJax Integration:** Test LaTeX rendering in tooltip context

### Performance Tests
- **Graph Rendering:** 1000+ node graphs with tooltips enabled
- **Search Response Time:** Filtered queries under load
- **Memory Usage:** Tooltip caching and cleanup
- **Math Rendering:** Concurrent LaTeX processing performance

## Documentation Updates

### Files to Update:
- `docs/external-knowledge-integration.md` - Document enhanced extraction capabilities
- `README.md` - Update feature list with new search and tooltip capabilities  
- `docs/COMPLETE_WORKFLOW_GUIDE.md` - Include new search filtering workflows
- API documentation for new search endpoints

### New Documentation:
- `docs/enhanced-metadata-extraction.md` - Guide for complexity/prerequisite extraction
- `docs/mathematical-notation-support.md` - Comprehensive symbol support documentation
- `docs/interactive-graph-features.md` - Tooltip and interaction guide

## Assumptions

### Enhancement Assumptions (Based on User Answers):
1. **Automated Processing Priority** - Enhanced extraction should be automatic during document ingestion
2. **Mathematical Complexity** - Users work with advanced financial mathematics requiring extensive notation  
3. **Research Context** - External links and academic sources are important for user workflows
4. **Performance Expectations** - Interactive features should not degrade graph visualization performance

### Technical Assumptions:
1. **Existing Infrastructure** - Neo4j, FastAPI, MathJax stack remains unchanged
2. **Document Quality** - PDF documents contain extractable text and mathematical notation
3. **Browser Support** - Modern browsers with ES6+ and MathJax 3.x support
4. **Data Volume** - System should handle 10,000+ concepts with enhanced metadata

## Git & Github Commit Instructions

### Branch Strategy:
```bash
git checkout -b feature/enhanced-graph-metadata
```

### Commit Message Format:
```
feat(component): brief description

- Detailed change description
- Reference to requirement ID (FR1, FR2, etc.)
- Breaking changes noted if any

Co-authored-by: [collaborator if applicable]
```

### Example Commits:
```bash
git commit -m "feat(extraction): implement complexity level detection (FR1.1)

- Add complexity analysis based on mathematical notation depth
- Identify educational indicators in document context  
- Default to intermediate for financial mathematics concepts"

git commit -m "feat(search): add complexity and domain filtering (FR3.1, FR3.2)

- Implement /api/search/by-complexity/{level} endpoint
- Add /api/search/by-domain/{domain} endpoint
- Maintain backward compatibility with existing search API"

git commit -m "feat(frontend): implement interactive graph tooltips (FR4)

- Add hover tooltips with enhanced metadata display
- Include LaTeX preview for mathematical concepts
- Optimize performance for large graph rendering"
```

### Pull Request Requirements:
- [ ] All acceptance criteria met and tested
- [ ] Unit tests written with >90% coverage for new code
- [ ] Integration tests verify end-to-end functionality  
- [ ] Performance benchmarks show no regression
- [ ] Documentation updated for new features
- [ ] API changes documented with examples

### Deployment Notes:
- Enhanced extraction requires reprocessing existing documents for full metadata
- New search endpoints can be deployed without downtime
- Tooltip feature is backward compatible and can be gradually rolled out
- Consider feature flags for enhanced extraction during initial deployment