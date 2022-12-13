import os
import sys

sys.path.insert(0, os.path.abspath('../../opa'))

autoclass_content = 'both'

project = 'opa-python'
copyright = '2022, Gustaf Sjoberg'
author = 'Gustaf Sjoberg'

extensions = [
    'sphinx.ext.autodoc',
]

templates_path = ['_templates']
exclude_patterns = []

html_theme = "sphinx_rtd_theme"
html_static_path = ['_static']
