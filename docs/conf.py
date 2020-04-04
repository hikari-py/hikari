#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © Nekoka.tt 2019-2020
#
# This file is part of Hikari.
#
# Hikari is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Hikari is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Hikari. If not, see <https://www.gnu.org/licenses/>.
"""
Sphinx documentation configuration.
"""
# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# http://www.sphinx-doc.org/en/master/config
import os
import re
import shutil
import sys
import textwrap
import types

import sphinx_bootstrap_theme


sys.path.insert(0, os.path.abspath(".."))


name = "hikari"


with open(os.path.join("..", name, "_about.py")) as fp:
    code = fp.read()

token_pattern = re.compile(r"^__(?P<key>\w+)?__\s*=\s*(?P<quote>(?:'{3}|\"{3}|'|\"))(?P<value>.*?)(?P=quote)", re.M)

groups = {}

for match in token_pattern.finditer(code):
    group = match.groupdict()
    groups[group["key"]] = group["value"]
    del match, group

meta = types.SimpleNamespace(**groups)

del groups, token_pattern, code, fp


# -- Project information -----------------------------------------------------

project = name.title()
author = meta.author
copyright = meta.copyright
version = meta.version

is_staging = "dev" in version

# -- General configuration ---------------------------------------------------

extensions = [
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx.ext.mathjax",
]

if shutil.which("dot"):
    print("Inheritance diagram enabled")
    extensions += ["sphinx.ext.graphviz", "sphinx.ext.inheritance_diagram"]

templates_path = ["_templates"]
exclude_patterns = []

# -- Pygments style ----------------------------------------------------------
pygments_style = "fruity"


# -- Options for HTML output -------------------------------------------------
html_theme = "bootstrap"
html_theme_path = sphinx_bootstrap_theme.get_html_theme_path()
html_static_path = ["_static"]

# Theme options are theme-specific and customize the look and feel of a
# theme further.
html_theme_options = {
    # Navigation bar title. (Default: ``project`` value)
    # 'navbar_title': "",
    # Tab name for entire site. (Default: "Site")
    "navbar_site_name": "Modules",
    # A list of tuples containing pages or urls to link to.
    # Valid tuples should be in the following forms:
    #    (name, page)                 # a link to a page
    #    (name, "/aa/bb", 1)          # a link to an arbitrary relative url
    #    (name, "http://example.com", True) # arbitrary absolute url
    # Note the "1" or "True" value above as the third argument to indicate
    # an arbitrary url.
    "navbar_links": [
        ("Source", "http://gitlab.com/nekokatt/hikari", True),
        ("Builds", "http://gitlab.com/nekokatt/hikari/pipelines", True),
    ],
    # Render the next and previous page links in navbar. (Default: true)
    "navbar_sidebarrel": False,
    # Render the current pages TOC in the navbar. (Default: true)
    "navbar_pagenav": False,
    # Tab name for the current pages TOC. (Default: "Page")
    "navbar_pagenav_name": "This page",
    # Global TOC depth for "site" navbar tab. (Default: 1)
    # Switching to -1 shows all levels.
    "globaltoc_depth": 6,
    # Include hidden TOCs in Site navbar?
    #
    # Note: If this is "false", you cannot have mixed ``:hidden:`` and
    # non-hidden ``toctree`` directives in the same page, or else the build
    # will break.
    #
    # Values: "true" (default) or "false"
    "globaltoc_includehidden": "false",
    # HTML navbar class (Default: "navbar") to attach to <div> element.
    # For black navbar, do "navbar navbar-inverse"
    "navbar_class": "navbar navbar-inverse",
    # Fix navigation bar to top of page?
    # Values: "true" (default) or "false"
    "navbar_fixed_top": "false",
    # Location of link to source.
    # Options are "nav" (default), "footer" or anything else to exclude.
    "source_link_position": "footer",
    # Bootswatch (http://bootswatch.com/) theme.
    #
    # Options are nothing (default) or the name of a valid theme
    # such as "cosmo" or "sandstone".
    #
    # The set of valid themes depend on the version of Bootstrap
    # that's used (the next config option).
    #
    # Currently, the supported themes are:
    # - Bootstrap 2: https://bootswatch.com/2
    # - Bootstrap 3: https://bootswatch.com/3
    "bootswatch_theme": None,
    # Choose Bootstrap version.
    # Values: "3" (default) or "2" (in quotes)
    "bootstrap_version": "3",
}

# -- Autodoc options ---------------------------------------------------------
autoclass_content = "both"

autodoc_default_options = {
    # "member-order": "bysource",
    # "member-order": "alphabetical",
    "member-order": "groupwise",
    "undoc-members": False,
    "exclude-members": "__weakref__",
    "show_inheritance": True,
    "imported_members": False,
    "ignore-module-all": True,
    "inherited_members": True,
    "members": True,
}

autodoc_typehints = "none"
autodoc_mock_imports = ["aiohttp"]

# -- Intersphinx options -----------------------------------------------------
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "aiohttp": ("https://aiohttp.readthedocs.io/en/stable/", None),
    "attrs": ("https://www.attrs.org/en/stable/", None),
    "click": ("https://click.palletsprojects.com/en/7.x/", None),
}

# -- Inheritance diagram options... -------------------------------------------------

inheritance_graph_attrs = dict(
    bgcolor="transparent", rankdir="TD", ratio="auto", fontsize=10, splines="line", size='"20 50"',
)

inheritance_node_attrs = dict(
    fontsize=10, fontname='"monospace"', color='"#505050"', style='"filled,rounded"', fontcolor='"#FFFFFF"'
)
inheritance_edge_attrs = dict(
    color='"#505050"',
    arrowtail="oempty",
    arrowhead="none",
    arrowsize=1,
    dir="both",
    fontcolor='"#FFFFFF"',
    style='"filled"',
)
graphviz_output_format = "svg"

# -- Epilog to inject into each page... ---------------------------------------------


rst_epilog = """
.. |internal| replace::  
        These components are part of the hikari.internal module. 
        This means that anything located here is designed **only to be used internally by Hikari**, 
        and **you should not use it directly in your applications**. Changes to these files will occur 
        **without** warning or a deprecation period. It is only documented to ensure a complete reference 
        for application developers wishing to either contribute to or extend this library. 
"""

if not is_staging:
    rst_epilog += textwrap.dedent(
        """.. |staging_link| replace:: If you want the latest staging documentation instead, please visit 
            `this page <staging/index.html>`__.
        
        """
    )
else:
    rst_epilog += textwrap.dedent(
        """.. |staging_link| replace:: This is the documentation for the development release.
        
        """
    )


def setup(app):
    app.add_stylesheet("style.css")
