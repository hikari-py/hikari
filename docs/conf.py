# -*- coding: utf-8 -*-
# Copyright (c) 2020 Nekokatt
# Copyright (c) 2021-present davfsa
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""Configuration file for the Sphinx documentation builder."""
import os
import pathlib
import re
import types

# -- Project information -----------------------------------------------------

with open(os.path.join("..", "hikari", "_about.py")) as fp:
    code = fp.read()

token_pattern = re.compile(r"^__(?P<key>\w+)?__.*=\s*(?P<quote>(?:'{3}|\"{3}|'|\"))(?P<value>.*?)(?P=quote)", re.M)

groups = {}

for match in token_pattern.finditer(code):
    group = match.groupdict()
    groups[group["key"]] = group["value"]

metadata = types.SimpleNamespace(**groups)

project = "hikari"
copyright = metadata.copyright
author = metadata.author
release = version = metadata.version

PROJECT_ROOT_DIR = pathlib.Path(__file__).parents[1].resolve()


# -- General configuration ---------------------------------------------------

extensions = [
    # Sphinx own extensions
    "sphinx.ext.autosummary",
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
    "sphinx.ext.mathjax",
    # Our extensions
    "myst_parser",
    "sphinxext.opengraph",
    "sphinx_copybutton",
    "sphinxcontrib.towncrier.ext",
]

if os.getenv("SKIP_REFERENCE_DOCS") is None:
    extensions.extend(
        (
            "autoapi.extension",
            "numpydoc",
        )
    )


templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

default_role = "py:obj"

# -- HTML output --------------------------------------------------------------

html_theme = "furo"
html_favicon = "https://www.hikari-py.dev/logo.png"
html_static_path = ["_static"]
html_css_files = ["extra.css"]

# -- OpenGraph ----------------------------------------------------------------

ogp_site_url = "https://docs.hikari-py.dev"
ogp_image = "https://www.hikari-py.dev/logo.png"

ogp_custom_meta_tags = [
    '<meta property="theme-color" content="#ff029a">',
]

# -- AutoAPI options ----------------------------------------------------------

autoapi_root = "reference"
autoapi_dirs = ["../hikari"]
autoapi_ignore = ["__main__.py"]

autoapi_options = ["members", "show-inheritance"]
autoapi_template_dir = "_templates"

autoapi_add_toctree_entry = False
autoapi_keep_files = True
autoapi_member_order = "groupwise"

# -- AutoDoc options ----------------------------------------------------------

autodoc_typehints = "none"  # NumpyDoc will do it for us. We just want to remove them from the signature too
autodoc_preserve_defaults = True

# -- NumpyDoc options ---------------------------------------------------------

numpydoc_class_members_toctree = True
numpydoc_show_class_members = False
numpydoc_xref_param_type = True
numpydoc_validation_checks = {
    "all",
    # Under here are all disabled checks
    "GL08",  # Missing docstring
    "GL06",  # Unknown section
}

# -- Intersphinx options ------------------------------------------------------

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "aiohttp": ("https://docs.aiohttp.org/en/stable", None),
    "attrs": ("https://www.attrs.org/en/stable/", None),
    "multidict": ("https://multidict.aio-libs.org/en/stable/", None),
    "yarl": ("https://yarl.aio-libs.org/en/stable/", None),
}

# -- MyST ---------------------------------------------------------------------

myst_heading_anchors = 3

# -- Towncrier ----------------------------------------------------------------

towncrier_draft_autoversion_mode = "draft"
towncrier_draft_include_empty = True
towncrier_draft_working_directory = PROJECT_ROOT_DIR
