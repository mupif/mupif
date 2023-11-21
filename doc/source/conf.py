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
    'sphinx.ext.todo',
    'sphinxcontrib.mermaid',
    'sphinx_rtd_theme'
]

import sys, os.path

autodoc_pydantic_model_show_json_error_strategy='coerce'

thisDir=os.path.dirname(os.path.abspath(__file__))

#apidoc_module_dir=thisDir+'/../../mupif'
#apidoc_output_dir='api/'
#apidoc_toc_file='api'
#apidoc_excluded_paths=[]
#apidoc_module_first=True

todo_include_todos=True

autodoc_pydantic_model_show_json = True
autodoc_pydantic_settings_show_json = True


sys.path.append(thisDir+'/../..')
import mupif
import mupif.tests
import importlib


# HACK: pretend everything is in mupif.* directly
# so that cross-references in autodoc work
for a in mupif.__all__:
    try:
        # if it is a module, do nothing
        importlib.import_module('mupif.'+a)
    except ImportError:
        # otherwise put it into the mupif module directly
        o=getattr(mupif,a)
        #o.__module__='mupif'


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

html_theme='sphinx_rtd_theme'

#html_theme_options=dict(
#    github_banner=True,
#    github_user='mupif',
#    github_repo='mupif',
#    display_github=True
#)
html_context=dict(
    github_banner=True,
    github_user='mupif',
    github_repo='mupif',
    display_github=True,
    github_version='dev',
    conf_py_path='mupif/doc/source'
)

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

html_css_files=[
    'custom.css',
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css'
]


##### generate data schemas so that readthedocs.io serves them at a known URL
import mupif as mp
import os
import json
os.makedirs('_static/schema',exist_ok=True)
open('_static/schema/ModelMeta.json','w').write(mp.meta.ModelMeta.schema_json())
open('_static/schema/WorkflowMeta.json','w').write(mp.meta.WorkflowMeta.schema_json())
open('_static/schema/HeavyStruct.json','w').write(json.dumps(mp.heavystruct.HeavyStructSchemaModel))
