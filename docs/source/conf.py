import os
import sys

sys.path.insert(0, os.path.abspath('../../opa'))
on_rtd = os.environ.get('READTHEDOCS') == 'True'

autoclass_content = 'both'

project = 'opa-python'
copyright = '2022, Gustaf Sjoberg'
author = 'Gustaf Sjoberg'

extensions = [
    'sphinx.ext.autodoc',
]

templates_path = ['_templates']
exclude_patterns = []

html_static_path = ['_static']

if on_rtd:
    html_theme = "sphinx_rtd_theme"
