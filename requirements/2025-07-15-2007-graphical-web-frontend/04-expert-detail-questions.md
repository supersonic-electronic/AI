# Expert Detail Questions - Phase 4

Based on deep codebase analysis, these technical implementation questions will finalize the requirements:

## Q1: Should the FastAPI backend extend the existing CLI pattern in `src/cli.py` with a new `serve` command that launches the web server?
**Technical Context:** Current CLI has commands like `process-pdfs`, `extract-concepts`. Adding `serve` would maintain consistency.
**Options:** Yes (extend CLI) / No (separate entry point)

## Q2: Should the web API reuse the existing `FinancialMathOntology.export_ontology()` method from `src/knowledge/ontology.py:424` for data formatting?
**Technical Context:** The method returns concept/relationship dictionaries that need conversion to Cytoscape.js format.
**Options:** Yes (reuse and transform) / No (direct JSON access)

## Q3: Should the backend implement caching for the knowledge graph data since it's read-only and stored in JSON files?
**Technical Context:** Current data is in `data/knowledge_graph.json` (20 concepts, 262 relationships). FastAPI supports response caching.
**Options:** Yes (implement caching) / No (direct file reads)

## Q4: Should the frontend use the existing concept type color scheme from `src/knowledge/graph_viz.py:47-61` for visual consistency?
**Technical Context:** Existing colors: Portfolio (#FFB74D), Risk (#F06292), Return (#81C784), etc. Well-designed color palette.
**Options:** Yes (reuse colors) / No (new color scheme)

## Q5: Should the web server configuration (port, host, debug mode) use the existing `src/settings.py` Pydantic settings pattern?
**Technical Context:** Current settings handle database paths, API keys, etc. with environment variable support.
**Options:** Yes (extend Settings class) / No (separate config)