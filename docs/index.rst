AI Knowledge Graph Documentation
=====================================

Welcome to the AI Knowledge Graph system documentation. This system provides comprehensive document processing, mathematical content extraction, and knowledge graph construction capabilities.

.. toctree::
   :maxdepth: 2
   :caption: User Guide:

   installation
   quickstart
   configuration
   workflows
   api_reference

.. toctree::
   :maxdepth: 2
   :caption: Developer Guide:

   architecture
   modules
   testing
   deployment
   contributing

.. toctree::
   :maxdepth: 2
   :caption: API Documentation:

   modules/ingestion
   modules/extractors
   modules/knowledge
   modules/frontend
   modules/optimization

Overview
--------

The AI Knowledge Graph system is designed to process academic and technical documents, extract mathematical content, and build interconnected knowledge graphs. Key features include:

* **Multi-format Document Processing**: Support for PDF, HTML, DOCX, XML, and LaTeX documents
* **Mathematical Content Extraction**: Advanced detection and extraction of mathematical formulas and expressions
* **Knowledge Graph Construction**: Automatic concept extraction and relationship mapping
* **Web Interface**: Interactive visualization and exploration of knowledge graphs
* **Plugin Architecture**: Extensible extractor system with entry point discovery
* **CI/CD Integration**: Comprehensive testing and deployment automation

Quick Start
-----------

1. **Installation**::

    git clone https://github.com/supersonic-electronic/AI.git
    cd AI
    poetry install

2. **Configuration**::

    cp config.yaml.example config.yaml
    # Edit config.yaml with your settings

3. **Run Document Processing**::

    poetry run python -m src.cli ingest --input-dir ./data/papers

4. **Start Web Interface**::

    poetry run python -m src.cli serve

5. **Open Browser**: Navigate to http://localhost:8000

Architecture
------------

The system is built with a modular architecture:

.. code-block:: text

    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
    │   Document      │    │   Knowledge     │    │   Web           │
    │   Ingestion     │───▶│   Graph         │───▶│   Interface     │
    │                 │    │   Engine        │    │                 │
    └─────────────────┘    └─────────────────┘    └─────────────────┘
    │                 │    │                 │    │                 │
    │ • PDF Extract   │    │ • Concept Map   │    │ • Visualization │
    │ • Math Detect   │    │ • Relationships │    │ • Search        │
    │ • Plugin System │    │ • Graph DB      │    │ • REST API      │
    │ • Async Process │    │ • Vector Store  │    │ • Interactive   │
    └─────────────────┘    └─────────────────┘    └─────────────────┘

Key Features
------------

Document Processing
~~~~~~~~~~~~~~~~~~~

* **Multiple Format Support**: Process PDF, HTML, DOCX, XML, and LaTeX documents
* **Mathematical Content**: Advanced detection and extraction of formulas
* **Batch Processing**: Efficient processing of large document collections
* **Error Handling**: Robust error recovery and logging

Knowledge Graph
~~~~~~~~~~~~~~~

* **Concept Extraction**: Automatic identification of key concepts
* **Relationship Mapping**: Discovery of connections between concepts
* **Graph Database**: Persistent storage with Neo4j or in-memory options
* **Vector Embeddings**: Semantic similarity search with multiple backends

Web Interface
~~~~~~~~~~~~~

* **Interactive Visualization**: Explore knowledge graphs with Cytoscape.js
* **Search Functionality**: Find concepts and relationships
* **Real-time Updates**: Live updates as documents are processed
* **RESTful API**: Programmatic access to all functionality

Contributing
------------

We welcome contributions! Please see our :doc:`contributing` guide for details on:

* Setting up the development environment
* Running tests
* Submitting pull requests
* Coding standards

License
-------

This project is licensed under the MIT License. See the LICENSE file for details.

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`