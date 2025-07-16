# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import os
import sys
sys.path.insert(0, os.path.abspath('../src'))

project = 'AI Knowledge Graph'
copyright = '2025, supersonic-electronic'
author = 'supersonic-electronic'
version = '0.1.0'
release = '0.1.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
    'sphinx.ext.intersphinx',
    'sphinx.ext.todo',
    'sphinx.ext.coverage',
    'sphinx.ext.imgmath',
    'sphinx.ext.githubpages',
    'myst_parser',
]

# Napoleon settings for Google/NumPy style docstrings
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_preprocess_types = False
napoleon_type_aliases = None
napoleon_attr_annotations = True

# MyST configuration for markdown support
myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "html_admonition",
    "html_image",
    "linkify",
    "replacements",
    "smartquotes",
    "substitution",
    "tasklist",
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# Source file parsers
source_suffix = {
    '.rst': None,
    '.md': 'myst_parser',
}

# Master document
master_doc = 'index'

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_theme_options = {
    'canonical_url': '',
    'analytics_id': '',
    'logo_only': False,
    'display_version': True,
    'prev_next_buttons_location': 'bottom',
    'style_external_links': False,
    'vcs_pageview_mode': '',
    'style_nav_header_background': '#2980B9',
    'collapse_navigation': False,
    'sticky_navigation': True,
    'navigation_depth': 4,
    'includehidden': True,
    'titles_only': False
}

html_static_path = ['_static']
html_favicon = None

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
# html_static_path = ['_static']

# -- Options for autodoc -----------------------------------------------------
autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': True,
    'exclude-members': '__weakref__'
}

# Mock imports for modules that might not be available during doc build
autodoc_mock_imports = [
    'fitz',
    'pymupdf',
    'pinecone',
    'chromadb',
    'openai',
    'mpxpy',
    'langchain',
    'langchain_text_splitters',
    'sentence_transformers',
    'transformers',
    'torch',
    'tensorflow',
    'sklearn',
    'scikit-learn',
    'numpy',
    'pandas',
    'matplotlib',
    'seaborn',
    'plotly',
    'fastapi',
    'uvicorn',
    'jinja2',
    'python_docx',
    'beautifulsoup4',
    'lxml',
    'watchdog',
    'aiofiles',
    'click'
]

# -- Options for intersphinx -------------------------------------------------
intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
    'numpy': ('https://numpy.org/doc/stable/', None),
    'pandas': ('https://pandas.pydata.org/docs/', None),
    'fastapi': ('https://fastapi.tiangolo.com/', None),
    'pydantic': ('https://docs.pydantic.dev/', None),
}

# -- Options for todo extension ----------------------------------------------
todo_include_todos = True

# -- Options for coverage extension ------------------------------------------
coverage_show_missing_items = True

# Additional configuration
html_show_sourcelink = True
html_show_sphinx = True
html_show_copyright = True

# Add version info to sidebar
html_context = {
    'display_github': True,
    'github_user': 'supersonic-electronic',
    'github_repo': 'AI',
    'github_version': 'main/docs/',
}

# LaTeX output configuration
latex_engine = 'pdflatex'
latex_elements = {
    'papersize': 'letterpaper',
    'pointsize': '10pt',
    'preamble': '',
    'fncychap': '\\usepackage[Bjornstrup]{fncychap}',
    'printindex': '\\footnotesize\\raggedright\\printindex',
}

latex_documents = [
    (master_doc, 'ai-knowledge-graph.tex', 'AI Knowledge Graph Documentation',
     'supersonic-electronic', 'manual'),
]