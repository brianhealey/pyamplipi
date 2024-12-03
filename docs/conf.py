# docs/conf.py
import os
import sys
sys.path.insert(0, os.path.abspath('..'))  # Add parent directory to Python path

project = 'pyamplipi'
copyright = '2024'
author = 'brianhealey, linknum23, mjustian'

extensions = [
    'sphinx.ext.autodoc',      # Core extension for API documentation
    'sphinx.ext.napoleon',     # Support for Google and NumPy style docstrings
    'sphinx.ext.viewcode',     # Add links to highlighted source code
    'sphinx.ext.intersphinx',  # Link to other project's documentation
    'sphinx.ext.autosummary',  # Generate summary tables
    'myst_parser',             # Support Markdown files
]

# Theme configuration
html_theme = 'sphinx_rtd_theme'

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# If true, `todo` and `todoList` produce output
todo_include_todos = True

# Autodoc configuration
autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': True,
    'exclude-members': '__weakref__'
}

# Napoleon settings
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = True
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_type_aliases = None
