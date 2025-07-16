# Detail Questions

## Q6: Should we enhance the existing automated concept extraction in `src/knowledge/concept_extractor.py` to extract more metadata fields (like complexity levels, prerequisites) from document context?
**Default if unknown:** No (the current implementation focuses on mathematical content detection and basic concept identification, with enhanced metadata likely added manually or through separate enrichment processes)

## Q7: Do you want to expand the mathematical symbol detection in `src/ingestion/math_detector.py` to support additional notation systems beyond the current 50+ LaTeX mappings?
**Default if unknown:** No (the existing symbol detection covers standard financial mathematics notation and can be extended incrementally as needed)

## Q8: Should we add new API endpoints to `src/frontend/api/` for managing enhanced metadata separately from the core concept CRUD operations?
**Default if unknown:** No (the existing `/api/concepts` endpoints already return all enhanced metadata, and the system is designed as read-only for concept details)

## Q9: Do you need enhanced search capabilities in `src/frontend/api/search.py` to filter concepts by complexity level, domain, or prerequisite relationships?
**Default if unknown:** Yes (the discovery answers indicated users need to search/filter by enhanced metadata, and the existing search API would benefit from these filters)

## Q10: Should the concept visualization in the web app display enhanced metadata directly on the graph nodes (tooltips, badges) rather than only in the details panel?
**Default if unknown:** No (graph readability is typically better with minimal node decoration, keeping detailed metadata in the expandable details panel as currently implemented)