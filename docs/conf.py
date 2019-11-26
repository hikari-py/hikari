#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © Nekoka.tt 2019
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
import contextlib
import datetime
import os
import shutil
import sys
import textwrap

import sphinx_bootstrap_theme

sys.path.insert(0, os.path.abspath(".."))

# -- Project information -----------------------------------------------------

project = "Hikari"
author = "Nekokatt"
copyright = author
version = "0.0.54"

is_staging = "dev" in version

# -- General configuration ---------------------------------------------------

extensions = [
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinx_autodoc_typehints",
    "sphinx.ext.intersphinx",
    "sphinx.ext.inheritance_diagram",
    "sphinx.ext.graphviz",
]

if shutil.which("dot"):
    print("GRAPHVIZ INSTALLED, WILL GENERATE PRETTY DIAGRAMS :)")

    extensions += ("sphinx.ext.inheritance_diagram", "sphinx.ext.graphviz")
else:
    print("dot WAS NOT INSTALLED, PLEASE INSTALL GRAPHVIZ PROPERLY FOR dot DIAGRAMS TO RENDER")

# Apply our code that fixes weird issues in graphviz
with open(os.path.join(os.path.dirname(__name__), "graphviz_hacks.py")) as fp:
    exec(fp.read(), globals(), locals())  # nosec

templates_path = ["_templates"]
exclude_patterns = []

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
        ("Hikari", "http://gitlab.com/nekokatt/hikari", True),
        ("Wiki", "http://gitlab.com/nekokatt/hikari/wikis", True),
        ("CI", "http://gitlab.com/nekokatt/hikari/pipelines", True),
    ],
    # Render the next and previous page links in navbar. (Default: true)
    "navbar_sidebarrel": True,
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
    "globaltoc_includehidden": "true",
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
    "inherited_members": True,
    "members": True,
}

# -- Intersphinx options -----------------------------------------------------
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "aiohttp": ("https://aiohttp.readthedocs.io/en/stable/", None),
    "websockets": ("https://websockets.readthedocs.io/en/stable/", None),
}

# -- Inheritance diagram options ---------------------------------------------


# https://www.graphviz.org/doc/info/attrs.html
# https://www.graphviz.org/doc/info/arrows.html
inheritance_graph_attrs = dict(
    layout="twopi",  # dot neato twopi circo fdp
    rankdir="TD",
    fontsize=10,
    ratio="compress",
    # splines="ortho",
    pad=0.5,
    nodesep=4,
    ranksep=4,
    # Use a stupidly large size we will never reach, then let the compress ratio fix itself.
    size='"100000.0 100000.0"',
    splines="straight",
)

inheritance_node_attrs = dict(
    fontsize=10, fontname='"monospace"', color='"#772953"', style='"filled,rounded"', fontcolor="white"
)

inheritance_edge_attrs = dict(color='"#772953"', arrowhead="onormal", arrowsize=1)

graphviz_output_format = "svg"

# -- Epilog to inject into each page... ---------------------------------------------


rst_epilog = """
.. |rawEvent| replace:: This is is a raw event. This means that it is fired with the raw data sent by Discord's gateway
                        without any form of pre-processing or validation. Corresponding information may be incorrect, 
                        sent multiple times, or refer to information that is not cached. The implementation specifics
                        of this are documented on the developer portal for Discord at 
                        https://discordapp.com/developers/docs/topics/gateway#commands-and-events

.. |selfHealing| replace:: You do not have to do anything in this situation. The gateway client in Hikari will attempt 
                           to resolve these issues for you.
"""

if not is_staging:
    rst_epilog += textwrap.dedent(
        """
        .. |staging_link| replace:: If you want the latest staging documentation instead, please visit 
                                    `this page <staging/index.html>`__.
    """
    )
else:
    rst_epilog += textwrap.dedent(
        """
        .. |staging_link| replace:: This is the documentation for the development release
    """
    )


def setup(app):
    app.add_stylesheet("style.css")
    print(dir(app), type(app))

    # Little easteregg.
    with contextlib.suppress(Exception):
        if datetime.datetime.now().month in (12, 1, 2):
            app.add_javascript("http://www.schillmania.com/projects/snowstorm/snowstorm.js")
