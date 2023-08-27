# Configuration file for the Sphinx documentation builder.

import os
import sys

# -- Project information

project = 'LexFlow'
copyright = '2023, Fuad'
author = 'Fuad'

release = '0.1'
version = '0.1.0'

# -- General configuration

extensions = [
    'sphinx.ext.duration',
    'sphinx.ext.doctest',
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.autosummary',
    'sphinx.ext.intersphinx',
]

intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
    'sphinx': ('https://www.sphinx-doc.org/en/master/', None),
}
intersphinx_disabled_domains = ['std']

templates_path = ['_templates']

# Add the project directory to the system path
sys.path.insert(0, os.path.abspath('../../src'))


# -- Options for HTML output

html_theme = 'furo'
# html_theme = 'sphinx_rtd_theme'

# -- Options for EPUB output
epub_show_urls = 'footnote'

# -- Run sphinx-apidoc automatically
# autodoc_mock_imports = ["pydantic"]


def run_apidoc(_):
    from sphinx.ext.apidoc import main
    cur_dir = os.path.abspath(os.path.dirname(__file__))
    module_path = os.path.join(cur_dir, "..", "..", "src")  # pointing to the 'src' directory
    main(['-e', '-f', '-o', os.path.join(cur_dir, 'generated'), module_path])  # output to the 'generated' directory

def setup(app):
    app.connect('builder-inited', run_apidoc)