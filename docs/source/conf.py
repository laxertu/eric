# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
# import os
# import sys
# sys.path.insert(0, os.path.abspath('.'))

import sys
from pathlib import Path
__eric_root_dir = Path(__file__).parent.parent.parent
__eric_modules_path = f'{__eric_root_dir.absolute()}'
sys.path.append(__eric_modules_path)


# -- Project information -----------------------------------------------------
project = 'eric-sse'
author = 'Luca Stretti'

# The full version, including alpha/beta/rc tags
# release = '1.0.0'


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.duration',
    'sphinx.ext.doctest',
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx_markdown_builder'
]

markdown_anchor_sections = True
markdown_anchor_signatures = True

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#

"""
html_theme = 'agogo'
html_theme_options = {
    "sidebarwidth": "20%"
}
"""

html_theme = 'sphinx_book_theme'
html_theme_options = {
    "repository_url": "https://github.com/laxertu/eric",
    "use_repository_button": True,
    "use_issues_button": True,
    "use_download_button": False,
}



# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
# html_static_path = ['_static']

# Luca
add_module_names = False
# python_display_short_literal_types = True
modindex_common_prefix = ['eric_sse.']
toc_object_entries_show_parents = 'hide'

# -- Options for autodoc ----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html#configuration

# Automatically extract typehints when specified and place them in
# descriptions of the relevant function/method.
autodoc_typehints = "description"

# Don't show class signature with the class' name.
autodoc_class_signature = "separated"