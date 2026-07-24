"""Sphinx configuration for the GrabMore eCommerce documentation."""

import os
import sys

import django

sys.path.insert(0, os.path.abspath(".."))
os.environ["DJANGO_SETTINGS_MODULE"] = "ecommerce_project.settings"
django.setup()

project = "GrabMore eCommerce"
copyright = "2026, Nomfundo Shabangu"
author = "Nomfundo Shabangu"
release = "1.0"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]