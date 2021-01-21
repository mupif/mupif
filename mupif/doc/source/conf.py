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


# -- Project information -----------------------------------------------------

project = 'MuPIF'
copyright = '2021, Bořek Patzák, Vít Šmilauer'
author = 'Bořek Patzák, Vít Šmilauer'
# (Czech Technical University, Faculty of Civil Engineering, Department of Mechanics, Thákurova 7, 16629, Prague, Czech Republic.)'

# The full version, including alpha/beta/rc tags
release = '3.x'


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autodoc',
    'sphinxcontrib.apidoc'
]

apidoc_module_dir='../../../mupif'
apidoc_output_dir='api/'
apidoc_toc_file='api'
apidoc_excluded_paths=['tools']
apidoc_module_first=True

import sys
sys.path.append('../../..')
import mupif


# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []

numfig=True

latex_engine = 'lualatex'
latex_logo='img/mupif-logo.png'
latex_documents=[('index','mupif.tex','MuPIF Documentation',
    r'Bořek Patzák\\Vít Šmilauer\\Stanislav Šulc\\Martin Horák\\ \hbox{} \\ \parbox{.5\linewidth}{\normalsize Czech Technical University \\ Faculty of Civil Engineering \\ Department of Mechanics \\ Thákurova 7 \\ 16629 Prague \\ Czech Republic}','manual')]


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'alabaster'
html_theme_options=dict(
    github_banner=True,
    github_user='mupif',
    github_repo='mupif'
)

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']